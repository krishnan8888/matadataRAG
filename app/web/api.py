import asyncio
import json
import os
import re
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.concurrency import run_in_threadpool
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from app.ingest.pipeline import ingest_document
from app.retrieval.answer_generator import generate_answer
from app.retrieval.context_builder import build_context
from app.retrieval.metadata_retriever import list_metadata_profiles
from app.retrieval.router import route_query
from app.settings import (
    ANSWER_MODEL,
    LOCAL_SHUTDOWN_ENABLED,
    METADATA_MODEL,
    OLLAMA_BASE_URL,
)
from app.web.shutdown import schedule_process_exit, unload_ollama_models


PROJECT_ROOT = Path(__file__).resolve().parents[2]
APP_DIR = PROJECT_ROOT / "app"
DATA_DIR = APP_DIR / "data"
METADATA_DIR = APP_DIR / "metadata"
STATIC_DIR = Path(__file__).resolve().parent / "static"

ALLOWED_SUFFIXES = {
    ".txt",
    ".md",
    ".pdf",
    ".docx",
    ".xlsx",
    ".csv",
    ".py",
    ".js",
    ".ts",
    ".java",
    ".json",
    ".yaml",
    ".yml",
    ".xml",
    ".html",
    ".css",
    ".log",
}

MAX_UPLOAD_BYTES = int(os.getenv("MAX_UPLOAD_BYTES", str(25 * 1024 * 1024)))
MODEL_LOCK = asyncio.Lock()


class QueryRequest(BaseModel):
    query: str = Field(min_length=1, max_length=4000)
    top_k_docs: int = Field(default=5, ge=1, le=20)
    top_k_results: int = Field(default=5, ge=1, le=20)


def safe_filename(filename: str) -> str:
    source = Path(filename or "upload")
    stem = re.sub(r"[^A-Za-z0-9._-]+", "_", source.stem).strip("._")
    suffix = source.suffix.lower()

    return f"{stem or 'upload'}{suffix}"


def serialize_result(result) -> dict:
    return {
        "document_id": result.document_id,
        "content": result.content,
        "source": result.source,
        "score": result.score,
        "metadata": result.metadata,
    }


def read_metadata(document_id: str) -> dict:
    metadata_path = METADATA_DIR / f"{document_id}.json"

    with open(metadata_path, "r", encoding="utf-8") as f:
        return json.load(f)


def ingest_and_describe(file_path: Path) -> dict:
    ingest_document(str(file_path))
    document_id = file_path.stem
    metadata = read_metadata(document_id)

    return {
        "document_id": document_id,
        "filename": file_path.name,
        "metadata": metadata,
    }


def query_and_answer(request: QueryRequest) -> dict:
    response = route_query(
        request.query,
        top_k_docs=request.top_k_docs,
        top_k_results=request.top_k_results,
    )
    context = build_context(response["results"])
    answer_context = build_context(
        response["results"],
        include_debug_metadata=False,
        deduplicate=True,
    )
    answer = generate_answer(request.query, answer_context)

    return {
        "query": request.query,
        "answer": answer,
        "context": context,
        "chosen_documents": response["chosen_documents"],
        "results": [
            serialize_result(result)
            for result in response["results"]
        ],
        "warnings": response["errors"],
    }


app = FastAPI(
    title="HCL Metadata-First RAG",
    version="0.1.0",
)

allowed_origins = [
    origin.strip()
    for origin in os.getenv("CORS_ORIGINS", "").split(",")
    if origin.strip()
]

if allowed_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


@app.get("/api/health")
def health() -> dict:
    return {
        "status": "ok",
        "documents": len(list_metadata_profiles()),
    }


@app.get("/api/documents")
def documents() -> dict:
    profiles = list_metadata_profiles()
    profiles.sort(key=lambda item: item.get("document_id", "").lower())

    return {
        "documents": profiles,
    }


@app.post("/api/ingest")
async def ingest(file: UploadFile = File(...)) -> dict:
    filename = safe_filename(file.filename or "")
    suffix = Path(filename).suffix.lower()

    if suffix not in ALLOWED_SUFFIXES:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {suffix or 'none'}",
        )

    content = await file.read(MAX_UPLOAD_BYTES + 1)

    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"File exceeds the {MAX_UPLOAD_BYTES // (1024 * 1024)} MB limit.",
        )

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    target = DATA_DIR / filename
    target.write_bytes(content)

    try:
        async with MODEL_LOCK:
            result = await run_in_threadpool(ingest_and_describe, target)

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Ingestion failed: {exc}",
        ) from exc

    return result


@app.post("/api/query")
async def query(request: QueryRequest) -> dict:
    try:
        async with MODEL_LOCK:
            return await run_in_threadpool(query_and_answer, request)

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Query failed: {exc}",
        ) from exc


@app.post("/api/shutdown")
async def shutdown() -> dict:
    if not LOCAL_SHUTDOWN_ENABLED:
        raise HTTPException(
            status_code=404,
            detail="Local shutdown is disabled.",
        )

    try:
        async with MODEL_LOCK:
            unloaded_models = await run_in_threadpool(
                unload_ollama_models,
                OLLAMA_BASE_URL,
                [METADATA_MODEL, ANSWER_MODEL],
            )
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Could not unload Ollama models: {exc}",
        ) from exc

    schedule_process_exit()

    return {
        "status": "shutting_down",
        "unloaded_models": unloaded_models,
    }


app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/", include_in_schema=False)
def index():
    return FileResponse(STATIC_DIR / "index.html")
