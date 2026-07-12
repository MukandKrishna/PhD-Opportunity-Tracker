"""Source registry exports."""

from app.sources.findaphd import FindAPhDSource
from app.sources.inria import InriaSource
from app.sources.jobs_ac_uk import JobsAcUkSource
from app.sources.registry import build_source_registry

__all__ = [
    "FindAPhDSource",
    "InriaSource",
    "JobsAcUkSource",
    "build_source_registry",
]
