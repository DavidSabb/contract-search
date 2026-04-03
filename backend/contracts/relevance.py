"""
Relevance scoring and deduplication for contract search results.

Scores each result 0.0–1.0 based on how well its title and description
match the query and its synonyms. Results scoring 0.0 are discarded.
"""

import re


def _tokenize(text: str) -> list[str]:
    """Lowercase, strip punctuation, split into words."""
    cleaned = re.sub(r"[^\w\s]", " ", text.lower())
    return cleaned.split()


def _word_match(term: str, text_tokens: list[str]) -> bool:
    """
    Check if a term appears as whole word(s) in the token list.
    For multi-word terms like 'blister pack', checks if all words appear.
    Avoids partial matches like 'pack' in 'backpack' by checking token boundaries.
    """
    term_words = term.lower().split()
    if len(term_words) == 1:
        return term_words[0] in text_tokens
    # Multi-word: all words must be present
    return all(w in text_tokens for w in term_words)


def _text_contains(term: str, raw_text: str) -> bool:
    """
    Check if term appears as a whole word in raw text using regex.
    More precise than token matching for single words — catches
    hyphenated forms like 'pre-packaging'.
    """
    pattern = r"\b" + re.escape(term.lower()) + r"\b"
    return bool(re.search(pattern, raw_text.lower()))


def score_result(
    result: dict, primary_query: str, synonyms: list[str]
) -> tuple[float, list[str]]:
    """
    Score a normalized contract result for relevance.

    Returns (score, matched_terms) where score is 0.0–1.0.
    A score of 0.0 means the result should be excluded.
    matched_terms lists which terms matched and where.
    """
    title = (result.get("title") or "").lower()
    description = (result.get("description") or "").lower()
    title_tokens = _tokenize(title)
    desc_tokens = _tokenize(description)

    score = 0.0
    matched_terms = []

    # Primary query in title → +0.5
    if _text_contains(primary_query, title):
        score += 0.5
        matched_terms.append(f"title contains '{primary_query}'")
    # Primary query in description → +0.3
    if _text_contains(primary_query, description):
        score += 0.3
        matched_terms.append(f"description contains '{primary_query}'")

    # Synonyms in title → +0.3 (once, for first match)
    synonym_in_title = False
    for syn in synonyms:
        if _text_contains(syn, title) or _word_match(syn, title_tokens):
            if not synonym_in_title:
                score += 0.3
                synonym_in_title = True
            matched_terms.append(f"title contains '{syn}'")

    # Synonyms in description → +0.2 (once, for first match)
    synonym_in_desc = False
    for syn in synonyms:
        if _text_contains(syn, description) or _word_match(syn, desc_tokens):
            if not synonym_in_desc:
                score += 0.2
                synonym_in_desc = True
            matched_terms.append(f"description contains '{syn}'")

    # If nothing matched at all, this result is irrelevant
    if score == 0.0:
        return 0.0, []

    # Boost if contract has a real value
    if result.get("value") and result["value"] > 0:
        score += 0.1

    # Cap at 1.0
    score = min(score, 1.0)

    return round(score, 2), matched_terms


def _title_similarity(title_a: str, title_b: str) -> float:
    """
    Compute token-overlap similarity between two titles (Jaccard-like).
    Returns 0.0–1.0.
    """
    tokens_a = set(_tokenize(title_a))
    tokens_b = set(_tokenize(title_b))
    if not tokens_a or not tokens_b:
        return 0.0
    intersection = tokens_a & tokens_b
    union = tokens_a | tokens_b
    return len(intersection) / len(union)


def deduplicate_results(results: list[dict], threshold: float = 0.8) -> list[dict]:
    """
    Remove near-duplicate results by title similarity.
    When two results have >threshold title similarity, keep the higher-scored one.
    """
    if not results:
        return results

    # Sort by relevance_score descending so we keep the best version
    sorted_results = sorted(
        results, key=lambda x: x.get("relevance_score", 0), reverse=True
    )

    kept = []
    for result in sorted_results:
        title = result.get("title", "")
        is_dup = False
        for existing in kept:
            if _title_similarity(title, existing.get("title", "")) > threshold:
                is_dup = True
                break
        if not is_dup:
            kept.append(result)

    return kept
