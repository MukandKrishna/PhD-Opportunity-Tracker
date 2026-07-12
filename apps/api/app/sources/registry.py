"""Source registry construction."""

from __future__ import annotations

from app.sources.base import OpportunitySource
from app.sources.academictransfer import AcademicTransferSource
from app.sources.euraxess import EuraxessSource
from app.sources.findaphd import FindAPhDSource
from app.sources.inria import InriaSource
from app.sources.jobs_ac_uk import JobsAcUkSource


def build_source_registry() -> dict[str, OpportunitySource]:
    sources: list[OpportunitySource] = [
        InriaSource(),
        JobsAcUkSource(),
        AcademicTransferSource(),
        EuraxessSource(),
        FindAPhDSource(),
    ]
    return {source.descriptor.source_name: source for source in sources}
