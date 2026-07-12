"""Base source contracts and normalized source models."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class SourceQuery:
    query: str | None = None
    countries: list[str] = field(default_factory=list)
    domain_tags: list[str] = field(default_factory=list)


@dataclass
class SourceOpportunity:
    external_id: str
    source_name: str
    source_url: str
    official_url: str | None
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
    domain_tags: list[str] = field(default_factory=list)
    supervisor_name: str | None = None
    supervisor_profile_url: str | None = None
    funding: str | None = None
    salary_stipend: str | None = None
    duration_text: str | None = None
    start_date_text: str | None = None
    deadline_text: str | None = None
    qualification_requirements: str | None = None
    required_documents: list[str] = field(default_factory=list)
    application_process: str | None = None
    description: str | None = None
    contact_info: str | None = None
    last_seen_at: datetime | None = None


@dataclass
class SourceDescriptor:
    source_name: str
    display_name: str
    trust_level: str
    category: str
    source_type: str
    live_ready: bool
    notes: str | None = None


class OpportunitySource(ABC):
    descriptor: SourceDescriptor

    @abstractmethod
    def fetch_opportunities(self, query: SourceQuery) -> list[SourceOpportunity]:
        """Fetch normalized opportunities from the source."""

