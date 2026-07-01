FROM python:3.11-slim

ARG EMBEDDING_MODEL=BAAI/bge-small-en-v1.5

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    HOST=0.0.0.0 \
    PORT=8000 \
    OLLAMA_BASE_URL=http://host.docker.internal:11434 \
    METADATA_MODEL=qwen2.5-coder:7b \
    ANSWER_MODEL=qwen2.5-coder:7b \
    EMBEDDING_MODEL=${EMBEDDING_MODEL} \
    HF_HOME=/opt/huggingface \
    HF_HUB_OFFLINE=1 \
    TRANSFORMERS_OFFLINE=1

WORKDIR /app

RUN addgroup --system appuser \
    && adduser --system --ingroup appuser appuser

RUN apt-get update \
    && apt-get install --no-install-recommends -y libgomp1 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir \
        --index-url https://download.pytorch.org/whl/cpu \
        torch \
    && pip install --no-cache-dir -r requirements.txt

RUN HF_HUB_OFFLINE=0 TRANSFORMERS_OFFLINE=0 python -c \
    "from sentence_transformers import SentenceTransformer; SentenceTransformer('${EMBEDDING_MODEL}')"

COPY app ./app
COPY run_web.py .

RUN mkdir -p \
    app/data \
    app/dataframes \
    app/keyword_index \
    app/metadata \
    app/raw_files \
    app/structured \
    app/tables \
    app/vectordb \
    && chown -R appuser:appuser /app

USER appuser

EXPOSE 8000

VOLUME ["/app/app/data", "/app/app/dataframes", "/app/app/keyword_index", "/app/app/metadata", "/app/app/raw_files", "/app/app/structured", "/app/app/tables", "/app/app/vectordb"]

HEALTHCHECK --interval=10s --timeout=5s --start-period=90s --retries=6 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/health', timeout=3)" || exit 1

CMD ["uvicorn", "app.web.api:app", "--host", "0.0.0.0", "--port", "8000"]
