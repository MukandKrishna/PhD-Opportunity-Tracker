# API App

This backend is now scaffolded around:

- FastAPI
- SQLAlchemy
- local SQLite by default for quick iteration
- source registry and parser adapters
- opportunity + applied tracking routes

## Current Capabilities

- `GET /health`
- `GET /ingest/sources`
- `POST /ingest/run`
- `POST /ingest/seed-demo`
- `GET /opportunities`
- `GET /opportunities/{id}`
- `PATCH /opportunities/{id}/apply`

## Local Run

From this folder:

```bash
uv sync
uv run python run.py
```

Then open:

- `http://127.0.0.1:8000/docs`

## Current Source Status

Registered source adapters:

- `inria`
- `jobs_ac_uk`
- `findaphd`

They are registered and URL-ready, but live parsing is not enabled yet. The current scaffold includes a demo seed endpoint so we can build the web UI before the live scrapers are finished.

## Next Backend Work

- implement first real HTML fetch + parse flow
- add normalization for documents / deadlines / funding
- add source verification pipeline
- connect to Supabase when we want hosted persistence
