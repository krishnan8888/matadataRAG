import re

import numpy as np


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


def exact_identifier_score(query: str, text: str) -> float:
    query_identifiers = {
        identifier.lower()
        for identifier in re.findall(
            r"\b(?=[A-Za-z0-9_-]*[A-Za-z])(?=[A-Za-z0-9_-]*\d)"
            r"[A-Za-z0-9]+(?:[-_][A-Za-z0-9]+)+\b",
            query,
        )
    }

    if not query_identifiers:
        return 0.0

    normalized_text = text.lower()
    matches = sum(
        identifier in normalized_text
        for identifier in query_identifiers
    )
    return matches / len(query_identifiers)


def semantic_scores(query: str, texts: list[str]) -> list[float]:
    if not texts:
        return []

    from app.ingest.embedder import generate_embeddings

    embeddings = np.asarray(
        generate_embeddings([query, *texts]),
        dtype=float,
    )
    query_embedding = embeddings[0]
    text_embeddings = embeddings[1:]
    query_norm = np.linalg.norm(query_embedding)
    text_norms = np.linalg.norm(text_embeddings, axis=1)
    denominators = text_norms * query_norm
    similarities = np.divide(
        text_embeddings @ query_embedding,
        denominators,
        out=np.zeros(len(texts), dtype=float),
        where=denominators != 0,
    )

    return [
        max(0.0, min(1.0, float(score)))
        for score in similarities
    ]


def hybrid_scores(
    query: str,
    texts: list[str],
) -> list[float]:
    query_has_identifier = exact_identifier_score(query, query) > 0
    lexical_weight = 0.45 if query_has_identifier else 0.55
    identifier_weight = 0.40 if query_has_identifier else 0.0
    semantic_weight = 1.0 - lexical_weight - identifier_weight
    lexical = [term_score(query, text) for text in texts]
    identifiers = [exact_identifier_score(query, text) for text in texts]
    semantic = semantic_scores(query, texts)

    return [
        lexical_weight * lexical_score
        + identifier_weight * identifier_score
        + semantic_weight * semantic_score
        for lexical_score, identifier_score, semantic_score
        in zip(lexical, identifiers, semantic)
    ]


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
