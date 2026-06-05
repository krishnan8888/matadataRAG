import argparse
import os
from pathlib import Path


os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")

from app.ingest.pipeline import ingest_document


DATA_DIR = Path(__file__).resolve().parent / "app" / "data"

FILES_TO_INGEST = [
    DATA_DIR / "ChangeOrder124.docx",
    DATA_DIR / "Global_Role_Rate_Card.xlsx",
]


def get_files_to_ingest() -> list[Path]:
    parser = argparse.ArgumentParser(
        description="Ingest files into the metadata-first RAG pipeline."
    )
    parser.add_argument(
        "files",
        nargs="*",
        help="File paths to ingest. Defaults to the project sample files."
    )

    args = parser.parse_args()

    if args.files:
        return [
            Path(file_path)
            for file_path in args.files
        ]

    return FILES_TO_INGEST


def main():
    for file_path in get_files_to_ingest():
        if not file_path.exists():
            print(f"Skipping missing file: {file_path}")
            continue

        ingest_document(str(file_path))


if __name__ == "__main__":
    main()
