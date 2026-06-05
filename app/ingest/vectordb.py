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


def delete_document_vectors(document_id: str) -> None:
    collection.delete(
        where={
            "document_id": document_id
        }
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
