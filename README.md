# PhD Opportunity Tracker

A dedicated tracker for active PhD opportunities in AI, Computer Science, Machine Learning, Deep Learning, Agents, and RAG.

This project is separate from the job-board scraper so we can grow it into a focused product:

- scrape and verify active PhD opportunities
- normalize requirements and deadlines
- track applied opportunities
- highlight easy-to-target, high-quality sources first
- expand source coverage gradually

## Product Goal

Build a site that helps a real applicant find and manage PhD openings.

The main experience should support:

- active opportunities list
- domain and country filters
- structured details per opportunity
- official application link
- required documents list
- supervisor and lab links
- funding / stipend details
- deadline and start date
- an `Applied` workflow

## Initial Focus

We will start with sources that are:

- genuine and recent
- easy to extract consistently
- likely to expose structured fields

The first target domains are:

- AI
- CS
- ML
- DL
- Agents
- RAG

## Planned Structure

- `docs/`
  - architecture and roadmap
  - source-priority decisions
- `db/`
  - initial schema
- `apps/api/`
  - scraper + parser + enrichment + storage API
- `apps/web/`
  - frontend dashboard and applied tracker

## First Milestone

MVP:

- ingest opportunities from a small set of trusted sources
- store normalized records
- show them in a web dashboard
- mark an opportunity as applied
- show applied items in a separate page/tab

## Suggested Early Sources

Tier 1:

- FindAPhD
- jobs.ac.uk
- AcademicTransfer
- Inria Jobs
- EURAXESS
- Jobbnorge

Tier 2:

- Academic Positions
- DAAD

Tier 3 discovery-only:

- PhDScanner
- OwlIndex
- ScholarshipDB
- ApplyIndex
- ScholarshipPositions
- ScholarshipRegion

## Notes

Aggregator-only records should not be treated as fully trusted until linked back to an official university or institute page.
