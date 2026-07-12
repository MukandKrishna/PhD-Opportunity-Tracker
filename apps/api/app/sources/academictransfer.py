"""AcademicTransfer source adapter."""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from urllib.parse import quote_plus, urljoin

from bs4 import BeautifulSoup

from app.sources.base import OpportunitySource, SourceDescriptor, SourceOpportunity, SourceQuery
from app.sources.extraction import (
    clean_text,
    extract_contact_info,
    extract_duration,
    extract_required_documents,
    html_to_lines,
)
from app.sources.fetching import FetchOptions, fetch_text
from app.sources.link_validation import clean_optional_url
from app.services.nlp import classify_domain_tags


class AcademicTransferSource(OpportunitySource):
    descriptor = SourceDescriptor(
        source_name="academictransfer",
        display_name="AcademicTransfer",
        trust_level="official_aggregator",
        category="phd_board",
        source_type="aggregator",
        live_ready=True,
        notes="Structured academic vacancy source with JSON-LD JobPosting data and visible application links.",
    )

    BASE_URL = "https://www.academictransfer.com"
    SEARCH_URL = "https://www.academictransfer.com/en/jobs/"
    COUNTRY_MAP = {
        "NL": "Netherlands",
        "BE": "Belgium",
        "DE": "Germany",
    }

    def build_search_url(self, query: str | None) -> str:
        if not query:
            return self.SEARCH_URL
        return f"{self.SEARCH_URL}?q={quote_plus(query)}"

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
            if not re.search(r"/en/jobs/\d+/", href):
                continue
            if self._is_excluded_title(href):
                continue

            absolute_url = urljoin(self.BASE_URL, href)
            if absolute_url in seen:
                continue
            seen.add(absolute_url)
            urls.append(absolute_url)

        return urls

    def _parse_detail(self, detail_url: str, html: str) -> SourceOpportunity | None:
        soup = BeautifulSoup(html, "lxml")
        job = self._extract_job_posting(soup)
        if not job:
            return None

        title = self._clean_text(str(job.get("title") or ""))
        if not title or self._is_excluded_title(title) or not self._looks_like_phd_title(title):
            return None

        description_html = str(job.get("description") or "")
        description = self._html_to_text(description_html)
        domain_tags = classify_domain_tags(title, description)
        if not domain_tags:
            return None

        location = job.get("jobLocation") or {}
        address = location.get("address") if isinstance(location, dict) else {}
        address = address if isinstance(address, dict) else {}
        country_code = str(address.get("addressCountry") or "").strip()
        country = self.COUNTRY_MAP.get(country_code.upper(), country_code or None)
        city = self._clean_text(str(address.get("addressLocality") or "")) or None

        organization = job.get("hiringOrganization") or {}
        institution = None
        if isinstance(organization, dict):
            institution = self._clean_text(str(organization.get("name") or "")) or None

        identifier = job.get("identifier") or {}
        external_id = detail_url
        if isinstance(identifier, dict) and identifier.get("value"):
            external_id = str(identifier["value"])

        apply_url = self._extract_apply_url(soup)
        salary = self._format_salary(job.get("baseSalary"))
        deadline_text = self._format_date(str(job.get("validThrough") or ""))

        return SourceOpportunity(
            external_id=external_id,
            source_name=self.descriptor.source_name,
            source_url=detail_url,
            official_url=apply_url,
            verification_status="aggregator_verified",
            status=self._derive_status(deadline_text),
            title=title,
            project_title=self._clean_project_title(title),
            institution=institution,
            department=self._extract_department(description),
            lab=None,
            country=country,
            city=city,
            domain_primary=domain_tags[0],
            domain_tags=domain_tags,
            supervisor_name=self._extract_supervisor_name(description),
            supervisor_profile_url=None,
            funding=salary,
            salary_stipend=salary,
            duration_text=self._extract_duration(description),
            start_date_text=self._extract_start_date(description),
            deadline_text=deadline_text,
            qualification_requirements=self._extract_qualification_requirements(description),
            required_documents=self._extract_required_documents(description),
            application_process=self._extract_application_process(description),
            description=description or None,
            contact_info=self._extract_contact_info(description),
            last_seen_at=datetime.now(timezone.utc),
        )

    def _extract_job_posting(self, soup: BeautifulSoup) -> dict[str, object] | None:
        for script in soup.find_all("script", type="application/ld+json"):
            try:
                data = json.loads(script.get_text(strip=True))
            except json.JSONDecodeError:
                continue
            candidates = [data]
            if isinstance(data, dict) and isinstance(data.get("mainEntity"), dict):
                candidates.append(data["mainEntity"])
            for candidate in candidates:
                if isinstance(candidate, dict) and candidate.get("@type") == "JobPosting":
                    return candidate
        return None

    def _extract_apply_url(self, soup: BeautifulSoup) -> str | None:
        for anchor in soup.find_all("a", href=True):
            text = self._clean_text(anchor.get_text(" ", strip=True)).lower()
            if "apply now" not in text:
                continue
            href = urljoin(self.BASE_URL, anchor.get("href", ""))
            return clean_optional_url(href)
        return None

    def _format_salary(self, raw: object) -> str | None:
        if not isinstance(raw, dict):
            return None
        currency = str(raw.get("currency") or "").strip()
        value = raw.get("value")
        if not isinstance(value, dict):
            return None
        minimum = value.get("minValue")
        maximum = value.get("maxValue")
        unit = str(value.get("unitText") or "").strip().lower()
        if minimum and maximum:
            suffix = f" / {unit}" if unit else ""
            return f"{currency} {minimum} - {maximum}{suffix}".strip()
        return None

    def _format_date(self, raw: str) -> str | None:
        if not raw:
            return None
        try:
            parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
            return parsed.date().isoformat()
        except ValueError:
            return raw[:10] if len(raw) >= 10 else raw

    def _derive_status(self, deadline_text: str | None) -> str:
        if not deadline_text:
            return "active"
        try:
            deadline = datetime.strptime(deadline_text, "%Y-%m-%d").date()
        except ValueError:
            return "active"
        return "closed" if deadline < datetime.now(timezone.utc).date() else "active"

    def _extract_department(self, text: str) -> str | None:
        match = re.search(r"Faculty of ([^\n.]+)", text, flags=re.IGNORECASE)
        if match:
            return f"Faculty of {self._clean_text(match.group(1))}"
        return None

    def _extract_supervisor_name(self, text: str) -> str | None:
        patterns = [
            r"contact\s+(?:dr\.?|prof\.?)?\s*([^,\n]+),\s+via",
            r"please contact\s+([^,\n]+),\s+via",
            r"supervisor[s]?:\s*([^\n]+)",
        ]
        for pattern in patterns:
            match = re.search(pattern, text, flags=re.IGNORECASE)
            if match:
                return self._clean_text(match.group(1))
        return None

    def _extract_duration(self, text: str) -> str | None:
        return extract_duration(text)

    def _extract_start_date(self, text: str) -> str | None:
        match = re.search(r"start(?:ing)? date[:\s]+([^\n.]+)", text, flags=re.IGNORECASE)
        return self._clean_text(match.group(1)) if match else None

    def _extract_qualification_requirements(self, text: str) -> str | None:
        match = re.search(
            r"Job requirements\s*(.+?)(?:TU Delft|Conditions of employment|Contract terms|We offer|Are you interested|$)",
            text,
            flags=re.IGNORECASE | re.DOTALL,
        )
        if match:
            return self._clean_text(match.group(1)[:1200])
        return None

    def _extract_application_process(self, text: str) -> str | None:
        match = re.search(
            r"(Are you interested in this vacancy\?.+?)(?:Please do not contact|Working at|$)",
            text,
            flags=re.IGNORECASE | re.DOTALL,
        )
        if match:
            return self._clean_text(match.group(1)[:800])
        if "You can apply online" in text:
            return "You can apply online. Applications sent by email or post may not be processed."
        return None

    def _extract_required_documents(self, text: str) -> list[str]:
        return extract_required_documents(text)

    def _extract_contact_info(self, text: str) -> str | None:
        return extract_contact_info(text)

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

    def _looks_like_phd_title(self, title: str) -> bool:
        lowered = title.lower()
        return "phd" in lowered or "doctoral candidate" in lowered

    def _is_excluded_title(self, title: str) -> bool:
        lowered = title.lower()
        return "postdoc" in lowered or "postdoctoral" in lowered or "post-doctoral" in lowered

    def _clean_project_title(self, title: str) -> str:
        value = re.sub(r"^PhD (Position|Candidate|Student)[:\-]?\s*", "", title, flags=re.IGNORECASE)
        return value.strip() or title

    def _html_to_text(self, html: str) -> str:
        return "\n".join(html_to_lines(html))

    def _clean_text(self, value: str | None) -> str:
        return clean_text(value)
