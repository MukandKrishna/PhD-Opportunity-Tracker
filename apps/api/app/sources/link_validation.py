"""Shared URL hygiene for harvested opportunity links."""

from __future__ import annotations

from urllib.parse import urlparse


EXAMPLE_HOSTS = {
    "example.com",
    "example.net",
    "example.org",
    "university.example",
}


def is_usable_external_url(value: str | None) -> bool:
    if not value:
        return False

    parsed = urlparse(value.strip())
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return False

    host = parsed.netloc.lower()
    if host.startswith("www."):
        host = host[4:]

    if host in EXAMPLE_HOSTS or host.endswith(".example"):
        return False

    path = parsed.path.lower()
    synthetic_markers = ("/demo-", "/demo_", "/test-", "/placeholder")
    return not any(marker in path for marker in synthetic_markers)


def clean_optional_url(value: str | None) -> str | None:
    return value.strip() if is_usable_external_url(value) else None
