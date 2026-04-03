"""
Expand plain-English search queries into procurement-specific terminology.

Maps common terms to their procurement synonyms so API queries and
relevance scoring can match contracts using industry-specific language.
"""

PROCUREMENT_SYNONYMS: dict[str, list[str]] = {
    "packaging": [
        "packaging", "packing", "package", "containerization",
        "wrapping", "crating", "kitting", "pouching", "bagging",
        "blister pack", "labeling and packaging",
    ],
    "it": [
        "information technology", "software", "hardware", "cyber",
        "network", "IT services", "cloud computing", "data center",
        "systems integration", "cybersecurity",
    ],
    "it consulting": [
        "IT consulting", "information technology consulting",
        "technology advisory", "systems consulting", "IT professional services",
        "software consulting", "digital transformation",
    ],
    "construction": [
        "construction", "renovation", "infrastructure", "building",
        "general contractor", "site work", "demolition", "civil works",
        "structural", "masonry", "paving",
    ],
    "cleaning": [
        "cleaning", "janitorial", "custodial", "sanitation",
        "housekeeping", "facility maintenance", "disinfection",
    ],
    "security": [
        "security", "guard services", "surveillance", "access control",
        "protective services", "security systems", "patrol",
    ],
    "consulting": [
        "consulting", "advisory", "professional services", "management consulting",
        "strategy", "analysis", "assessment",
    ],
    "transportation": [
        "transportation", "trucking", "freight", "logistics",
        "shipping", "hauling", "delivery services", "cargo",
    ],
    "medical": [
        "medical", "healthcare", "clinical", "pharmaceutical",
        "biomedical", "health services", "medical supplies",
    ],
    "food": [
        "food", "catering", "meal services", "food supply",
        "provisions", "rations", "dietary",
    ],
}


def expand_query(user_query: str) -> dict:
    """
    Expand a user search query into procurement-specific terms.

    Returns a dict with:
        primary: the original query (lowered)
        synonyms: list of related procurement terms
        keywords_list: primary + synonyms combined
        sam_query: space-separated keywords for SAM.gov
        open_canada_query: simpler query for CKAN
    """
    normalized = user_query.strip().lower()

    # Try exact match first, then check if query contains a known key
    synonyms = []
    if normalized in PROCUREMENT_SYNONYMS:
        synonyms = PROCUREMENT_SYNONYMS[normalized]
    else:
        for key, syns in PROCUREMENT_SYNONYMS.items():
            if key in normalized or normalized in key:
                synonyms = syns
                break

    # If no synonym map found, use the query as-is
    if not synonyms:
        synonyms = [normalized]

    # Build the full keywords list (primary first, then synonyms without dupes)
    keywords_list = [normalized]
    for s in synonyms:
        if s.lower() != normalized:
            keywords_list.append(s)

    return {
        "primary": normalized,
        "synonyms": [s for s in synonyms if s.lower() != normalized],
        "keywords_list": keywords_list,
        "sam_query": " ".join(keywords_list[:5]),
        "open_canada_query": normalized,
    }
