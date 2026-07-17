"""Authentication dependencies for administrative API operations."""

from __future__ import annotations

from secrets import compare_digest

from fastapi import Header, HTTPException, status

from app.config import get_settings


def require_ingest_api_key(
    provided_key: str | None = Header(default=None, alias="X-Ingest-API-Key"),
) -> None:
    """Protect ingestion writes while keeping local setup friction low.

    Local development remains open when no key is configured. Render fails
    closed so a forgotten environment variable cannot expose scraping jobs.
    """

    settings = get_settings()
    expected_key = settings.ingest_api_key

    if expected_key is None:
        if settings.is_render:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Ingestion is disabled until PHD_TRACKER_INGEST_API_KEY is configured.",
            )
        return

    if provided_key is None or not compare_digest(provided_key, expected_key):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="A valid X-Ingest-API-Key header is required.",
        )
