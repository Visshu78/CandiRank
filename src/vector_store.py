"""In-memory retrieval helpers used by the deterministic baseline."""


def lexical_similarity(query: str, text: str) -> float:
    query_terms = {term for term in query.lower().split() if len(term) > 2}
    if not query_terms:
        return 0.0
    text_l = text.lower()
    return sum(1 for term in query_terms if term in text_l) / len(query_terms)
