# PhD Opportunity Tracker

[![CI](https://github.com/MukandKrishna/PhD-Opportunity-Tracker/actions/workflows/ci.yml/badge.svg)](https://github.com/MukandKrishna/PhD-Opportunity-Tracker/actions/workflows/ci.yml)

A full-stack application that discovers, normalizes, verifies, and tracks active PhD opportunities in AI and computer science.

PhD vacancies are scattered across university portals and aggregators, with inconsistent fields and frequently stale links. This project turns five different sources into one searchable data model while preserving the distinction between an official application page and an aggregator listing.

> **Demo status:** the application currently runs locally. A public deployment is the next release milestone; the API requires a server runtime and cannot be hosted directly by GitHub Pages alone.

## What it does

- Ingests live vacancies from Inria, AcademicTransfer, EURAXESS, jobs.ac.uk, and FindAPhD.
- Normalizes titles, institutions, locations, deadlines, funding, supervisors, requirements, and application documents.
- Rejects placeholder links and records that have no usable external destination.
- Classifies opportunities into AI/ML topics with a shared rule-based NLP service.
- Filters opportunities by source, year, and intake in a Next.js dashboard.
- Tracks applied opportunities separately without removing them from the main list.
- Exposes a typed FastAPI API and interactive OpenAPI documentation.
- Preserves existing local data through an idempotent SQLite schema migration.

## Architecture

```mermaid
flowchart LR
    A[Five live sources] --> B[Source adapters]
    B --> C[Fetch fallback and extraction]
    C --> D[URL hygiene and NLP tagging]
    D --> E[(SQLite)]
    E --> F[FastAPI]
    F --> G[Next.js dashboard]
```

Each source adapter implements the same `OpportunitySource` contract. The ingestion service queries selected adapters, converts their output into `SourceOpportunity` objects, validates links, and upserts records using `(source_name, external_id)` as the natural identity. The UI consumes normalized API responses rather than containing source-specific logic.

## Technology

| Area            | Technology                                         |
| --------------- | -------------------------------------------------- |
| Primary backend | Python 3.11, FastAPI, SQLAlchemy, Pydantic         |
| Extraction      | HTTPX, Beautiful Soup, lxml, Scrapling fallback    |
| Frontend        | TypeScript, Next.js 15, React                      |
| Persistence     | SQLite locally; portable SQL schema included       |
| Quality         | pytest, TypeScript strict checking, GitHub Actions |

For the MLH code-sample form, the primary contribution should be listed as **Python (SWE, SRE, Web3)** because the main engineering depth is in the ingestion, parsing, normalization, validation, persistence, and API layers. TypeScript is the secondary language.

## Run locally

Prerequisites: Python 3.11+, Node.js 20+, and Git.

### 1. Start the API

```powershell
cd apps/api
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e . pytest
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

The API starts at `http://127.0.0.1:8000`; interactive docs are at `http://127.0.0.1:8000/docs`.

### 2. Start the web application

In another terminal:

```powershell
cd apps/web
Copy-Item .env.example .env.local
npm.cmd ci
npm.cmd run dev
```

Open `http://127.0.0.1:3000`.

The API seeds demo records only when the database is empty. Run live ingestion from the OpenAPI page with `POST /ingest/run` and a focused query such as `machine learning`.

## Verify the project

Backend:

```powershell
cd apps/api
.\.venv\Scripts\python.exe -m pytest tests
```

Frontend:

```powershell
cd apps/web
npm.cmd run typecheck
```

The same checks run on every push and pull request through [GitHub Actions](.github/workflows/ci.yml).

## API surface

| Method    | Route                         | Purpose                                  |
| --------- | ----------------------------- | ---------------------------------------- |
| `GET`   | `/health`                   | Runtime health check                     |
| `GET`   | `/ingest/sources`           | Registered sources and trust metadata    |
| `POST`  | `/ingest/run`               | Run selected live source adapters        |
| `GET`   | `/opportunities`            | List and filter normalized opportunities |
| `GET`   | `/opportunities/{id}`       | View complete opportunity details        |
| `PATCH` | `/opportunities/{id}/apply` | Update an applicant's tracking state     |

## Suggested code-review path

For a focused review of the Python contribution, start with:

1. [`sources/base.py`](apps/api/app/sources/base.py) — adapter contract and normalized model.
2. [`sources/fetching.py`](apps/api/app/sources/fetching.py) — HTTP-first fetching with challenge-aware fallback.
3. [`sources/jobs_ac_uk.py`](apps/api/app/sources/jobs_ac_uk.py) — a representative real-world parser.
4. [`services/ingest.py`](apps/api/app/services/ingest.py) — source orchestration and failure isolation.
5. [`repositories/opportunities.py`](apps/api/app/repositories/opportunities.py) — validation, deduplication, and persistence.
6. [`migrations.py`](apps/api/app/migrations.py) — backward-compatible local schema evolution.
7. [`tests/`](apps/api/tests) — parser, extraction, NLP, fallback, and migration regression tests.

## Engineering decisions

- **HTTP first, browser fallback:** normal requests stay fast; Scrapling is used only for blocked or challenge pages.
- **One adapter contract:** adding a source does not change the API or UI layers.
- **Trust is explicit:** `verification_status` describes source trust, while `link_verification_status` records the result of an active link check.
- **Usable links are mandatory:** records with neither a real source URL nor official URL are rejected.
- **Graceful partial failure:** one broken source is reported without discarding successful results from other sources.
- **Rule-based NLP first:** deterministic classification is easier to test; model-based ranking remains an optional later layer.

## Current limitations

- FindAPhD is Cloudflare-heavy, so normal ingestion uses listing-card data and source links rather than crawling every detail page.
- Some aggregator pages do not expose a direct university application URL.
- Link-verification metadata is stored, but the scheduled stale-link checker is not implemented yet.
- The current single-user key is intended for a personal tracker, not a multi-tenant service.
- Public deployment still needs a hosted FastAPI service and persistent database; GitHub Pages can host only a static frontend.

## Documentation

- [Architecture](docs/architecture.md)
- [Roadmap](docs/roadmap.md)
- [Source-priority rationale](docs/source-priority.md)
- [Detailed implementation progress](PROGRESS.md)
- [MLH Fellowship preparation](for_mlh_fellowship.md)

## Roadmap

1. Build the stale-link checker that updates `last_verified_at` and `link_verification_status`.
2. Add on-demand deep verification for selected FindAPhD records.
3. Add keyword search, CSV export, notes, and deadline reminders.
4. Deploy the API and database, then publish the frontend under a stable public URL.

## Author

Built and maintained by [Mukand Krishna](https://github.com/MukandKrishna).
