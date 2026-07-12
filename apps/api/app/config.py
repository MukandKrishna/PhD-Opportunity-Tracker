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


def _as_bool(value: str | None, default: bool) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings(
        database_url=os.getenv("PHD_TRACKER_DATABASE_URL", "sqlite:///./phd_tracker.db"),
        default_user_key=os.getenv("PHD_TRACKER_DEFAULT_USER_KEY", "local-user"),
        enable_demo_seed=_as_bool(os.getenv("PHD_TRACKER_ENABLE_DEMO_SEED"), True),
    )
