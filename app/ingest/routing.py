from app.ingest.chunker import chunk_document


VECTOR_STORAGE_TARGET = "vector_db"

TEXT_CHUNK_EMBEDDING_MODES = {
    "full_text_chunks",
    "hybrid_text_and_table",
    "code_chunks",
}

SUMMARY_EMBEDDING_MODES = {
    "summary_only",
    "table_summaries",
}

IMPLEMENTED_STORAGE_TARGETS = {
    "metadata_store",
    "vector_db",
    "table_store",
    "dataframe_store",
    "structured_json_store",
    "keyword_index",
    "raw_file_store",
}


def get_embedding_mode(metadata: dict) -> str:
    return metadata.get("embedding_mode", "none")


def get_retrieval_modes(metadata: dict) -> list[str]:
    return metadata.get("retrieval_modes", [])


def get_storage_targets(metadata: dict) -> list[str]:
    return metadata.get("storage_targets", [])


def should_store_vectors(metadata: dict) -> bool:
    embedding_mode = get_embedding_mode(metadata)
    storage_targets = get_storage_targets(metadata)

    return (
        VECTOR_STORAGE_TARGET in storage_targets
        and embedding_mode != "none"
    )


def build_embedding_units(text: str, metadata: dict) -> list[str]:
    embedding_mode = get_embedding_mode(metadata)

    if embedding_mode in TEXT_CHUNK_EMBEDDING_MODES:
        return chunk_document(text)

    if embedding_mode in SUMMARY_EMBEDDING_MODES:
        summary = metadata.get("summary", "").strip()
        return [summary] if summary else []

    return []


def get_unimplemented_storage_targets(metadata: dict) -> list[str]:
    return [
        target
        for target in get_storage_targets(metadata)
        if target not in IMPLEMENTED_STORAGE_TARGETS
    ]
