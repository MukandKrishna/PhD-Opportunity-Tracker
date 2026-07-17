"""ORM models."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base
from app.verification import LinkVerificationStatus


class Opportunity(Base):
    __tablename__ = "phd_opportunities"
    __table_args__ = (
        UniqueConstraint("source_name", "external_id", name="uq_source_external_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    external_id: Mapped[str] = mapped_column(String(255))
    source_name: Mapped[str] = mapped_column(String(100), index=True)
    source_url: Mapped[str] = mapped_column(Text)
    official_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    verification_status: Mapped[str] = mapped_column(String(50), default="aggregator_unverified")
    link_verification_status: Mapped[str] = mapped_column(
        String(30),
        default=LinkVerificationStatus.NOT_CHECKED.value,
    )
    last_verified_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    status: Mapped[str] = mapped_column(String(30), default="active", index=True)

    title: Mapped[str] = mapped_column(Text)
    project_title: Mapped[str | None] = mapped_column(Text, nullable=True)
    institution: Mapped[str | None] = mapped_column(String(255), nullable=True)
    department: Mapped[str | None] = mapped_column(String(255), nullable=True)
    lab: Mapped[str | None] = mapped_column(String(255), nullable=True)
    country: Mapped[str | None] = mapped_column(String(120), nullable=True, index=True)
    city: Mapped[str | None] = mapped_column(String(120), nullable=True)

    domain_primary: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    domain_tags: Mapped[list[str]] = mapped_column(JSON, default=list)

    supervisor_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    supervisor_profile_url: Mapped[str | None] = mapped_column(Text, nullable=True)

    funding: Mapped[str | None] = mapped_column(Text, nullable=True)
    salary_stipend: Mapped[str | None] = mapped_column(Text, nullable=True)
    duration_text: Mapped[str | None] = mapped_column(String(120), nullable=True)
    start_date_text: Mapped[str | None] = mapped_column(String(120), nullable=True)
    deadline_text: Mapped[str | None] = mapped_column(String(120), nullable=True)

    qualification_requirements: Mapped[str | None] = mapped_column(Text, nullable=True)
    required_documents: Mapped[list[str]] = mapped_column(JSON, default=list)
    application_process: Mapped[str | None] = mapped_column(Text, nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    contact_info: Mapped[str | None] = mapped_column(Text, nullable=True)

    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    first_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    tracking_entries: Mapped[list["OpportunityTracking"]] = relationship(
        back_populates="opportunity",
        cascade="all, delete-orphan",
    )


class OpportunityTracking(Base):
    __tablename__ = "phd_user_tracking"
    __table_args__ = (
        UniqueConstraint("opportunity_id", "user_key", name="uq_opportunity_user"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    opportunity_id: Mapped[int] = mapped_column(ForeignKey("phd_opportunities.id", ondelete="CASCADE"))
    user_key: Mapped[str] = mapped_column(String(120), index=True)
    is_applied: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    applied_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    documents_ready: Mapped[list[str]] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    opportunity: Mapped[Opportunity] = relationship(back_populates="tracking_entries")
