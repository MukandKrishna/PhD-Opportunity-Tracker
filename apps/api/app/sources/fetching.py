"""Resilient fetch helpers for source adapters.

The default path is still plain HTTP because it is cheap, predictable, and
friendly to source sites. Scrapling is used as an optional fallback for pages
that return bot challenges, access-denied responses, or empty dynamic shells.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import httpx


DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/125.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-GB,en;q=0.9,en-US;q=0.8",
}


BOT_CHALLENGE_MARKERS = (
    "enable javascript and cookies to continue",
    "cf_chl_",
    "cf-browser-verification",
    "cloudflare ray id",
    "checking your browser",
    "please verify you are a human",
    "captcha challenge",
    "captcha verification",
    "access denied",
)


@dataclass(frozen=True)
class FetchOptions:
    source_name: str
    timeout_seconds: float = 30.0
    use_scrapling_fallback: bool = True
    headless: bool = True
    solve_cloudflare: bool = True
    network_idle: bool = True


class BrowserChallengeError(RuntimeError):
    """Raised when a page requires browser-backed collection."""


def looks_like_bot_challenge(text: str | None) -> bool:
    lowered = (text or "").lower()
    return any(marker in lowered for marker in BOT_CHALLENGE_MARKERS)


def fetch_text(url: str, *, options: FetchOptions) -> str:
    """Fetch page text with HTTP first and optional Scrapling fallback."""

    http_error: Exception | None = None
    try:
        with httpx.Client(
            timeout=options.timeout_seconds,
            follow_redirects=True,
            headers=DEFAULT_HEADERS,
        ) as client:
            response = client.get(url)
            text = response.text
            if response.status_code < 400 and text.strip() and not looks_like_bot_challenge(text):
                return text
            http_error = httpx.HTTPStatusError(
                f"{response.status_code} response for {url}",
                request=response.request,
                response=response,
            )
    except httpx.HTTPError as exc:
        http_error = exc

    if options.use_scrapling_fallback:
        scrapling_text = _fetch_with_scrapling(url, options)
        if scrapling_text and not looks_like_bot_challenge(scrapling_text):
            return scrapling_text

    if http_error is not None:
        raise http_error
    raise BrowserChallengeError(f"{options.source_name} returned a browser challenge for {url}")


def _fetch_with_scrapling(url: str, options: FetchOptions) -> str | None:
    fetcher = _load_stealthy_fetcher()
    if fetcher is None:
        return None

    try:
        response = fetcher.fetch(
            url,
            headless=options.headless,
            network_idle=options.network_idle,
            solve_cloudflare=options.solve_cloudflare,
        )
    except Exception:
        return None

    return _response_to_text(response)


def _load_stealthy_fetcher() -> Any | None:
    try:
        from scrapling import StealthyFetcher  # type: ignore

        return StealthyFetcher
    except Exception:
        pass

    try:
        from scrapling.fetchers import StealthyFetcher  # type: ignore

        return StealthyFetcher
    except Exception:
        return None


def _response_to_text(response: Any) -> str | None:
    if response is None:
        return None

    text = getattr(response, "text", None)
    if isinstance(text, str) and text.strip():
        return text

    html = getattr(response, "html", None)
    if isinstance(html, str) and html.strip():
        return html

    body = getattr(response, "body", None)
    if isinstance(body, bytes):
        return body.decode("utf-8", errors="ignore")

    return str(response) if response else None
