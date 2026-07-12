"""Opportunity routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db import get_db
from app.repositories.opportunities import (
    get_opportunity,
    get_tracking_for_user,
    list_opportunities,
    set_applied_state,
)
from app.schemas import ApplyUpdate, OpportunityDetail, OpportunitySummary, TrackingState

router = APIRouter(prefix="/opportunities", tags=["opportunities"])


def _to_tracking_state(opportunity, user_key: str) -> TrackingState | None:
    tracking = get_tracking_for_user(opportunity, user_key)
    if tracking is None:
        return None
    return TrackingState.model_validate(tracking)


@router.get("", response_model=list[OpportunitySummary])
def get_opportunities(
    user_key: str | None = Query(default=None),
    applied: bool | None = Query(default=None),
    status: str | None = Query(default="active"),
    country: str | None = Query(default=None),
    domain_primary: str | None = Query(default=None),
    verification_status: str | None = Query(default=None),
    db: Session = Depends(get_db),
) -> list[OpportunitySummary]:
    resolved_user_key = user_key or get_settings().default_user_key
    items = list_opportunities(
        db,
        user_key=resolved_user_key,
        applied=applied,
        status=status,
        country=country,
        domain_primary=domain_primary,
        verification_status=verification_status,
    )

    results: list[OpportunitySummary] = []
    for item in items:
        payload = OpportunitySummary.model_validate(item).model_dump()
        payload["tracking"] = _to_tracking_state(item, resolved_user_key)
        results.append(OpportunitySummary(**payload))
    return results


@router.get("/{opportunity_id}", response_model=OpportunityDetail)
def get_opportunity_detail(
    opportunity_id: int,
    user_key: str | None = Query(default=None),
    db: Session = Depends(get_db),
) -> OpportunityDetail:
    resolved_user_key = user_key or get_settings().default_user_key
    item = get_opportunity(db, opportunity_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Opportunity not found")

    payload = OpportunityDetail.model_validate(item).model_dump()
    payload["tracking"] = _to_tracking_state(item, resolved_user_key)
    return OpportunityDetail(**payload)


@router.patch("/{opportunity_id}/apply", response_model=OpportunityDetail)
def update_applied_state(
    opportunity_id: int,
    request: ApplyUpdate,
    db: Session = Depends(get_db),
) -> OpportunityDetail:
    item = get_opportunity(db, opportunity_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Opportunity not found")

    set_applied_state(
        db,
        opportunity=item,
        user_key=request.user_key,
        is_applied=request.is_applied,
        notes=request.notes,
        documents_ready=request.documents_ready,
    )
    refreshed = get_opportunity(db, opportunity_id)
    payload = OpportunityDetail.model_validate(refreshed).model_dump()
    payload["tracking"] = _to_tracking_state(refreshed, request.user_key)
    return OpportunityDetail(**payload)
