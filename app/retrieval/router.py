from app.retrieval import (
    dataframe_retriever,
    keyword_retriever,
    structured_retriever,
    table_retriever,
    vector_retriever,
)
from app.retrieval.metadata_retriever import select_candidate_documents
from app.retrieval.types import RetrievalRequest, RetrievalResult


RETRIEVER_BY_MODE = {
    "semantic_search": vector_retriever,
    "table_lookup": table_retriever,
    "dataframe_query": dataframe_retriever,
    "structured_field_lookup": structured_retriever,
    "keyword_search": keyword_retriever,
}


def route_query(
    query: str,
    top_k_docs: int = 5,
    top_k_results: int = 5
) -> dict:
    request = RetrievalRequest(
        query=query,
        top_k=top_k_results
    )
    candidates = select_candidate_documents(
        query,
        top_k=top_k_docs
    )
    results = []
    errors = []

    for profile in candidates:
        retrieval_modes = profile.get("retrieval_modes", [])

        for mode in retrieval_modes:
            retriever = RETRIEVER_BY_MODE.get(mode)

            if retriever is None:
                continue

            try:
                results.extend(retriever.retrieve(request, profile))

            except Exception as exc:
                errors.append({
                    "document_id": profile.get("document_id", ""),
                    "retrieval_mode": mode,
                    "error": str(exc)
                })

    results.sort(
        key=lambda result: result.score or 0,
        reverse=True
    )

    return {
        "query": query,
        "chosen_documents": candidates,
        "results": results[:top_k_results],
        "errors": errors
    }
