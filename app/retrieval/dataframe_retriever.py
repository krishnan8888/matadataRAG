import json
from pathlib import Path

from app.retrieval.matching import keep_strong_results, row_to_text, term_score
from app.retrieval.types import RetrievalRequest, RetrievalResult


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATAFRAME_DIR = PROJECT_ROOT / "app" / "dataframes"


def retrieve(request: RetrievalRequest, profile: dict) -> list[RetrievalResult]:
    document_id = profile["document_id"]
    dataframe_path = DATAFRAME_DIR / f"{document_id}.json"

    if not dataframe_path.exists():
        return []

    with open(dataframe_path, "r", encoding="utf-8") as f:
        payload = json.load(f)

    results = []

    if "sheets" in payload:
        for sheet in payload.get("sheets", []):
            sheet_name = sheet.get("sheet_name", "")

            for row_index, row in enumerate(sheet.get("rows", [])):
                content = row_to_text(row)
                score = term_score(request.query, content)

                if score <= 0:
                    continue

                results.append(
                    RetrievalResult(
                        document_id=document_id,
                        content=content,
                        source="dataframe_store",
                        score=score,
                        metadata={
                            "sheet_name": sheet_name,
                            "row_index": row_index
                        }
                    )
                )
    else:
        for row_index, row in enumerate(payload.get("rows", [])):
            content = row_to_text(row)
            score = term_score(request.query, content)

            if score <= 0:
                continue

            results.append(
                RetrievalResult(
                    document_id=document_id,
                    content=content,
                    source="dataframe_store",
                    score=score,
                    metadata={
                        "row_index": row_index
                    }
                )
            )

    return keep_strong_results(results, request.top_k)
