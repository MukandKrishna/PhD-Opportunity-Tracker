"""Lightweight NLP helpers for opportunity shortlisting."""

from __future__ import annotations

import re
import unicodedata


TARGET_DOMAIN_PATTERNS: dict[str, list[str]] = {
    "RAG": [
        r"\brag\b",
        r"\bretrieval[\s-]+augmented(?:\s+generation)?\b",
        r"\bretrieval\s+augmented\b",
        r"\bvector\s+(?:search|database|retrieval)\b",
        r"\bsemantic\s+retrieval\b",
    ],
    "Agents": [
        r"\bagentic\b",
        r"\bagents?\b",
        r"\bautonomous\s+agents?\b",
        r"\bintelligent\s+agents?\b",
        r"\bplanning\s+agents?\b",
        r"\breasoning\s+agents?\b",
    ],
    "Multi-Agent": [
        r"\bmulti[\s-]+agents?\b",
        r"\bmultiagent\b",
        r"\bmulti[\s-]+agent\s+systems?\b",
        r"\bagent\s+societ(?:y|ies)\b",
        r"\bcooperative\s+agents?\b",
    ],
    "Knowledge Graphs": [
        r"\bknowledge\s+graphs?\b",
        r"\bknowledge\s+representation\b",
        r"\bsemantic\s+web\b",
        r"\bontolog(?:y|ies)\b",
        r"\bgraph\s+reasoning\b",
    ],
    "AI": [
        r"\bartificial\s+intelligence\b",
        r"\bgenerative\s+ai\b",
        r"\bai\b",
        r"\bfoundation\s+models?\b",
        r"\bllms?\b",
        r"\blarge\s+language\s+models?\b",
    ],
    "ML": [
        r"\bmachine\s+learning\b",
        r"\bstatistical\s+learning\b",
        r"\blearning\s+models?\b",
        r"\bscientific\s+machine\s+learning\b",
        r"\bself[\s-]+supervised\s+learning\b",
        r"\bsupervised\s+learning\b",
        r"\bunsupervised\s+learning\b",
    ],
    "DL": [
        r"\bdeep\s+learning\b",
        r"\bneural\s+networks?\b",
        r"\bdeep\s+neural\s+networks?\b",
        r"\bfew[\s-]+shot\s+learning\b",
        r"\btransformers?\b",
    ],
    "Computer Vision": [
        r"\bcomputer\s+vision\b",
        r"\bimage\s+(?:analysis|processing|classification|segmentation|recognition)\b",
        r"\bvisual\s+recognition\b",
        r"\bimaging\b",
        r"\bimage[\s-]+based\b",
    ],
    "Data Science": [
        r"\bdata\s+science\b",
        r"\bdata\s+analytics?\b",
        r"\bbig\s+data\b",
        r"\bdata\s+mining\b",
        r"\bstatistical\s+modelling\b",
        r"\bstatistical\s+modeling\b",
    ],
    "NLP": [
        r"\bnatural\s+language\s+processing\b",
        r"\bnlp\b",
        r"\bspeech\s+language\b",
        r"\blanguage\s+models?\b",
    ],
    "CS": [
        r"\bcomputer\s+science\b",
        r"\bcomputer\s+engineering\b",
        r"\bsoftware\b",
        r"\balgorithms?\b",
        r"\bdistributed\s+systems?\b",
        r"\bformal\s+(?:methods|verification)\b",
        r"\bcyber\s*security\b",
        r"\bcybersecurity\b",
    ],
}


def normalize_text(text: str | None) -> str:
    if not text:
        return ""
    value = unicodedata.normalize("NFKC", text)
    value = value.replace("&", " and ")
    value = re.sub(r"[_/]+", " ", value)
    value = re.sub(r"\s+", " ", value)
    return value.strip().lower()


def classify_domain_tags(*parts: str | None) -> list[str]:
    text = normalize_text(" ".join(part for part in parts if part))
    if not text:
        return []

    tags: list[str] = []
    for tag, patterns in TARGET_DOMAIN_PATTERNS.items():
        if any(re.search(pattern, text) for pattern in patterns):
            tags.append(tag)
    return tags


def is_target_opportunity(*parts: str | None) -> bool:
    return bool(classify_domain_tags(*parts))
