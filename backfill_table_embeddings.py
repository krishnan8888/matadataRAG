import json
from pathlib import Path

from app.ingest.embedder import generate_embeddings
from app.ingest.vectordb import delete_table_row_vectors, store_table_rows
from app.table_rows import build_table_row_records


PROJECT_ROOT = Path(__file__).resolve().parent
TABLE_DIR = PROJECT_ROOT / "app" / "tables"


def main() -> None:
    for table_path in sorted(TABLE_DIR.glob("*.json")):
        with open(table_path, "r", encoding="utf-8") as f:
            payload = json.load(f)

        document_id = payload.get("document_id", table_path.stem)
        records = build_table_row_records(payload)
        delete_table_row_vectors(document_id)

        if records:
            embeddings = generate_embeddings([
                record["content"]
                for record in records
            ])
            store_table_rows(document_id, records, embeddings)

        print(f"{document_id}: {len(records)} table rows persisted")


if __name__ == "__main__":
    main()
