"""EURAXESS source adapter."""

from __future__ import annotations

import re
from datetime import datetime, timezone
from urllib.parse import quote_plus, urljoin

from bs4 import BeautifulSoup, Tag

from app.sources.base import OpportunitySource, SourceDescriptor, SourceOpportunity, SourceQuery
from app.sources.extraction import (
    clean_text,
    extract_contact_info,
    extract_duration,
    extract_funding,
    extract_required_documents,
)
from app.sources.fetching import FetchOptions, fetch_text
from app.sources.link_validation import clean_optional_url
from app.services.nlp import classify_domain_tags


class EuraxessSource(OpportunitySource):
    descriptor = SourceDescriptor(
        source_name="euraxess",
        display_name="EURAXESS",
        trust_level="official_aggregator",
        category="research_jobs",
        source_type="aggregator",
        live_ready=True,
        notes="Europe-wide research opportunities source with static detail pages and visible application links.",
    )

    BASE_URL = "https://euraxess.ec.europa.eu"
    SEARCH_URL = "https://euraxess.ec.europa.eu/jobs/search"
    def build_search_url(self, query: str | None) -> str:
        if not query:
            return self.SEARCH_URL
        return f"{self.SEARCH_URL}?keywords={quote_plus(query)}"

    def fetch_opportunities(self, query: SourceQuery) -> list[SourceOpportunity]:
        listing_html = self._fetch_text(self.build_search_url(query.query))
        detail_urls = self._parse_listing_urls(listing_html)
        results: list[SourceOpportunity] = []

        for detail_url in detail_urls:
            detail_html = self._fetch_text(detail_url)
            item = self._parse_detail(detail_url, detail_html)
            if item is None or not self._matches_scope(item, query):
                continue
            results.append(item)

        return results

    def _fetch_text(self, url: str) -> str:
        return fetch_text(url, options=FetchOptions(source_name=self.descriptor.source_name))

    def _parse_listing_urls(self, html: str) -> list[str]:
        soup = BeautifulSoup(html, "lxml")
        urls: list[str] = []
        seen: set[str] = set()

        for anchor in soup.find_all("a", href=True):
            href = anchor.get("href", "")
            title = self._clean_text(anchor.get_text(" ", strip=True))
            if not re.fullmatch(r"/jobs/\d+", href):
                continue
            if not title or self._is_excluded_title(title) or not self._looks_like_doctoral_title(title):
                continue

            absolute_url = urljoin(self.BASE_URL, href)
            if absolute_url in seen:
                continue
            seen.add(absolute_url)
            urls.append(absolute_url)

        return urls

    def _parse_detail(self, detail_url: str, html: str) -> SourceOpportunity | None:
        soup = BeautifulSoup(html, "lxml")
        title = self._extract_title(soup)
        if not title or self._is_excluded_title(title) or not self._looks_like_doctoral_title(title):
            return None

        fields = self._extract_description_fields(soup)
        offer_description = self._extract_section_text(soup, "Offer Description")
        requirements = self._extract_section_text(soup, "Requirements")
        additional_info = self._extract_section_text(soup, "Additional Information")
        description = "\n\n".join(part for part in [offer_description, additional_info] if part).strip()

        domain_tags = classify_domain_tags(title, description, requirements)
        if not domain_tags:
            return None

        apply_url = self._extract_apply_url(soup) or clean_optional_url(fields.get("Website"))
        deadline_text = fields.get("Application Deadline")
        start_date_text = fields.get("Offer Starting Date")

        return SourceOpportunity(
            external_id=self._extract_external_id(detail_url),
            source_name=self.descriptor.source_name,
            source_url=detail_url,
            official_url=apply_url,
            verification_status="aggregator_verified",
            status=self._derive_status(deadline_text),
            title=title,
            project_title=self._clean_project_title(title),
            institution=fields.get("Organisation/Company") or fields.get("Company/Institute"),
            department=fields.get("Department"),
            lab=None,
            country=fields.get("Country"),
            city=fields.get("City"),
            domain_primary=domain_tags[0],
            domain_tags=domain_tags,
            supervisor_name=None,
            supervisor_profile_url=None,
            funding=self._extract_funding(description),
            salary_stipend=self._extract_funding(description),
            duration_text=self._extract_duration(description),
            start_date_text=start_date_text,
            deadline_text=deadline_text,
            qualification_requirements=requirements or None,
            required_documents=self._extract_required_documents("\n".join([description, requirements])),
            application_process=self._extract_application_process(description),
            description=description or None,
            contact_info=fields.get("E-Mail") or self._extract_contact_info(description),
            last_seen_at=datetime.now(timezone.utc),
        )

    def _extract_title(self, soup: BeautifulSoup) -> str | None:
        for heading in soup.find_all("h1"):
            text = self._clean_text(heading.get_text(" ", strip=True))
            if text and text.lower() != "job offer":
                return text
        return None

    def _extract_description_fields(self, soup: BeautifulSoup) -> dict[str, str]:
        fields: dict[str, str] = {}
        for term in soup.find_all("dt"):
            label = self._clean_text(term.get_text(" ", strip=True))
            value_node = term.find_next_sibling("dd")
            if not label or value_node is None:
                continue
            value = self._clean_text(value_node.get_text(" ", strip=True))
            if value and label not in fields:
                fields[label] = value
        return fields

    def _extract_section_text(self, soup: BeautifulSoup, section_title: str) -> str:
        heading = None
        for candidate in soup.find_all("h2"):
            if self._clean_text(candidate.get_text(" ", strip=True)).lower() == section_title.lower():
                heading = candidate
                break
        if heading is None:
            return ""

        chunks: list[str] = []
        sibling = heading.find_next_sibling()
        while sibling is not None:
            if isinstance(sibling, Tag) and sibling.name == "h2":
                break
            if isinstance(sibling, Tag):
                text = self._clean_text(sibling.get_text("\n", strip=True))
                if text:
                    chunks.append(text)
            sibling = sibling.find_next_sibling()
        return "\n".join(chunks).strip()

    def _extract_apply_url(self, soup: BeautifulSoup) -> str | None:
        for anchor in soup.find_all("a", href=True):
            text = self._clean_text(anchor.get_text(" ", strip=True)).lower()
            if "apply now" not in text:
                continue
            return clean_optional_url(urljoin(self.BASE_URL, anchor.get("href", "")))
        return None

    def _extract_external_id(self, detail_url: str) -> str:
        match = re.search(r"/jobs/(\d+)", detail_url)
        return match.group(1) if match else detail_url

    def _derive_status(self, deadline_text: str | None) -> str:
        if not deadline_text:
            return "active"
        cleaned = re.sub(r"\s+-\s+.*$", "", deadline_text.strip())
        for fmt in ("%d %b %Y", "%d %B %Y", "%Y-%m-%d"):
            try:
                deadline = datetime.strptime(cleaned, fmt).date()
                return "closed" if deadline < datetime.now(timezone.utc).date() else "active"
            except ValueError:
                continue
        return "active"

    def _looks_like_doctoral_title(self, title: str) -> bool:
        lowered = title.lower()
        return (
            "phd" in lowered
            or "doctoral" in lowered
            or "doctorate" in lowered
            or "research studentship" in lowered
            or "research fellowship" in lowered
        )

    def _is_excluded_title(self, title: str) -> bool:
        lowered = title.lower()
        return any(
            marker in lowered
            for marker in [
                "post-doctoral",
                "postdoctoral",
                "post-doc",
                "assistant professor",
                "research engineer",
            ]
        )

    def _matches_scope(self, opportunity: SourceOpportunity, query: SourceQuery) -> bool:
        if query.countries and opportunity.country:
            if opportunity.country.lower() not in {country.lower() for country in query.countries}:
                return False
        if query.domain_tags:
            requested = {item.lower() for item in query.domain_tags}
            current = {item.lower() for item in opportunity.domain_tags}
            if not requested.intersection(current):
                return False
        if query.query:
            haystack = " ".join(
                part
                for part in [opportunity.title, opportunity.description or "", opportunity.qualification_requirements or ""]
                if part
            ).lower()
            query_words = [word for word in re.split(r"\W+", query.query.lower()) if len(word) > 2]
            if query_words and not any(word in haystack for word in query_words):
                return False
        return True

    def _extract_duration(self, text: str) -> str | None:
        return extract_duration(text)

    def _extract_funding(self, text: str) -> str | None:
        return extract_funding(text)

    def _extract_required_documents(self, text: str) -> list[str]:
        return extract_required_documents(text)

    def _extract_application_process(self, text: str) -> str | None:
        if "applications are open" in text.lower():
            return self._clean_text(text[:600])
        return None

    def _extract_contact_info(self, text: str) -> str | None:
        return extract_contact_info(text)

    def _clean_project_title(self, title: str) -> str:
        return re.sub(r"^PhD\s*[-:]?\s*", "", title, flags=re.IGNORECASE).strip() or title

    def _clean_text(self, value: str | None) -> str:
        return clean_text(value)
