import json
from pathlib import Path

from app.retrieval.matching import keep_strong_results, row_to_text, term_score
from app.retrieval.types import RetrievalRequest, RetrievalResult


PROJECT_ROOT = Path(__file__).resolve().parents[2]
TABLE_DIR = PROJECT_ROOT / "app" / "tables"


def retrieve(request: RetrievalRequest, profile: dict) -> list[RetrievalResult]:
    document_id = profile["document_id"]
    table_path = TABLE_DIR / f"{document_id}.json"

    if not table_path.exists():
        return []

    with open(table_path, "r", encoding="utf-8") as f:
        payload = json.load(f)

    results = []

    for table in payload.get("tables", []):
        table_id = table.get("table_id", document_id)

        for row_index, row in enumerate(table.get("rows", [])):
            content = row_to_text(row)
            score = term_score(request.query, content)

            if score <= 0:
                continue

            results.append(
                RetrievalResult(
                    document_id=document_id,
                    content=content,
                    source="table_store",
                    score=score,
                    metadata={
                        "table_id": table_id,
                        "row_index": row_index
                    }
                )
            )

    return keep_strong_results(results, request.top_k)
