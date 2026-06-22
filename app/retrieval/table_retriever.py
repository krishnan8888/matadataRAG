import json
from pathlib import Path

from app.retrieval.matching import hybrid_scores, keep_strong_results, row_to_text
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

    row_candidates = []

    for table in payload.get("tables", []):
        table_id = table.get("table_id", document_id)
        project_id = table.get("project_id", "")
        document_section = table.get("document_section", "")
        section_title = table.get("section_title", "")
        rows = table.get("rows", [])
        columns = rows[0] if rows and isinstance(rows[0], list) else []

        for row_index, row in enumerate(rows):
            if row_index == 0 and columns:
                continue

            if columns and isinstance(row, list):
                row = {
                    str(column): row[index] if index < len(row) else ""
                    for index, column in enumerate(columns)
                }

            row_content = row_to_text(row)
            context = " | ".join(
                value
                for value in (
                    f"Project: {project_id}" if project_id else "",
                    document_section,
                    section_title,
                    row_content,
                )
                if value
            )
            row_candidates.append({
                "content": context,
                "table_id": table_id,
                "row_index": row_index,
                "project_id": project_id,
                "document_section": document_section,
                "section_title": section_title,
            })

    scores = hybrid_scores(
        request.query,
        [candidate["content"] for candidate in row_candidates],
    )
    results = []

    for candidate, score in zip(row_candidates, scores):
        results.append(
            RetrievalResult(
                document_id=document_id,
                content=candidate["content"],
                source="table_store",
                score=score,
                metadata={
                    "table_id": candidate["table_id"],
                    "row_index": candidate["row_index"],
                    "project_id": candidate["project_id"],
                    "document_section": candidate["document_section"],
                    "section_title": candidate["section_title"],
                }
            )
        )

    return keep_strong_results(results, request.top_k)
