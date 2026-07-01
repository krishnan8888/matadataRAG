import os
from pathlib import Path


os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")

import chromadb


PROJECT_ROOT = Path(__file__).resolve().parents[2]


client = chromadb.PersistentClient(
    path=str(PROJECT_ROOT / "app" / "vectordb")
)


collection = client.get_or_create_collection(
    name="documents"
)

table_row_collection = client.get_or_create_collection(
    name="table_rows"
)


def delete_document_vectors(document_id: str) -> None:
    collection.delete(
        where={
            "document_id": document_id
        }
    )


def delete_table_row_vectors(document_id: str) -> None:
    table_row_collection.delete(
        where={
            "document_id": document_id
        }
    )


def store_table_rows(document_id: str, records: list[dict], embeddings) -> None:
    if not records:
        return

    if hasattr(embeddings, "tolist"):
        embeddings = embeddings.tolist()

    ids = []
    documents = []
    metadatas = []

    for record_index, record in enumerate(records):
        ids.append(f"{document_id}_table_row_{record_index}")
        documents.append(record["content"])
        metadatas.append({
            "document_id": document_id,
            "table_id": record.get("table_id", ""),
            "row_index": record.get("row_index", 0),
            "project_id": record.get("project_id", ""),
            "document_section": record.get("document_section", ""),
            "section_title": record.get("section_title", ""),
        })

    table_row_collection.upsert(
        ids=ids,
        documents=documents,
        embeddings=embeddings,
        metadatas=metadatas,
    )


def get_table_rows(document_id: str) -> dict:
    return table_row_collection.get(
        where={
            "document_id": document_id
        },
        include=["documents", "metadatas", "embeddings"],
    )


def store_document(
    document_id: str,
    chunks: list[str],
    embeddings,
    base_metadata: dict | None = None
):

    ids = []

    metadatas = []

    for i in range(len(chunks)):

        ids.append(f"{document_id}_chunk_{i}")

        chunk_metadata = {
            "document_id": document_id,
            "chunk_index": i
        }

        if base_metadata:
            chunk_metadata.update(base_metadata)

        metadatas.append(chunk_metadata)

    if hasattr(embeddings, "tolist"):
        embeddings = embeddings.tolist()

    collection.upsert(
        ids=ids,
        documents=chunks,
        embeddings=embeddings,
        metadatas=metadatas
    )
