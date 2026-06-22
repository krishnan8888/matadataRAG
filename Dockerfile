FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    HOST=0.0.0.0 \
    PORT=8000 \
    OLLAMA_BASE_URL=http://model-api:11434 \
    METADATA_MODEL=qwen2.5-coder:7b \
    ANSWER_MODEL=qwen2.5-coder:7b \
    EMBEDDING_MODEL=BAAI/bge-small-en-v1.5

WORKDIR /app

RUN addgroup --system appuser \
    && adduser --system --ingroup appuser appuser

COPY requirements.txt .

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY run_web.py .

RUN mkdir -p \
    app/data \
    app/dataframes \
    app/metadata \
    app/tables \
    app/vectordb \
    && chown -R appuser:appuser /app

USER appuser

EXPOSE 8000

VOLUME ["/app/app/data", "/app/app/dataframes", "/app/app/metadata", "/app/app/tables", "/app/app/vectordb"]

CMD ["uvicorn", "app.web.api:app", "--host", "0.0.0.0", "--port", "8000"]
