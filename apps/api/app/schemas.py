"""Pydantic schemas for API requests and responses."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class TrackingState(BaseModel):
    user_key: str
    is_applied: bool = False
    applied_at: datetime | None = None
    notes: str | None = None
    documents_ready: list[str] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class OpportunityBase(BaseModel):
    id: int
    source_name: str
    source_url: str
    official_url: str | None = None
    verification_status: str
    status: str
    title: str
    project_title: str | None = None
    institution: str | None = None
    department: str | None = None
    lab: str | None = None
    country: str | None = None
    city: str | None = None
    domain_primary: str | None = None
    domain_tags: list[str] = Field(default_factory=list)
    supervisor_name: str | None = None
    supervisor_profile_url: str | None = None
    funding: str | None = None
    salary_stipend: str | None = None
    duration_text: str | None = None
    start_date_text: str | None = None
    deadline_text: str | None = None
    last_seen_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class OpportunitySummary(OpportunityBase):
    tracking: TrackingState | None = None


class OpportunityDetail(OpportunityBase):
    qualification_requirements: str | None = None
    required_documents: list[str] = Field(default_factory=list)
    application_process: str | None = None
    description: str | None = None
    contact_info: str | None = None
    tracking: TrackingState | None = None


class ApplyUpdate(BaseModel):
    user_key: str
    is_applied: bool = True
    notes: str | None = None
    documents_ready: list[str] = Field(default_factory=list)


class SourceDescriptor(BaseModel):
    source_name: str
    display_name: str
    trust_level: str
    category: str
    source_type: str
    live_ready: bool
    notes: str | None = None


class IngestRequest(BaseModel):
    user_key: str | None = None
    source_names: list[str] = Field(default_factory=list)
    query: str | None = None
    countries: list[str] = Field(default_factory=list)
    domain_tags: list[str] = Field(default_factory=list)


class IngestResult(BaseModel):
    requested_sources: list[str]
    inserted_count: int
    updated_count: int
    skipped_count: int
    errors: list[str] = Field(default_factory=list)
