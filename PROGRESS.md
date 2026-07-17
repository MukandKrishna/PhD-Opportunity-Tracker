# PhD Opportunity Tracker Progress

Last updated: 2026-07-17

This file records what has been built, what was fixed, what was verified, current issues, and what remains.

## MLH Code Sample Readiness Update

The repository has been prepared for a focused MLH Fellowship review:

- root documentation now describes the implemented system rather than the initial plan
- an interview-friendly Python code-review path is documented
- GitHub Actions verifies backend tests and frontend types
- link verification now has explicit `link_verification_status` and `last_verified_at` fields
- existing SQLite databases receive the new fields through an idempotent compatibility migration
- migration regression coverage brings the backend suite to 27 passing tests
- generated databases, environments, caches, and build metadata are excluded from Git
- `for_mlh_fellowship.md` contains draft application answers, evidence mapping, deployment guidance, and a remaining checklist

Public deployment and changing repository visibility to public remain separate, pending steps.

## Current Status

The project is now a working local PhD opportunity tracker with:

- FastAPI backend
- Next.js frontend
- SQLite local database
- five live source adapters
- applied-opportunity tracking
- link hygiene and source verification rules
- shared resilient scraping/fetching utilities
- rule-based NLP/keyword shortlisting for AI-related PhD opportunities
- dashboard filters for target years, intakes, and websites
- direct application/source links on every listed opportunity card

The app is usable locally for finding and tracking PhD opportunities in AI, ML, DL, RAG, agents, knowledge graphs, computer vision, data science, NLP, and computer science.

## Local Run Commands

Backend:

```powershell
cd D:\claude_mcp\PhD-Opportunity-Tracker\apps\api
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Frontend:

```powershell
cd D:\claude_mcp\PhD-Opportunity-Tracker\apps\web
npm.cmd run dev
```

Note: use `npm.cmd`, not plain `npm`, because PowerShell execution policy can block the npm shim.

## Backend Progress

The backend lives in:

- `apps/api`

Main pieces now working:

- FastAPI application
- opportunity listing API
- opportunity detail API
- applied tracking API
- ingest API
- source registry
- SQLite persistence
- CORS support for the local frontend
- direct source ingestion from five configured websites
- URL validation before records are stored or shown
- shared HTTP/Scrapling fetch fallback
- shared extraction helpers for common parsing tasks

Important files:

- `apps/api/app/main.py`
- `apps/api/app/models.py`
- `apps/api/app/routes/opportunities.py`
- `apps/api/app/routes/ingest.py`
- `apps/api/app/services/ingest.py`
- `apps/api/app/services/nlp.py`
- `apps/api/app/sources/registry.py`
- `apps/api/app/sources/fetching.py`
- `apps/api/app/sources/extraction.py`
- `apps/api/app/sources/link_validation.py`

## Scraping and Extraction Improvements

Added:

- `apps/api/app/sources/fetching.py`
- `apps/api/app/sources/extraction.py`

What this changed:

- source adapters no longer duplicate fragile HTTP/header/challenge-detection code
- normal HTTP is attempted first for speed and simplicity
- Scrapling `StealthyFetcher` is available as a fallback for blocked/challenge pages
- shared bot/challenge detection catches real challenge pages without rejecting normal pages
- shared extraction helpers now handle:
  - text cleanup
  - noisy HTML removal
  - labeled-field parsing
  - document detection
  - contact/email extraction
  - duration extraction
  - funding/stipend extraction

Important fixes:

- jobs.ac.uk normal pages include an hCaptcha script, so the challenge detector was falsely rejecting valid pages. This was fixed.
- shared cleanup was removing elements with `advert` in their class name, but jobs.ac.uk stores vacancy content in advert-like containers. This was fixed.
- Scrapling responses sometimes store usable HTML in `response.body` while `response.text` is empty. The fallback converter now handles this.

Dependency update:

- `apps/api/pyproject.toml` now includes `scrapling[fetchers]>=0.4.7`
- the local API venv has Scrapling and Playwright libraries installed

## Source Adapter Progress

### Inria

File:

- `apps/api/app/sources/inria.py`

Status:

- live-ready
- official source
- strong source quality
- official application/source links available

Live validation on 2026-06-14:

- query: `machine learning`
- result count: 15 live relevant records
- all sampled records had usable official/source links

Extracts:

- title
- institution/team
- country/city
- supervisor information where available
- salary/funding
- duration
- start date
- deadline
- requirements
- application process
- source links
- AI-related domain tags

### AcademicTransfer

File:

- `apps/api/app/sources/academictransfer.py`

Status:

- live-ready
- working source
- strong structured JSON-LD extraction
- official application links available for live records

Live validation on 2026-06-14:

- query: `machine learning`
- result count: 4 live relevant records
- usable links: 4/4
- official/application links: 4/4

This source is useful because it often has university-posted European PhD vacancies with stable metadata.

### EURAXESS

File:

- `apps/api/app/sources/euraxess.py`

Status:

- live-ready
- working source
- detail and apply links verified during testing

Live validation on 2026-06-14:

- query: `machine learning`
- result count: 1 live relevant record
- usable links: 1/1
- official/application links: 1/1

This source is useful for European doctoral and research openings.

### jobs.ac.uk

File:

- `apps/api/app/sources/jobs_ac_uk.py`

Status:

- live-ready
- parser fixed and verified
- records are now inserted into SQLite
- source appears in frontend filters with active records

Live validation on 2026-06-14:

- query: `machine learning`
- result count: 3 live relevant records
- usable links: 3/3
- official/application links: 2/3

Important fixes completed:

- added paginated search support
- increased result coverage with multiple pages
- added strict PhD filtering
- rejected non-PhD roles such as MSc, master's, postdoc, lecturer, research assistant, professor, and general jobs
- extracted structured detail-table fields
- extracted real application URLs from detail pages where visible
- kept jobs.ac.uk source URL when no university application URL is visible
- cleaned descriptions to avoid sidebar/related-job contamination
- fixed start date extraction such as `1 October 2026`
- fixed false challenge detection caused by normal hCaptcha script tags
- fixed over-aggressive cleanup that removed jobs.ac.uk vacancy content
- added regression coverage for current jobs.ac.uk page structure

Known limitation:

- not every jobs.ac.uk detail page exposes a direct university application URL. In those cases the tracker keeps the jobs.ac.uk source page so the card still has a usable external link.

### FindAPhD

File:

- `apps/api/app/sources/findaphd.py`

Status:

- live-ready in listing-card mode
- useful for discovery
- detail-page extraction intentionally limited because FindAPhD is Cloudflare-heavy

Issue found:

- direct backend HTTP requests return `403`
- full detail-page scraping through browser/stealth mode is slow and can stall ingestion

Fix completed:

- installed Scrapling fallback dependencies
- changed FindAPhD live ingestion to listing-card extraction
- extracts real FindAPhD project URLs from live search results
- avoids fetching every project detail page during normal ingest
- marks FindAPhD records as aggregator-verified source links, not official university application links

Live validation on 2026-06-14:

- query: `machine learning`
- result count: 14 live relevant records
- usable links: 14/14
- official/application links: 0/14

Known limitation:

- FindAPhD currently provides real project/source links, not final university application links. A future slow/deep verification workflow can visit selected project detail pages and try to extract official university links.

## Link Validation and Source Trust

Added/updated:

- `apps/api/app/sources/link_validation.py`
- `apps/web/lib/links.ts`

What was fixed:

- demo links like `university.example` and fake FindAPhD URLs are no longer treated as real links
- optional official/supervisor links are nulled if invalid
- frontend hides placeholder, test, example, and demo URLs
- backend skips records with no usable `official_url` and no usable `source_url`
- frontend cards now show a direct external button:
  - `Application page` when an official/application URL exists
  - `Source page` when only an aggregator/source URL exists
- detail pages also show the best external action link in applicant actions

Why this matters:

- every listed opportunity must lead somewhere real
- broken placeholder links damage trust
- aggregator links and official application links are handled separately
- source-only records are still useful when the source page is the best available verified link

## NLP / Keyword Shortlisting

Added:

- `apps/api/app/services/nlp.py`

This is not an AI model yet. It is a lightweight rule-based NLP/regex classifier.

It checks title, description, requirements, and application text for target themes such as:

- RAG
- Agents
- Multi-Agent
- Knowledge Graphs
- Artificial Intelligence
- Machine Learning
- Deep Learning
- Computer Vision
- Data Science
- NLP
- Computer Science

All source adapters use the shared classifier so tags are consistent across sources.

Future improvement:

- add optional model-based relevance scoring after extraction and link validation are stable
- score opportunities against a personal research profile

## Frontend Progress

The frontend lives in:

- `apps/web`

Pages:

- `apps/web/app/page.tsx`
- `apps/web/app/applied/page.tsx`
- `apps/web/app/opportunity/[id]/page.tsx`

Important components:

- `apps/web/components/opportunity-filter-board.tsx`
- `apps/web/components/opportunity-card.tsx`
- `apps/web/components/apply-toggle.tsx`

What is now working:

- filter board for year, intake, and website
- counts on the top-right of each filter button
- adaptive list filtering based on selected year/intake/source
- source filter supports all registered sources
- opportunity cards show direct external application/source links
- opportunity detail pages show direct external application/source links
- applied workflow remains available
- the old `Source coverage` card/section was removed from the home page

Target intake filters:

- `2026 Fall` for September/October 2026
- `2027 Spring` for January/February/March 2027
- `2027 Summer` for June/July 2027
- `2027 Fall` for September/October 2027

Website filters currently support:

- AcademicTransfer
- EURAXESS
- FindAPhD
- Inria
- jobs.ac.uk

## Live Ingestion Result

On 2026-06-14, all five configured sources were ingested using:

- query: `machine learning`
- domain tags:
  - RAG
  - Agents
  - Multi-Agent
  - Knowledge Graphs
  - AI
  - ML
  - DL
  - Computer Vision
  - Data Science

Ingestion result:

```text
inserted_count: 30
updated_count: 7
skipped_count: 0
errors: []
```

SQLite active counts after ingest:

```text
AcademicTransfer: 6
EURAXESS: 3
FindAPhD: 15
Inria: 16
jobs.ac.uk: 3
```

Official/application link counts among active rows:

```text
AcademicTransfer: 5 / 6
EURAXESS: 3 / 3
FindAPhD: 0 / 15
Inria: 15 / 16
jobs.ac.uk: 2 / 3
```

Important interpretation:

- all active rows have at least one usable external source/application link
- FindAPhD records currently use real FindAPhD project links as source links
- FindAPhD official university application links require a future deep-detail verification workflow

## Runtime and Build Fixes

### Frontend font issue

Problem:

- Next.js build was failing because `next/font/google` required network access.

Fix:

- removed Google font dependency
- added local/system font CSS variables in `globals.css`

### CSS import issue

Problem:

- the editor reported: `Cannot find module or type declarations for side-effect import of './globals.css'`.

Fix/status:

- this is a TypeScript/editor declaration issue, not a runtime CSS failure
- the app type check and prior build checks passed after cleanup

## Verification Done

Backend tests:

```powershell
cd D:\claude_mcp\PhD-Opportunity-Tracker\apps\api
.\.venv\Scripts\python.exe -m pytest tests
```

Latest result:

- `26 passed`

Frontend type check:

```powershell
cd D:\claude_mcp\PhD-Opportunity-Tracker\apps\web
.\node_modules\.bin\tsc.cmd --noEmit
```

Latest result:

- passed

Live source validation:

- AcademicTransfer: working
- EURAXESS: working
- FindAPhD: working in listing-card mode
- Inria: working
- jobs.ac.uk: working

## Known Issues

### 1. FindAPhD official application links are not extracted yet

FindAPhD is Cloudflare-heavy. Listing pages can now be extracted through Scrapling fallback, but detail-page extraction is slow and should not run for every listing during normal ingest.

Next action:

- add a separate "deep verify selected FindAPhD records" workflow
- run it only for saved/interesting records
- attempt to extract official university application links from those detail pages

### 2. Some aggregator records only expose source links

Some jobs.ac.uk and FindAPhD records do not expose a direct official university application URL from the listing/detail text currently parsed.

Next action:

- keep showing the source link
- later run per-record deep link verification
- add `last_verified_at` and `link_verified_status` fields

### 3. No AI model is used yet

Current NLP is rule-based, not model-based.

Next action:

- add optional AI relevance scoring later
- only score records after extraction and link validation are solid

### 4. Data quality still needs source-by-source review

Even with better parsers, each source needs manual spot checks for:

- deadline correctness
- start date/intake mapping
- funding/stipend extraction
- supervisor extraction
- required documents
- real application URL

## Remaining Work

Highest priority:

1. Add `last_verified_at` and source-link verification fields.
2. Add a stale-link checker.
3. Add a slow/deep verification job for selected FindAPhD records.
4. Add search by keyword/domain in the frontend.
5. Add export to CSV.
6. Add notes/status fields beyond applied/not applied.
7. Add reminders for deadlines.

Next source work:

1. Add Jobbnorge.
2. Add Academic Positions.
3. Add DAAD where useful.
4. Add more official university/institute sources.
5. Improve official-link extraction for jobs.ac.uk records that currently only expose source links.

Possible AI/NLP improvements:

1. Add model-based relevance scoring.
2. Score opportunities against a personal research profile.
3. Extract supervisor names and emails more reliably.
4. Summarize each opportunity into a short applicant-friendly brief.
5. Detect whether the position is truly PhD/doctoral, not just research-related.

## Short Summary

The tracker has moved from scaffold/demo stage into a usable local PhD opportunity application.

The strongest progress is:

- five live source adapters
- real live ingestion into SQLite
- direct links on opportunity cards
- link validation before display
- shared resilient fetch/extraction utilities
- Scrapling fallback for blocked sources
- FindAPhD listing-card extraction
- jobs.ac.uk parser fixes
- rule-based NLP shortlisting
- year/intake/website filters
- working backend tests
- frontend type check passing

The next major step is to add deep verification and `last verified` metadata so the tracker can distinguish:

- direct official application page
- verified aggregator/source page
- discovered but not yet deep-verified opportunity
