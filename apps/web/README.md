# Web App

This frontend is now scaffolded with:

- Next.js App Router
- TypeScript
- direct API integration with the backend

## Pages

- `/` all active opportunities
- `/applied` applied opportunities
- `/opportunity?id={id}` static-compatible detail page

## Current Features

- loads opportunity cards from the API
- shows applied items as green on the main page
- keeps applied items in a separate `Applied` page
- shows source metadata and live-ready status
- supports marking or unmarking an opportunity as applied

## Environment

Copy `.env.example` to `.env.local` and set:

```bash
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000
```

## Local Run

```bash
npm install
npm run dev
```

or with your preferred package manager:

```bash
pnpm install
pnpm dev
```

## GitHub Pages

The production frontend is a static export. GitHub Actions builds it with:

```text
GITHUB_PAGES=true
NEXT_PUBLIC_API_BASE_URL=https://phd-opportunity-tracker.onrender.com
```

The exported site is written to `out/` and deployed by
`.github/workflows/deploy-pages.yml`. The browser talks to the hosted FastAPI
service; database credentials are never included in the frontend.
