import json
from pathlib import Path

from app.retrieval.matching import term_score
from app.retrieval.types import RetrievalRequest, RetrievalResult


PROJECT_ROOT = Path(__file__).resolve().parents[2]
KEYWORD_INDEX_DIR = PROJECT_ROOT / "app" / "keyword_index"


def retrieve(request: RetrievalRequest, profile: dict) -> list[RetrievalResult]:
    document_id = profile["document_id"]
    keyword_path = KEYWORD_INDEX_DIR / f"{document_id}.json"

    if not keyword_path.exists():
        return []

    with open(keyword_path, "r", encoding="utf-8") as f:
        payload = json.load(f)

    terms = payload.get("terms", [])
    matched_terms = [
        term
        for term in terms
        if term_score(request.query, term) > 0
    ]

    if not matched_terms:
        return []

    return [
        RetrievalResult(
            document_id=document_id,
            content=", ".join(matched_terms[:request.top_k]),
            source="keyword_index",
            score=min(1.0, len(matched_terms) / max(1, request.top_k)),
            metadata={
                "matched_terms": matched_terms[:request.top_k]
            }
        )
    ]
