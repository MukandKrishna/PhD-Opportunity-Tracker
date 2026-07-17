"""Domain values used to report link-verification state."""

from __future__ import annotations

from enum import StrEnum


class LinkVerificationStatus(StrEnum):
    """Result of actively checking an opportunity's external links."""

    NOT_CHECKED = "not_checked"
    SOURCE_VERIFIED = "source_verified"
    OFFICIAL_VERIFIED = "official_verified"
    BROKEN = "broken"
