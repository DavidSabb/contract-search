"""
Government contract API clients.

Each client fetches contracts from a different source and returns raw results.
All clients have a 10-second timeout and return an empty list on failure.
Each client accepts an `expanded` dict from query_expander.expand_query()
and fetches up to 50 results for post-filtering by the relevance scorer.

APIs:
  1. ProcureData (Canadian federal) — RapidAPI
     Base URL: https://procuredata-canadian-government-procurement-api.p.rapidapi.com
     Endpoints: /contract, /tender, /award, /disclosure (singular, not plural)
     Pagination: limit (default 100, max 500) + offset (not page)
     Auth: X-RapidAPI-Key and X-RapidAPI-Host headers (from .env)

  2. Open Canada (Canadian federal — proactive disclosure)
     Base URL: https://open.canada.ca/data/api
     Auth: None (public)

  3. SAM.gov (US federal — contract opportunities)
     Base URL: https://api.sam.gov
     Auth: api_key query param (from .env SAM_GOV)

  4. USASpending (US federal — awarded contracts)
     Base URL: https://api.usaspending.gov/api
     Auth: None (public)
"""

import logging
import os
import time
from datetime import datetime, timedelta

import requests

logger = logging.getLogger(__name__)

TIMEOUT = 10
FETCH_LIMIT = 50  # Fetch more than needed, then relevance-filter down
SAM_MAX_RETRIES = 3
SAM_RETRY_DELAY = 2  # seconds, doubles each retry


def search_procuredata(expanded: dict, page: int = 1) -> list[dict]:
    """Search ProcureData Canadian government procurement API.
    Uses the primary query term — ProcureData handles full-text search well.

    Endpoints use singular names: /contract, /tender (not /contracts, /tenders).
    Pagination uses limit/offset (not page). Default limit is 100, max 500.
    Response format: {"entity_type": str, "count": int, "offset": int, "results": [...]}
    """
    api_key = os.getenv("x-rapidapi-key", "")
    api_host = os.getenv("x-rapidapi-host", "")

    if not api_key or not api_host:
        logger.warning("ProcureData: missing API key or host in .env")
        return []

    headers = {
        "X-RapidAPI-Key": api_key,
        "X-RapidAPI-Host": api_host,
    }
    base_url = f"https://{api_host}"
    results = []
    offset = (page - 1) * FETCH_LIMIT

    for endpoint in ("/contract", "/tender"):
        try:
            resp = requests.get(
                f"{base_url}{endpoint}",
                headers=headers,
                params={
                    "q": expanded["primary"],
                    "limit": FETCH_LIMIT,
                    "offset": offset,
                },
                timeout=TIMEOUT,
            )
            resp.raise_for_status()
            data = resp.json()
            results.extend(data.get("results", []))
        except Exception as e:
            logger.warning("ProcureData %s failed: %s", endpoint, e)

    logger.info("ProcureData returned %d raw results for '%s'", len(results), expanded["primary"])
    return results


def search_open_canada(expanded: dict, page: int = 1) -> list[dict]:
    """Search Open Canada proactive disclosure contracts.

    Two resources available:
      - Main (fac950c0): current data, 100k+ rows, NO full-text q= support.
        Use field-based filters={"description_en": "query"} instead.
      - Legacy (7f9b18ca): older data, supports full-text q= search.
    We query both and merge results.
    """
    base_url = "https://open.canada.ca/data/api/3/action/datastore_search"
    offset = (page - 1) * FETCH_LIMIT
    records = []

    # 1. Legacy resource — supports full-text q= search
    legacy_id = "7f9b18ca-f627-4852-93d5-69adeb9437d6"
    try:
        resp = requests.get(
            base_url,
            params={
                "resource_id": legacy_id,
                "q": expanded["open_canada_query"],
                "limit": FETCH_LIMIT,
                "offset": offset,
            },
            timeout=TIMEOUT,
        )
        resp.raise_for_status()
        data = resp.json()
        legacy_records = data.get("result", {}).get("records", [])
        records.extend(legacy_records)
        logger.info("Open Canada (legacy) returned %d results for '%s'", len(legacy_records), expanded["primary"])
    except Exception as e:
        logger.warning("Open Canada (legacy) failed: %s", e)

    # 2. Main resource — field-based filter on description_en
    main_id = "fac950c0-00d5-4ec1-a4d3-9cbebf98a305"
    try:
        import json
        resp = requests.get(
            base_url,
            params={
                "resource_id": main_id,
                "filters": json.dumps({"description_en": expanded["open_canada_query"]}),
                "limit": FETCH_LIMIT,
                "offset": offset,
            },
            timeout=TIMEOUT,
        )
        resp.raise_for_status()
        data = resp.json()
        main_records = data.get("result", {}).get("records", [])
        records.extend(main_records)
        logger.info("Open Canada (main) returned %d results for '%s'", len(main_records), expanded["primary"])
    except Exception as e:
        logger.warning("Open Canada (main) failed: %s", e)

    logger.info("Open Canada total: %d raw results for '%s'", len(records), expanded["primary"])
    return records


def search_sam_gov(expanded: dict, page: int = 1) -> list[dict]:
    """Search SAM.gov contract opportunities.
    Uses expanded keywords joined with spaces (SAM.gov uses implicit OR).
    Filters to relevant notice types only. Fetches 50 for post-filtering.
    Retries up to 3 times on 429 (rate limit) with exponential backoff.
    """
    api_key = os.getenv("SAM_GOV", "")
    if not api_key:
        logger.warning("SAM.gov: missing API key in .env")
        return []

    url = "https://api.sam.gov/opportunities/v2/search"
    posted_from = (datetime.now() - timedelta(days=90)).strftime("%m/%d/%Y")
    posted_to = datetime.now().strftime("%m/%d/%Y")
    offset = (page - 1) * 20

    params = {
        "api_key": api_key,
        "q": expanded["sam_query"],
        "limit": FETCH_LIMIT,
        "offset": offset,
        "postedFrom": posted_from,
        "postedTo": posted_to,
        "ptype": "o,k,p,r,s",
        "active": "true",
    }

    delay = SAM_RETRY_DELAY
    for attempt in range(SAM_MAX_RETRIES):
        try:
            resp = requests.get(url, params=params, timeout=TIMEOUT)
            if resp.status_code == 429:
                if attempt < SAM_MAX_RETRIES - 1:
                    logger.info("SAM.gov rate limited, retrying in %ds (attempt %d/%d)", delay, attempt + 1, SAM_MAX_RETRIES)
                    time.sleep(delay)
                    delay *= 2
                    continue
                logger.warning("SAM.gov rate limited after %d retries", SAM_MAX_RETRIES)
                return []
            resp.raise_for_status()
            data = resp.json()
            records = data.get("opportunitiesData", [])
            logger.info("SAM.gov returned %d raw results for '%s'", len(records), expanded["primary"])
            return records
        except requests.exceptions.HTTPError:
            # Already handled 429 above; other HTTP errors fall through
            if resp.status_code != 429:
                logger.warning("SAM.gov failed: %s %s", resp.status_code, resp.reason)
                return []
        except Exception as e:
            logger.warning("SAM.gov failed: %s", e)
            return []

    return []


def search_usa_spending(expanded: dict, page: int = 1) -> list[dict]:
    """Search USASpending awarded contracts.
    Passes the full expanded keywords list for broader matching,
    then relies on relevance scoring to filter out weak results.
    """
    url = "https://api.usaspending.gov/api/v2/search/spending_by_award/"
    today = datetime.now().strftime("%Y-%m-%d")
    ninety_days_ago = (datetime.now() - timedelta(days=90)).strftime("%Y-%m-%d")

    payload = {
        "filters": {
            "keywords": expanded["keywords_list"],
            "award_type_codes": ["A", "B", "C", "D"],
            "time_period": [{
                "start_date": ninety_days_ago,
                "end_date": today,
                "date_type": "date_signed",
            }],
        },
        "fields": [
            "Award ID",
            "Recipient Name",
            "Award Amount",
            "Awarding Agency",
            "Award Date",
            "End Date",
            "Description",
            "generated_internal_id",
        ],
        "page": page,
        "limit": FETCH_LIMIT,
        "sort": "Award Amount",
        "order": "desc",
    }

    try:
        resp = requests.post(url, json=payload, timeout=TIMEOUT)
        resp.raise_for_status()
        data = resp.json()
        records = data.get("results", [])
        logger.info("USASpending returned %d raw results for '%s'", len(records), expanded["primary"])
        return records
    except Exception as e:
        logger.warning("USASpending failed: %s", e)
        return []
