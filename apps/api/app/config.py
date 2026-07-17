"""Application settings."""

from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache


@dataclass(frozen=True)
class Settings:
    database_url: str
    default_user_key: str
    enable_demo_seed: bool
    cors_origins: tuple[str, ...]
    ingest_api_key: str | None
    is_render: bool


def _as_bool(value: str | None, default: bool) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _normalize_database_url(value: str) -> str:
    """Use SQLAlchemy's psycopg 3 dialect for Render-style Postgres URLs."""

    if value.startswith("postgres://"):
        return value.replace("postgres://", "postgresql+psycopg://", 1)
    if value.startswith("postgresql://"):
        return value.replace("postgresql://", "postgresql+psycopg://", 1)
    return value


def _cors_origins(value: str | None) -> tuple[str, ...]:
    origins = ["http://127.0.0.1:3000", "http://localhost:3000"]
    if value:
        origins.extend(origin.strip().rstrip("/") for origin in value.split(","))
    return tuple(dict.fromkeys(origin for origin in origins if origin))


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    ingest_api_key = os.getenv("PHD_TRACKER_INGEST_API_KEY")
    return Settings(
        database_url=_normalize_database_url(
            os.getenv("PHD_TRACKER_DATABASE_URL", "sqlite:///./phd_tracker.db")
        ),
        default_user_key=os.getenv("PHD_TRACKER_DEFAULT_USER_KEY", "local-user"),
        enable_demo_seed=_as_bool(os.getenv("PHD_TRACKER_ENABLE_DEMO_SEED"), True),
        cors_origins=_cors_origins(os.getenv("PHD_TRACKER_CORS_ORIGINS")),
        ingest_api_key=ingest_api_key.strip() if ingest_api_key else None,
        is_render=_as_bool(os.getenv("RENDER"), False),
    )
