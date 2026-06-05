import os


OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
METADATA_MODEL = os.getenv("METADATA_MODEL", "qwen2.5-coder:7b")
ANSWER_MODEL = os.getenv("ANSWER_MODEL", "qwen2.5-coder:7b")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "BAAI/bge-small-en-v1.5")
