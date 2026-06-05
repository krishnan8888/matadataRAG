# Web Application

The web app serves the frontend and API from the same FastAPI process.

## Run locally

```powershell
C:\Users\krish\.conda\envs\HCL\python.exe run_web.py
```

Open `http://127.0.0.1:8000`.

## API

- `GET /api/health`
- `GET /api/documents`
- `POST /api/ingest`
- `POST /api/query`
- `GET /docs` for the generated OpenAPI interface

## Deployment notes

- Use `HOST=0.0.0.0` in a container or remote environment.
- Keep Ollama reachable from the API process or replace the model adapter later.
- Configure `OLLAMA_BASE_URL`, `METADATA_MODEL`, `ANSWER_MODEL`, and
  `EMBEDDING_MODEL` through environment variables.
- Persist the `app/data`, `app/metadata`, `app/tables`, `app/dataframes`, and
  `app/vectordb` directories.
- Set `CORS_ORIGINS` only when hosting the frontend separately from the API.
- The local model operations are serialized to prevent concurrent requests from
  competing for model resources.
