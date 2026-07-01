import os
from urllib.parse import urlparse


OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
OLLAMA_KEEP_ALIVE = os.getenv("OLLAMA_KEEP_ALIVE", "30m")
METADATA_MODEL = os.getenv("METADATA_MODEL", "qwen2.5-coder:7b")
ANSWER_MODEL = os.getenv("ANSWER_MODEL", "qwen2.5-coder:7b")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "BAAI/bge-small-en-v1.5")

_ollama_host = urlparse(OLLAMA_BASE_URL).hostname
_local_shutdown_default = _ollama_host in {"127.0.0.1", "localhost", "::1"}
LOCAL_SHUTDOWN_ENABLED = os.getenv(
    "LOCAL_SHUTDOWN_ENABLED",
    str(_local_shutdown_default),
).lower() in {"1", "true", "yes"}
