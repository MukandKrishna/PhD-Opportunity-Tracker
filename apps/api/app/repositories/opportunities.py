"""Repository helpers for opportunities and user tracking."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Select, select
from sqlalchemy.orm import Session, selectinload

from app.models import Opportunity, OpportunityTracking
from app.sources.base import SourceOpportunity
from app.sources.link_validation import clean_optional_url, is_usable_external_url


def _base_query(user_key: str) -> Select[tuple[Opportunity]]:
    return (
        select(Opportunity)
        .options(selectinload(Opportunity.tracking_entries))
        .where(True)
    )


def list_opportunities(
    db: Session,
    *,
    user_key: str,
    applied: bool | None = None,
    status: str | None = "active",
    country: str | None = None,
    domain_primary: str | None = None,
    verification_status: str | None = None,
) -> list[Opportunity]:
    query = _base_query(user_key)

    if status:
        query = query.where(Opportunity.status == status)
    if country:
        query = query.where(Opportunity.country == country)
    if domain_primary:
        query = query.where(Opportunity.domain_primary == domain_primary)
    if verification_status:
        query = query.where(Opportunity.verification_status == verification_status)

    query = query.order_by(Opportunity.deadline_text.asc().nulls_last(), Opportunity.created_at.desc())
    opportunities = list(db.scalars(query).all())
    opportunities = [
        opportunity
        for opportunity in opportunities
        if is_usable_external_url(opportunity.official_url)
        or is_usable_external_url(opportunity.source_url)
    ]

    if applied is None:
        return opportunities

    filtered: list[Opportunity] = []
    for opportunity in opportunities:
        tracking = get_tracking_for_user(opportunity, user_key)
        if bool(tracking and tracking.is_applied) == applied:
            filtered.append(opportunity)
    return filtered


def get_opportunity(db: Session, opportunity_id: int) -> Opportunity | None:
    return db.scalar(
        select(Opportunity)
        .options(selectinload(Opportunity.tracking_entries))
        .where(Opportunity.id == opportunity_id)
    )


def get_tracking_for_user(opportunity: Opportunity, user_key: str) -> OpportunityTracking | None:
    for tracking in opportunity.tracking_entries:
        if tracking.user_key == user_key:
            return tracking
    return None


def set_applied_state(
    db: Session,
    *,
    opportunity: Opportunity,
    user_key: str,
    is_applied: bool,
    notes: str | None,
    documents_ready: list[str],
) -> OpportunityTracking:
    tracking = get_tracking_for_user(opportunity, user_key)
    if tracking is None:
        tracking = OpportunityTracking(
            opportunity=opportunity,
            user_key=user_key,
        )
        db.add(tracking)

    tracking.is_applied = is_applied
    tracking.applied_at = datetime.utcnow() if is_applied else None
    tracking.notes = notes
    tracking.documents_ready = documents_ready
    tracking.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(tracking)
    return tracking


def upsert_source_opportunity(db: Session, item: SourceOpportunity) -> tuple[Opportunity, bool]:
    if not is_usable_external_url(item.official_url) and not is_usable_external_url(item.source_url):
        raise ValueError(f"Opportunity has no usable external URL: {item.source_name}:{item.external_id}")

    existing = db.scalar(
        select(Opportunity).where(
            Opportunity.source_name == item.source_name,
            Opportunity.external_id == item.external_id,
        )
    )

    if existing is None:
        existing = Opportunity(
            external_id=item.external_id,
            source_name=item.source_name,
            source_url=item.source_url,
            official_url=clean_optional_url(item.official_url),
            verification_status=item.verification_status,
            status=item.status,
            title=item.title,
            project_title=item.project_title,
            institution=item.institution,
            department=item.department,
            lab=item.lab,
            country=item.country,
            city=item.city,
            domain_primary=item.domain_primary,
            domain_tags=item.domain_tags,
            supervisor_name=item.supervisor_name,
            supervisor_profile_url=clean_optional_url(item.supervisor_profile_url),
            funding=item.funding,
            salary_stipend=item.salary_stipend,
            duration_text=item.duration_text,
            start_date_text=item.start_date_text,
            deadline_text=item.deadline_text,
            qualification_requirements=item.qualification_requirements,
            required_documents=item.required_documents,
            application_process=item.application_process,
            description=item.description,
            contact_info=item.contact_info,
            last_seen_at=item.last_seen_at or datetime.utcnow(),
        )
        db.add(existing)
        db.commit()
        db.refresh(existing)
        return existing, True

    existing.source_url = item.source_url
    existing.official_url = clean_optional_url(item.official_url)
    existing.verification_status = item.verification_status
    existing.status = item.status
    existing.title = item.title
    existing.project_title = item.project_title
    existing.institution = item.institution
    existing.department = item.department
    existing.lab = item.lab
    existing.country = item.country
    existing.city = item.city
    existing.domain_primary = item.domain_primary
    existing.domain_tags = item.domain_tags
    existing.supervisor_name = item.supervisor_name
    existing.supervisor_profile_url = clean_optional_url(item.supervisor_profile_url)
    existing.funding = item.funding
    existing.salary_stipend = item.salary_stipend
    existing.duration_text = item.duration_text
    existing.start_date_text = item.start_date_text
    existing.deadline_text = item.deadline_text
    existing.qualification_requirements = item.qualification_requirements
    existing.required_documents = item.required_documents
    existing.application_process = item.application_process
    existing.description = item.description
    existing.contact_info = item.contact_info
    existing.last_seen_at = item.last_seen_at or datetime.utcnow()
    existing.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(existing)
    return existing, False
