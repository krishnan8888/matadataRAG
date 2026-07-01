import json
from pathlib import Path

from app.retrieval.matching import cosine_scores, hybrid_scores, keep_strong_results
from app.retrieval.types import RetrievalRequest, RetrievalResult
from app.table_rows import build_table_row_records


PROJECT_ROOT = Path(__file__).resolve().parents[2]
TABLE_DIR = PROJECT_ROOT / "app" / "tables"


def _backfill_table_rows(document_id: str, table_path: Path) -> dict:
    with open(table_path, "r", encoding="utf-8") as f:
        payload = json.load(f)

    records = build_table_row_records(payload)

    if not records:
        return {}

    from app.ingest.embedder import generate_embeddings
    from app.ingest.vectordb import store_table_rows

    embeddings = generate_embeddings([
        record["content"]
        for record in records
    ])
    store_table_rows(document_id, records, embeddings)

    from app.ingest.vectordb import get_table_rows

    return get_table_rows(document_id)


def retrieve(request: RetrievalRequest, profile: dict) -> list[RetrievalResult]:
    document_id = profile["document_id"]
    table_path = TABLE_DIR / f"{document_id}.json"

    if not table_path.exists():
        return []

    from app.ingest.vectordb import get_table_rows

    stored_rows = get_table_rows(document_id)

    if not stored_rows.get("ids"):
        stored_rows = _backfill_table_rows(document_id, table_path)

    documents = stored_rows.get("documents") or []
    metadatas = stored_rows.get("metadatas") or []
    embeddings = stored_rows.get("embeddings")

    if not documents or embeddings is None or len(embeddings) == 0:
        return []

    from app.ingest.embedder import generate_embeddings

    query_embedding = generate_embeddings([request.query])[0]
    semantic = cosine_scores(query_embedding, embeddings)
    scores = hybrid_scores(
        request.query,
        documents,
        precomputed_semantic_scores=semantic,
    )
    results = []

    for content, metadata, score in zip(documents, metadatas, scores):
        results.append(
            RetrievalResult(
                document_id=document_id,
                content=content,
                source="table_store",
                score=score,
                metadata={
                    "table_id": metadata.get("table_id", ""),
                    "row_index": metadata.get("row_index", 0),
                    "project_id": metadata.get("project_id", ""),
                    "document_section": metadata.get("document_section", ""),
                    "section_title": metadata.get("section_title", ""),
                }
            )
        )

    return keep_strong_results(results, request.top_k)
