import os


os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")

from sentence_transformers import SentenceTransformer

from app.settings import EMBEDDING_MODEL

embedding_model = SentenceTransformer(
    EMBEDDING_MODEL
)


def generate_embeddings(chunks: list[str]):

    embeddings = embedding_model.encode(
        chunks,
        convert_to_tensor=False
    )

    return embeddings
