import os
from pathlib import Path

from app.retrieval.types import RetrievalRequest, RetrievalResult


os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")

import chromadb


PROJECT_ROOT = Path(__file__).resolve().parents[2]
VECTOR_DB_DIR = PROJECT_ROOT / "app" / "vectordb"


def retrieve(request: RetrievalRequest, profile: dict) -> list[RetrievalResult]:
    from app.ingest.embedder import generate_embeddings

    document_id = profile["document_id"]
    query_embedding = generate_embeddings([request.query])

    if hasattr(query_embedding, "tolist"):
        query_embedding = query_embedding.tolist()

    client = chromadb.PersistentClient(
        path=str(VECTOR_DB_DIR)
    )
    collection = client.get_collection("documents")

    response = collection.query(
        query_embeddings=query_embedding,
        n_results=request.top_k,
        where={
            "document_id": document_id
        }
    )

    results = []
    ids = response.get("ids", [[]])[0]
    documents = response.get("documents", [[]])[0]
    metadatas = response.get("metadatas", [[]])[0]
    distances = response.get("distances", [[]])[0]

    for index, content in enumerate(documents):
        distance = distances[index] if index < len(distances) else None
        score = None if distance is None else 1 / (1 + distance)

        results.append(
            RetrievalResult(
                document_id=document_id,
                content=content,
                source="vector_db",
                score=score,
                metadata={
                    "chunk_id": ids[index] if index < len(ids) else "",
                    **(metadatas[index] if index < len(metadatas) else {})
                }
            )
        )

    return results
