# PhD Opportunity Tracker API

Python backend for live source ingestion, normalization, link hygiene, topic classification, persistence, and applicant tracking.

## Capabilities

- FastAPI and typed Pydantic responses
- SQLAlchemy with local SQLite persistence
- live adapters for Inria, AcademicTransfer, EURAXESS, jobs.ac.uk, and FindAPhD
- HTTP-first fetching with challenge-aware Scrapling fallback
- shared extraction and rule-based NLP services
- URL validation and explicit source/link trust metadata
- idempotent compatibility migrations for existing SQLite databases
- partial-failure isolation during multi-source ingestion

## Run

From `apps/api`:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e . pytest
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Open `http://127.0.0.1:8000/docs` for the interactive API.

## Test

```powershell
.\.venv\Scripts\python.exe -m pytest tests
```

The tests cover all five source adapters plus fetching fallback, extraction helpers, NLP classification, and database migration behavior.

## Routes

- `GET /health`
- `GET /ingest/sources`
- `POST /ingest/run`
- `POST /ingest/seed-demo`
- `GET /opportunities`
- `GET /opportunities/{id}`
- `PATCH /opportunities/{id}/apply`

## Configuration

Copy `.env.example` to `.env` if you need to override defaults. The application supports:

- `PHD_TRACKER_DATABASE_URL`
- `PHD_TRACKER_DEFAULT_USER_KEY`
- `PHD_TRACKER_ENABLE_DEMO_SEED`
- `PHD_TRACKER_CORS_ORIGINS` (comma-separated browser origins)
- `PHD_TRACKER_INGEST_API_KEY` (sent as `X-Ingest-API-Key`)

Render-style `postgresql://` URLs are automatically normalized to SQLAlchemy's
`postgresql+psycopg://` dialect. On Render, ingestion endpoints fail closed if
`PHD_TRACKER_INGEST_API_KEY` is missing. Read and health endpoints remain public.

For a GitHub Pages frontend, configure:

```text
PHD_TRACKER_CORS_ORIGINS=https://mukandkrishna.github.io
```

The origin must not include the repository path or a trailing slash.

Local databases and environment files are intentionally excluded from Git.
