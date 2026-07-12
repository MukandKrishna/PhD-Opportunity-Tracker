"""Ingestion and source metadata routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db import get_db
from app.schemas import IngestRequest, IngestResult, SourceDescriptor
from app.services.ingest import run_registered_sources, seed_demo_data
from app.sources.registry import build_source_registry

router = APIRouter(prefix="/ingest", tags=["ingest"])


@router.get("/sources", response_model=list[SourceDescriptor])
def list_sources() -> list[SourceDescriptor]:
    registry = build_source_registry()
    return [SourceDescriptor(**source.descriptor.__dict__) for source in registry.values()]


@router.post("/run", response_model=IngestResult)
def run_ingest(request: IngestRequest, db: Session = Depends(get_db)) -> IngestResult:
    return run_registered_sources(
        db,
        source_names=request.source_names,
        query=request.query,
        countries=request.countries,
        domain_tags=request.domain_tags,
    )


@router.post("/seed-demo", response_model=IngestResult)
def seed_demo(db: Session = Depends(get_db)) -> IngestResult:
    return seed_demo_data(db)


@router.post("/bootstrap-demo", response_model=IngestResult)
def bootstrap_demo_if_enabled(db: Session = Depends(get_db)) -> IngestResult:
    settings = get_settings()
    if not settings.enable_demo_seed:
        return IngestResult(
            requested_sources=["demo_seed"],
            inserted_count=0,
            updated_count=0,
            skipped_count=1,
            errors=["Demo seed is disabled by configuration."],
        )
    return seed_demo_data(db)
