# Web App

This frontend is now scaffolded with:

- Next.js App Router
- TypeScript
- direct API integration with the backend

## Pages

- `/` all active opportunities
- `/applied` applied opportunities
- `/opportunity/[id]` detail page

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
