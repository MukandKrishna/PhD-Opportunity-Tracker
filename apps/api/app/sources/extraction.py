"""Shared extraction helpers for PhD source adapters."""

from __future__ import annotations

import html
import re
from collections.abc import Iterable

from bs4 import BeautifulSoup, Tag


NOISE_SELECTORS = (
    "script",
    "style",
    "noscript",
    "nav",
    "footer",
    "header",
    "aside",
    "[class*='cookie']",
    "[id*='cookie']",
    "[class*='share']",
    "[class*='related']",
    "[class*='similar']",
)


DOCUMENT_PATTERNS: dict[str, tuple[str, ...]] = {
    "CV": (r"\bcv\b", r"\bcurriculum vitae\b", r"\bresume\b"),
    "Cover Letter": (r"\bcover letter\b", r"\bmotivation letter\b"),
    "Research Proposal": (r"\bresearch proposal\b", r"\bproposal\b"),
    "Transcripts": (r"\btranscript\b", r"\btranscripts\b"),
    "References": (
        r"\breferences\b",
        r"\bletters of recommendation\b",
        r"\brecommendation letters?\b",
    ),
    "Personal Statement": (r"\bpersonal statement\b",),
    "Research Statement": (r"\bresearch statement\b",),
}


def clean_text(value: str | None) -> str:
    if not value:
        return ""
    decoded = html.unescape(value)
    decoded = decoded.replace("\xa0", " ")
    return re.sub(r"\s+", " ", decoded).strip()


def html_to_lines(html_text: str) -> list[str]:
    soup = BeautifulSoup(
        html_text.replace("<br>", "\n").replace("<br/>", "\n").replace("<br />", "\n"),
        "lxml",
    )
    remove_noise(soup)
    return [clean_text(line) for line in soup.get_text("\n", strip=True).splitlines() if clean_text(line)]


def text_from_node(node: Tag | BeautifulSoup | None) -> str:
    if node is None:
        return ""
    return "\n".join(
        clean_text(line)
        for line in node.get_text("\n", strip=True).splitlines()
        if clean_text(line)
    )


def remove_noise(soup: BeautifulSoup | Tag, extra_selectors: Iterable[str] = ()) -> None:
    for selector in (*NOISE_SELECTORS, *tuple(extra_selectors)):
        for node in soup.select(selector):
            node.decompose()


def dedupe_preserve_order(values: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        cleaned = clean_text(value)
        key = cleaned.lower()
        if not cleaned or key in seen:
            continue
        seen.add(key)
        result.append(cleaned)
    return result


def extract_labeled_value(lines: list[str], labels: Iterable[str]) -> str | None:
    normalized_labels = [label.lower().rstrip(":") for label in labels]
    for index, line in enumerate(lines):
        lowered = line.lower().strip()
        for label in normalized_labels:
            if lowered == label or lowered == f"{label}:":
                if index + 1 < len(lines):
                    return clean_text(lines[index + 1]).lstrip("|").strip() or None
            if re.match(rf"^{re.escape(label)}\s*[:|]", lowered):
                value = re.split(r"\s*[:|]\s*", line, maxsplit=1)
                if len(value) == 2:
                    return clean_text(value[1]).lstrip("|").strip() or None
    return None


def extract_required_documents(text: str) -> list[str]:
    lowered = f" {text.lower()} "
    found: list[str] = []
    for label, patterns in DOCUMENT_PATTERNS.items():
        if any(re.search(pattern, lowered) for pattern in patterns):
            found.append(label)
    return found


def extract_contact_info(text: str) -> str | None:
    match = re.search(r"[\w\.-]+@[\w\.-]+\.\w+", text)
    return match.group(0) if match else None


def extract_duration(text: str) -> str | None:
    patterns = (
        r"duration:\s*([^\n.]+)",
        r"course length \(full time\):\s*([^\n.]+)",
        r"duration of\s+([^\n.]+)",
        r"(\d+\s*-?\s*year period of employment)",
        r"(\d+\s+years?)",
        r"(\d+\s+months?)",
    )
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            return clean_text(match.group(1))
    return None


def extract_funding(text: str) -> str | None:
    patterns = (
        r"funding(?: notes?| type)?:\s*([^\n.]+)",
        r"funding amount:\s*([^\n.]+)",
        r"salary:\s*([^\n.]+)",
        r"stipend:\s*([^\n.]+)",
        r"monthly maintenance allowance[:\s]+([^\n.]+)",
        r"bursary p\.a\.:\s*([^\n.]+)",
    )
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            return clean_text(match.group(1))
    return None


def extract_sections_by_headings(soup: BeautifulSoup, heading_tags: tuple[str, ...] = ("h2", "h3")) -> dict[str, str]:
    sections: dict[str, str] = {}
    for heading in soup.find_all(heading_tags):
        title = clean_text(heading.get_text(" ", strip=True))
        if not title:
            continue

        chunks: list[str] = []
        sibling = heading.find_next_sibling()
        while sibling is not None:
            if isinstance(sibling, Tag) and sibling.name in {"h1", "h2", "h3"}:
                break
            if isinstance(sibling, Tag):
                text = text_from_node(sibling)
                if text:
                    chunks.append(text)
            sibling = sibling.find_next_sibling()

        section_text = "\n".join(chunks).strip()
        if section_text:
            sections[title] = section_text
    return sections


def extraction_confidence(fields: dict[str, object | None], *, rich_text: str | None = None) -> float:
    meaningful = sum(1 for value in fields.values() if value not in (None, "", []))
    score = 0.35 + min(meaningful * 0.045, 0.45)
    if rich_text and len(rich_text.split()) >= 120:
        score += 0.1
    if fields.get("official_url"):
        score += 0.1
    return round(min(score, 1.0), 2)
