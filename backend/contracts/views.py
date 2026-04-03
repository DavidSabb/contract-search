import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .api_clients import (
    search_open_canada,
    search_procuredata,
    search_sam_gov,
    search_usa_spending,
)
from .normalizers import (
    normalize_open_canada,
    normalize_procuredata,
    normalize_sam_gov,
    normalize_usa_spending,
)
from .query_expander import expand_query
from .relevance import deduplicate_results, score_result

logger = logging.getLogger(__name__)

PAGE_SIZE = 20


class ContractSearchView(APIView):
    def post(self, request):
        query = (request.data.get("query") or "").strip()
        page = request.data.get("page", 1)
        show_closed = request.data.get("show_closed", False)

        if len(query) < 2:
            return Response(
                {"error": "Query must be at least 2 characters."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            page = max(1, int(page))
        except (ValueError, TypeError):
            page = 1

        # Step 1: Expand query into procurement terms
        expanded = expand_query(query)
        logger.info(
            "Query '%s' expanded: primary='%s', synonyms=%s",
            query, expanded["primary"], expanded["synonyms"],
        )

        # Step 2: Fetch from all 4 APIs in parallel (each fetches ~50 raw results)
        tasks = {
            "procuredata": (search_procuredata, normalize_procuredata),
            "open_canada": (search_open_canada, normalize_open_canada),
            "sam_gov": (search_sam_gov, normalize_sam_gov),
            "usa_spending": (search_usa_spending, normalize_usa_spending),
        }

        all_normalized = []
        raw_source_counts = {}

        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = {
                executor.submit(fetch_fn, expanded, page): (name, normalize_fn)
                for name, (fetch_fn, normalize_fn) in tasks.items()
            }

            for future in as_completed(futures):
                name, normalize_fn = futures[future]
                try:
                    raw = future.result()
                    normalized = normalize_fn(raw)
                    raw_source_counts[name] = len(normalized)
                    all_normalized.extend(normalized)
                except Exception as e:
                    logger.warning("Source %s failed: %s", name, e)
                    raw_source_counts[name] = 0

        logger.info(
            "Raw results fetched for '%s': %s (total %d)",
            query, raw_source_counts, len(all_normalized),
        )

        # Step 3: Score every result for relevance
        scored = []
        for result in all_normalized:
            relevance, matched_terms = score_result(
                result, expanded["primary"], expanded["synonyms"]
            )
            if relevance > 0.0:
                result["relevance_score"] = relevance
                result["matched_terms"] = matched_terms
                scored.append(result)

        logger.info(
            "After relevance filtering: %d/%d results kept for '%s'",
            len(scored), len(all_normalized), query,
        )

        # Step 3b: Filter by active status unless show_closed is true
        if not show_closed:
            before_active = len(scored)
            scored = [r for r in scored if r.get("is_active", False)]
            logger.info(
                "Active filter: %d/%d results kept for '%s'",
                len(scored), before_active, query,
            )

        # Step 4: Deduplicate by title similarity
        deduplicated = deduplicate_results(scored)

        # Step 5: Sort by relevance score desc, then by awarded_date desc
        deduplicated.sort(
            key=lambda x: (
                x.get("relevance_score", 0),
                x.get("awarded_date") or "",
            ),
            reverse=True,
        )

        # Count per source after filtering
        source_counts = {"procuredata": 0, "open_canada": 0, "sam_gov": 0, "usa_spending": 0}
        for r in deduplicated:
            src = r.get("source", "")
            if src in source_counts:
                source_counts[src] += 1

        total = len(deduplicated)

        # Step 6: Paginate
        start = (page - 1) * PAGE_SIZE
        page_results = deduplicated[start : start + PAGE_SIZE]

        # Step 7: Build response
        response_data = {
            "results": page_results,
            "total": total,
            "page": page,
            "sources": source_counts,
        }

        # If no relevant results, add helpful suggestions
        if total == 0:
            suggested = expanded["synonyms"][:5] if expanded["synonyms"] else []
            response_data["message"] = (
                f"No contracts found matching '{query}'. "
                + (
                    f"Try related terms like '{suggested[0]}' or '{suggested[1]}'."
                    if len(suggested) >= 2
                    else "Try broadening your search terms."
                )
            )
            response_data["suggested_terms"] = suggested

        logger.info(
            "Search '%s' returning %d results (page %d of %d total)",
            query, len(page_results), page, total,
        )

        return Response(response_data)
