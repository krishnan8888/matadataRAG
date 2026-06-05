import re


STOP_WORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "for",
    "from",
    "how",
    "in",
    "is",
    "it",
    "of",
    "on",
    "or",
    "the",
    "to",
    "was",
    "what",
    "when",
    "where",
    "which",
    "who",
    "with",
}


def tokenize(text: str) -> set[str]:
    return {
        token
        for token in re.findall(r"[a-zA-Z0-9_]+", text.lower())
        if len(token) >= 2 and token not in STOP_WORDS
    }


def row_to_text(row) -> str:
    if isinstance(row, dict):
        return " | ".join(
            f"{key}: {value}"
            for key, value in row.items()
        )

    if isinstance(row, list):
        return " | ".join(str(value) for value in row)

    return str(row)


def term_score(query: str, text: str) -> float:
    query_terms = tokenize(query)

    if not query_terms:
        return 0

    text_terms = tokenize(text)
    overlap = query_terms.intersection(text_terms)
    score = len(overlap) / len(query_terms)

    if query.lower() in text.lower():
        score = 1.0

    return score


def keep_strong_results(results: list, top_k: int, relative_threshold: float = 0.8):
    if not results:
        return []

    results.sort(
        key=lambda result: result.score or 0,
        reverse=True
    )
    best_score = results[0].score or 0
    minimum_score = best_score * relative_threshold

    return [
        result
        for result in results
        if (result.score or 0) >= minimum_score
    ][:top_k]
