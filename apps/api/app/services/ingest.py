"""Ingestion services."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy.orm import Session

from app.repositories.opportunities import upsert_source_opportunity
from app.schemas import IngestResult
from app.sources.base import SourceOpportunity, SourceQuery
from app.sources.registry import build_source_registry


def build_demo_opportunities() -> list[SourceOpportunity]:
    now = datetime.utcnow()
    return [
        SourceOpportunity(
            external_id="demo-inria-001",
            source_name="inria",
            source_url="",
            official_url=None,
            verification_status="demo",
            status="active",
            title="PhD Position F/M Multimodal and Social Grounding of Speech Language Models",
            project_title="Multimodal and Social Grounding of Speech Language Models",
            institution="Inria",
            department="RobotLearn Team",
            country="France",
            city="Grenoble",
            domain_primary="AI",
            domain_tags=["AI", "ML", "NLP", "Agents"],
            supervisor_name="Demo Supervisor",
            supervisor_profile_url=None,
            funding="Fully funded PhD position",
            salary_stipend="Standard French doctoral salary",
            duration_text="3 years",
            start_date_text="October 2026",
            deadline_text="Rolling",
            qualification_requirements="Master's degree in CS, ML, NLP, or related field.",
            required_documents=["CV", "Cover Letter", "Transcripts"],
            application_process="Apply on the official Inria portal.",
            description="Demo seed record to support early frontend and API development.",
            contact_info="demo@inria.example",
            last_seen_at=now,
        ),
        SourceOpportunity(
            external_id="demo-academictransfer-001",
            source_name="academictransfer",
            source_url="",
            official_url=None,
            verification_status="demo",
            status="active",
            title="PhD Position on Foundation Models for Generative Design of Mechatronic Products",
            project_title="Foundation Models for Generative Design of Mechatronic Products",
            institution="TU Delft",
            department="Department of Computer Science",
            country="Netherlands",
            city="Delft",
            domain_primary="ML",
            domain_tags=["AI", "ML", "DL", "Agents"],
            supervisor_name="Demo Delft Supervisor",
            supervisor_profile_url=None,
            funding="Fully funded",
            salary_stipend="EUR 3059 - EUR 3881 / month",
            duration_text="4 years",
            start_date_text="September 2026",
            deadline_text="18 June 2026",
            qualification_requirements="Strong MSc background in CS, AI, robotics, or related field.",
            required_documents=["CV", "Motivation Letter", "Transcripts", "References"],
            application_process="Apply via the academic portal with the requested files.",
            description="Demo record reflecting the type of structured vacancy we want to capture.",
            contact_info="phd@example.org",
            last_seen_at=now,
        ),
        SourceOpportunity(
            external_id="demo-findaphd-001",
            source_name="findaphd",
            source_url="",
            official_url=None,
            verification_status="demo",
            status="active",
            title="Leverhulme Doctoral Scholarship in AI-Enabled Digital Accessibility",
            project_title="AI-Enabled Digital Accessibility",
            institution="University of Surrey",
            department="Institute for People-Centred Artificial Intelligence",
            country="United Kingdom",
            city="Surrey",
            domain_primary="AI",
            domain_tags=["AI", "RAG", "Accessibility"],
            supervisor_name="Demo Surrey Supervisor",
            supervisor_profile_url=None,
            funding="Scholarship and tuition support available",
            salary_stipend="See official funding call",
            duration_text="3 years",
            start_date_text="2026",
            deadline_text="To be confirmed",
            qualification_requirements="Relevant master's degree with strong research potential.",
            required_documents=["CV", "Cover Letter", "Research Proposal"],
            application_process="Review the university page and complete the application there.",
            description="Demo record to validate list, detail, and applied states.",
            contact_info="admissions@example.org",
            last_seen_at=now,
        ),
    ]


def seed_demo_data(db: Session) -> IngestResult:
    inserted = 0
    updated = 0
    skipped = 0

    for item in build_demo_opportunities():
        try:
            _, created = upsert_source_opportunity(db, item)
            if created:
                inserted += 1
            else:
                updated += 1
        except ValueError:
            skipped += 1

    return IngestResult(
        requested_sources=["demo_seed"],
        inserted_count=inserted,
        updated_count=updated,
        skipped_count=skipped,
        errors=[],
    )


def run_registered_sources(
    db: Session,
    *,
    source_names: list[str],
    query: str | None,
    countries: list[str],
    domain_tags: list[str],
) -> IngestResult:
    registry = build_source_registry()
    requested = source_names or list(registry.keys())

    inserted = 0
    updated = 0
    skipped = 0
    errors: list[str] = []
    source_query = SourceQuery(query=query, countries=countries, domain_tags=domain_tags)

    for source_name in requested:
        source = registry.get(source_name)
        if source is None:
            errors.append(f"Unknown source: {source_name}")
            continue

        try:
            items = source.fetch_opportunities(source_query)
        except Exception as exc:
            errors.append(f"{source_name}: {exc}")
            continue

        if not items:
            skipped += 1
            continue

        for item in items:
            try:
                _, created = upsert_source_opportunity(db, item)
                if created:
                    inserted += 1
                else:
                    updated += 1
            except ValueError as exc:
                skipped += 1
                errors.append(str(exc))

    return IngestResult(
        requested_sources=requested,
        inserted_count=inserted,
        updated_count=updated,
        skipped_count=skipped,
        errors=errors,
    )
