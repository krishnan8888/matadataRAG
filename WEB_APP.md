# Web Applications

The production-facing MVP frontend is an ASP.NET Core Blazor Web App targeting
.NET 8. The Python FastAPI application remains the RAG API and owns ingestion,
retrieval, and answer generation.

## Run locally

Start both services in one terminal:

```powershell
.\run_app.ps1
```

Open `http://127.0.0.1:5050`.

Alternatively, start each service separately.

Start the Python RAG API:

```powershell
C:\Users\krish\.conda\envs\HCL\python.exe run_web.py
```

Start the .NET frontend in a second terminal:

```powershell
.\run_dotnet.ps1
```

## Integration boundary

- The .NET frontend calls the Python service through `IRagApiClient`.
- Configure the Python API location using `RagApi:BaseUrl` in the .NET
  application settings or the `RagApi__BaseUrl` environment variable.
- Keep the Python endpoint contract stable when integrating this Blazor app
  into the firm's main .NET website.

## Deployment notes

- Build the Python RAG API container from the repository root:

```powershell
docker build -t hcl-rag-api .
```

- Run the API with persistent host folders mounted into the container:

```powershell
docker run --rm -p 8000:8000 `
  -e OLLAMA_BASE_URL=http://model-api:11434 `
  -v ${PWD}/app/data:/app/app/data `
  -v ${PWD}/app/metadata:/app/app/metadata `
  -v ${PWD}/app/tables:/app/app/tables `
  -v ${PWD}/app/dataframes:/app/app/dataframes `
  -v ${PWD}/app/vectordb:/app/app/vectordb `
  hcl-rag-api
```

- The firm's target website runs on .NET and C#. The Blazor frontend can be
  moved or upgraded separately from the Python RAG API.
- Use `HOST=0.0.0.0` in a container or remote environment.
- Keep the configured model endpoint reachable from the API process. The
  current local placeholder is `OLLAMA_BASE_URL`; it can be replaced by a
  production model adapter later, such as an OpenAI-backed adapter.
- Configure `OLLAMA_BASE_URL`, `METADATA_MODEL`, `ANSWER_MODEL`, and
  `EMBEDDING_MODEL` through environment variables. `OLLAMA_KEEP_ALIVE`
  controls how long the local answer model remains loaded and defaults to
  `30m`.
- Persist the `app/data`, `app/metadata`, `app/tables`, `app/dataframes`, and
  `app/vectordb` directories.
- Set `CORS_ORIGINS` only when hosting the frontend separately from the API.
- The local model operations are serialized to prevent concurrent requests from
  competing for model resources.
- The local UI Exit button unloads the configured Ollama models and stops both
  application processes. It is enabled automatically only when Ollama uses a
  loopback URL; set `LOCAL_SHUTDOWN_ENABLED=false` explicitly in production.

## Table retrieval performance

- Table-row embeddings are generated during ingestion and persisted in a
  dedicated Chroma collection. Queries embed only the question and reuse the
  stored row vectors. Existing table stores are backfilled once on first use.
- Existing deployments can prefill all saved table stores with
  `python backfill_table_embeddings.py`.
