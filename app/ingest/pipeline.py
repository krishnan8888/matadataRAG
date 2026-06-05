import json
from pathlib import Path

from app.ingest.loader import load_document
from app.ingest.metadata_gen import generate_metadata
from app.ingest.routing import (
    build_embedding_units,
    get_embedding_mode,
    get_retrieval_modes,
    get_storage_targets,
    get_unimplemented_storage_targets,
    should_store_vectors,
)
from app.ingest.stores import (
    store_dataframe,
    store_keyword_index,
    store_raw_file,
    store_structured_json,
    store_tables,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]
METADATA_DIR = PROJECT_ROOT / "app" / "metadata"


def save_metadata(document_id: str, metadata: dict) -> Path:
    METADATA_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    metadata_path = METADATA_DIR / f"{document_id}.json"

    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=4)

    return metadata_path


def store_non_vector_targets(
    document_id: str,
    file_path: Path,
    text: str,
    metadata: dict
) -> None:
    storage_targets = get_storage_targets(metadata)

    if "table_store" in storage_targets:
        table_path = store_tables(document_id, file_path)

        if table_path:
            print(f"Table store saved to: {table_path}")
        else:
            print("Table store selected, but no extractable tables were found.")

    if "dataframe_store" in storage_targets:
        dataframe_path = store_dataframe(document_id, file_path)

        if dataframe_path:
            print(f"Dataframe store saved to: {dataframe_path}")
        else:
            print(
                "Dataframe store selected, but this file type "
                "does not have a dataframe extractor yet."
            )

    if "structured_json_store" in storage_targets:
        structured_path = store_structured_json(document_id, metadata)
        print(f"Structured JSON store saved to: {structured_path}")

    if "keyword_index" in storage_targets:
        keyword_path = store_keyword_index(document_id, text, metadata)
        print(f"Keyword index saved to: {keyword_path}")

    if "raw_file_store" in storage_targets:
        raw_path = store_raw_file(document_id, file_path)
        print(f"Raw file saved to: {raw_path}")


def build_vector_metadata(metadata: dict) -> dict:
    return {
        "document_type": metadata.get("document_type", ""),
        "content_structure": metadata.get("content_structure", ""),
        "embedding_mode": metadata.get("embedding_mode", ""),
        "retrieval_modes": ",".join(metadata.get("retrieval_modes", [])),
        "storage_targets": ",".join(metadata.get("storage_targets", [])),
        "chunking_strategy": metadata.get("chunking_strategy", ""),
        "table_handling": metadata.get("table_handling", ""),
    }


def ingest_document(file_path: str):
    source_path = Path(file_path).resolve()
    document_id = source_path.stem

    print(f"\n--- INGESTING: {document_id} ---\n")

    # -----------------------------------
    # LOAD DOCUMENT
    # -----------------------------------

    print("Loading document...")

    text = load_document(str(source_path))

    print("Document loaded successfully.")

    # -----------------------------------
    # GENERATE METADATA
    # -----------------------------------

    print("\nGenerating metadata...")

    metadata = generate_metadata(text)

    # -----------------------------------
    # SAVE METADATA
    # -----------------------------------

    metadata_path = save_metadata(document_id, metadata)

    print(f"Metadata saved to: {metadata_path}")

    # -----------------------------------
    # RETRIEVAL PROFILE / ROUTING DECISION
    # -----------------------------------

    embedding_mode = get_embedding_mode(metadata)
    retrieval_modes = get_retrieval_modes(metadata)
    storage_targets = get_storage_targets(metadata)

    print("\nRetrieval profile selected:")
    print(f"Embedding mode: {embedding_mode}")
    print(f"Retrieval modes: {', '.join(retrieval_modes)}")
    print(f"Storage targets: {', '.join(storage_targets)}")

    # -----------------------------------
    # STORAGE TARGET ROUTING
    # -----------------------------------

    planned_targets = get_unimplemented_storage_targets(metadata)

    for target in planned_targets:
        print(
            f"Storage target '{target}' is planned "
            "but not implemented yet."
        )

    store_non_vector_targets(
        document_id=document_id,
        file_path=source_path,
        text=text,
        metadata=metadata
    )

    # -----------------------------------
    # VECTOR STORAGE PIPELINE
    # -----------------------------------

    if should_store_vectors(metadata):
        from app.ingest.vectordb import delete_document_vectors

        delete_document_vectors(document_id)

        print("\nPreparing embedding units...")

        embedding_units = build_embedding_units(text, metadata)

        print(f"Generated {len(embedding_units)} embedding units.")

        if not embedding_units:
            print("No embedding units generated; skipping vector storage.")
            print(f"\n--- INGESTION COMPLETE: {document_id} ---\n")
            return

        print("\nGenerating embeddings...")

        from app.ingest.embedder import generate_embeddings
        from app.ingest.vectordb import store_document

        embeddings = generate_embeddings(embedding_units)

        print("Embeddings generated successfully.")

        print("\nStoring in vector database...")

        store_document(
            document_id=document_id,
            chunks=embedding_units,
            embeddings=embeddings,
            base_metadata=build_vector_metadata(metadata)
        )

        print("Vector storage complete.")

    # -----------------------------------
    # NON-EMBEDDING PIPELINE
    # -----------------------------------

    else:
        from app.ingest.vectordb import delete_document_vectors

        delete_document_vectors(document_id)

        print(
            "\nSkipping vector embedding generation "
            "for this retrieval profile."
        )

        print(
            "Document will rely on the non-vector retrieval "
            "modes listed in its metadata."
        )

    # -----------------------------------
    # COMPLETE
    # -----------------------------------

    print(f"\n--- INGESTION COMPLETE: {document_id} ---\n")
