# Architecture

## Overview

This project should be built as a small platform, not just a scraper.

Core layers:

1. source ingestion
2. parsing + normalization
3. verification
4. storage
5. frontend tracking UI

## Backend Shape

The backend should evolve from the existing Python scraper pattern:

- source registry
- source-specific parsers
- enrichment pipeline
- deduplication
- persistence

Suggested modules:

- `apps/api/sources/`
  - one parser per source
- `apps/api/pipeline/`
  - normalization, enrichment, verification
- `apps/api/services/`
  - database and cache access
- `apps/api/domain/`
  - PhD opportunity models

## Frontend Shape

The frontend should expose:

- `All Opportunities`
- `Verified`
- `Closing Soon`
- `Applied`
- `Opportunity Detail`

Required UI behaviors:

- applied entries stay visible on the main list
- applied entries are visually green / flagged
- applied entries also appear in the `Applied` view

## Verification Strategy

Each listing should have one of:

- `official`
- `aggregator_verified`
- `aggregator_unverified`

The crawler should prefer the official page whenever available.

## Extraction Strategy

Per source, we should extract:

- title
- project title
- department / lab
- country
- city
- domain tags
- funding
- salary / stipend
- duration
- start date
- deadline
- supervisor name
- supervisor profile URL
- required degree / eligibility
- required documents
- application URL
- source URL
- official URL

## Browser Harness Role

`browser-harness` is useful for:

- exploring dynamic sites
- discovering selectors
- inspecting hidden fields
- reverse-engineering structured network requests

It should help us design parsers, but the production pipeline should still prefer direct HTTP + structured extraction where possible.
