"""jobs.ac.uk source adapter."""

from __future__ import annotations

import re
from datetime import datetime, timezone
from urllib.parse import quote_plus, urlencode, urljoin

from bs4 import BeautifulSoup, Tag

from app.sources.base import OpportunitySource, SourceDescriptor, SourceOpportunity, SourceQuery
from app.sources.extraction import (
    clean_text,
    extract_contact_info,
    extract_required_documents,
    remove_noise,
)
from app.sources.fetching import FetchOptions, fetch_text
from app.sources.link_validation import clean_optional_url
from app.services.nlp import classify_domain_tags


class JobsAcUkSource(OpportunitySource):
    descriptor = SourceDescriptor(
        source_name="jobs_ac_uk",
        display_name="jobs.ac.uk",
        trust_level="official_aggregator",
        category="phd_board",
        source_type="aggregator",
        live_ready=True,
        notes="Structured PhD/studentship source with strong UK coverage. Parsing relies on jobs.ac.uk detail pages and should be monitored for selector drift.",
    )

    BASE_URL = "https://www.jobs.ac.uk"
    SEARCH_URL = "https://www.jobs.ac.uk/search/phds"
    PAGE_SIZE = 25
    MAX_PAGES = 4
    FIELD_LABELS = {
        "qualification_type": "Qualification Type",
        "location": "Location",
        "funding_for": "Funding for",
        "funding_amount": "Funding amount",
        "hours": "Hours",
        "placed_on": "Placed On",
        "closes": "Closes",
        "reference": "Reference",
    }

    def build_search_url(self, query: str | None) -> str:
        if not query:
            return self.SEARCH_URL
        return f"{self.SEARCH_URL}?keywords={quote_plus(query)}"

    def build_paginated_search_url(self, query: str | None, page: int) -> str:
        params = {
            "pageSize": str(self.PAGE_SIZE),
            "startIndex": str((page * self.PAGE_SIZE) + 1),
            "jobTypeFacet[0]": "phds",
        }
        if query:
            params["keywords"] = query
        return f"{self.SEARCH_URL}?{urlencode(params)}"

    def fetch_opportunities(self, query: SourceQuery) -> list[SourceOpportunity]:
        detail_urls: list[str] = []
        seen_urls: set[str] = set()
        for page in range(self.MAX_PAGES):
            search_html = self._fetch_text(self.build_paginated_search_url(query.query, page))
            page_urls = self._parse_listing_urls(search_html)
            new_urls = [url for url in page_urls if url not in seen_urls]
            if not new_urls:
                break
            detail_urls.extend(new_urls)
            seen_urls.update(new_urls)

        results: list[SourceOpportunity] = []

        for detail_url in detail_urls:
            detail_html = self._fetch_text(detail_url)
            item = self._parse_detail(detail_url, detail_html)
            if item is None:
                continue
            if not self._matches_scope(item, query):
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
            if "/job/" not in href:
                continue
            if not title or not self._looks_like_phd_title(title):
                continue
            if self._is_excluded_title(title):
                continue

            absolute_url = urljoin(self.BASE_URL, href)
            if absolute_url in seen:
                continue

            seen.add(absolute_url)
            urls.append(absolute_url)

        return urls

    def _parse_detail(self, detail_url: str, html: str) -> SourceOpportunity | None:
        soup = BeautifulSoup(html, "lxml")
        self._remove_noise(soup)

        title = self._get_heading_text(soup, "h1")
        if not title or not self._looks_like_phd_title(title):
            return None
        if self._is_excluded_title(title):
            return None

        fields = self._extract_detail_table_fields(soup)
        institution = self._extract_institution(soup)
        qualification_type = fields.get(self.FIELD_LABELS["qualification_type"])
        if qualification_type and "phd" not in qualification_type.lower():
            return None

        location = fields.get(self.FIELD_LABELS["location"])
        funding_for = fields.get(self.FIELD_LABELS["funding_for"])
        funding_amount = fields.get(self.FIELD_LABELS["funding_amount"])
        hours = fields.get(self.FIELD_LABELS["hours"])
        closes = fields.get(self.FIELD_LABELS["closes"])
        reference = fields.get(self.FIELD_LABELS["reference"]) or self._extract_reference_from_url(detail_url)

        description = self._extract_description(soup, title, institution)
        qualification_requirements = self._extract_qualification_requirements(description)
        required_documents = self._extract_required_documents(description)
        supervisor_name = self._extract_supervisor_name(description)
        start_date = self._extract_inline_value(description, ["Start Date", "Start date"])
        duration = self._extract_inline_value(description, ["Course length (full time)", "Duration"])
        application_url = self._extract_application_url(soup, detail_url)

        domain_tags = classify_domain_tags(title, description, qualification_requirements)

        if not domain_tags:
            return None

        country, city = self._split_location(location)
        return SourceOpportunity(
            external_id=reference or detail_url,
            source_name=self.descriptor.source_name,
            source_url=detail_url,
            official_url=application_url,
            verification_status="aggregator_verified",
            status=self._derive_status(closes),
            title=title,
            project_title=self._clean_project_title(title),
            institution=institution,
            department=None,
            lab=None,
            country=country,
            city=city,
            domain_primary=domain_tags[0] if domain_tags else None,
            domain_tags=domain_tags,
            supervisor_name=supervisor_name,
            supervisor_profile_url=None,
            funding=", ".join(part for part in [funding_for, funding_amount] if part) or None,
            salary_stipend=funding_amount,
            duration_text=duration or hours,
            start_date_text=start_date,
            deadline_text=closes,
            qualification_requirements=qualification_requirements,
            required_documents=required_documents,
            application_process=self._extract_application_process(description),
            description=description,
            contact_info=self._extract_contact_info(description),
            last_seen_at=datetime.now(timezone.utc),
        )

    def _extract_description(self, soup: BeautifulSoup, title: str, institution: str | None) -> str:
        root = (
            soup.select_one(".j-advert__body")
            or soup.select_one(".j-advert-details")
            or soup.find("main")
            or soup.body
            or soup
        )
        text = root.get_text("\n", strip=True)
        lines = [self._clean_text(line) for line in text.splitlines() if self._clean_text(line)]

        blocked_prefixes = (
            "Back to search results",
            "Qualification Type:",
            "Location:",
            "Funding for:",
            "Funding amount:",
            "Hours:",
            "Placed On:",
            "Closes:",
            "Reference:",
            "Manage your job alerts",
            "Show all PhDs",
        )
        trimmed = []
        for line in lines:
            if line == title or (institution and line == institution):
                continue
            if line.startswith(blocked_prefixes):
                continue
            if "/job/" in line or "jobs.ac.uk" in line:
                continue
            trimmed.append(line)

        description = "\n".join(trimmed).strip()
        stop_markers = [
            "\nLocation(s):",
            "\nShow all PhDs",
            "\nManage your job alerts",
            "\nSimilar PhDs",
            "\nRelated PhDs",
            "\nTerms and Conditions",
        ]
        for marker in stop_markers:
            if marker in description:
                description = description.split(marker, 1)[0].strip()
        return description

    def _extract_qualification_requirements(self, description: str) -> str | None:
        markers = [
            "Entry Requirements:",
            "Entry requirements:",
            "Essential Criteria:",
            "Essential criteria:",
            "Applicants should have",
            "Applicants must have",
        ]

        extracted = []
        for marker in markers:
            if marker in description:
                part = description.split(marker, 1)[1].strip()
                extracted.append(part[:800].strip())
        if extracted:
            return "\n\n".join(extracted)
        return None

    def _extract_required_documents(self, text: str) -> list[str]:
        return extract_required_documents(text)

    def _extract_supervisor_name(self, text: str) -> str | None:
        patterns = [
            r"Director of Studies:\s*(.+)",
            r"Supervisors:\s*(.+)",
            r"Supervisor:\s*(.+)",
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return self._clean_text(match.group(1))
        return None

    def _extract_application_process(self, text: str) -> str | None:
        markers = [
            "How to apply:",
            "Application deadline:",
            "To apply",
            "Apply now",
        ]
        matches = []
        for marker in markers:
            if marker in text:
                matches.append(text.split(marker, 1)[1][:400].strip())
        return "\n\n".join(matches) if matches else None

    def _extract_contact_info(self, text: str) -> str | None:
        return extract_contact_info(text)

    def _extract_inline_value(self, text: str, labels: list[str]) -> str | None:
        lines = [self._clean_text(line) for line in text.splitlines() if self._clean_text(line)]
        normalized_labels = [label.lower() for label in labels]
        for index, line in enumerate(lines):
            lowered = line.lower()
            for label in normalized_labels:
                if lowered == f"{label}:" or lowered == label:
                    if index + 1 < len(lines):
                        return self._clean_text(lines[index + 1])
                if lowered.startswith(f"{label}:"):
                    value = self._clean_text(line.split(":", 1)[1])
                    if value == "1" and index + 1 < len(lines):
                        next_line = self._clean_text(lines[index + 1])
                        if re.search(r"\b(january|february|march|april|may|june|july|august|september|october|november|december|jan|feb|mar|apr|jun|jul|aug|sep|sept|oct|nov|dec)\b", next_line, re.IGNORECASE):
                            return f"{value} {next_line}"
                    if value:
                        return value
        for label in labels:
            pattern = rf"{re.escape(label)}:\s*(.+)"
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return self._clean_text(match.group(1).splitlines()[0])
        return None

    def _extract_institution(self, soup: BeautifulSoup) -> str | None:
        heading = soup.find("h3")
        if heading is not None:
            text = self._clean_text(heading.get_text(" ", strip=True))
            if text:
                return text.split(" - ")[0].strip()
        return None

    def _remove_noise(self, soup: BeautifulSoup) -> None:
        remove_noise(soup)

    def _extract_detail_table_fields(self, soup: BeautifulSoup) -> dict[str, str]:
        fields: dict[str, str] = {}
        for row in soup.find_all("tr"):
            header = row.find("th")
            value = row.find("td")
            if header is None or value is None:
                continue
            label = self._clean_text(header.get_text(" ", strip=True)).rstrip(":")
            raw_value = self._clean_text(value.get_text(" ", strip=True))
            if label and raw_value:
                fields[label] = self._clean_field_value(raw_value)
        return fields

    def _extract_application_url(self, soup: BeautifulSoup, detail_url: str) -> str | None:
        preferred_patterns = [
            r"/apply/",
            r"/postgraduate/research",
            r"/research-degrees?",
            r"/study/postgraduate",
            r"/phd",
        ]
        blocked_hosts = {
            "www.jobs.ac.uk",
            "jobs.ac.uk",
            "account.jobs.ac.uk",
            "career-advice.jobs.ac.uk",
        }
        candidates: list[str] = []

        for anchor in soup.find_all("a", href=True):
            href = urljoin(self.BASE_URL, anchor.get("href", ""))
            if href == detail_url:
                continue
            host_match = re.match(r"https?://([^/]+)", href)
            host = host_match.group(1).lower() if host_match else ""
            text = self._clean_text(anchor.get_text(" ", strip=True)).lower()
            if host in blocked_hosts:
                continue
            if not clean_optional_url(href):
                continue
            if any(re.search(pattern, href, flags=re.IGNORECASE) for pattern in preferred_patterns):
                return href
            if any(word in text for word in ["apply", "application", "postgraduate", "research"]):
                candidates.append(href)

        return candidates[0] if candidates else None

    def _extract_field(self, lines: list[str], label: str) -> str | None:
        label_lower = label.lower()
        for index, line in enumerate(lines):
            if not line.lower().startswith(label_lower):
                continue
            parts = re.split(r"\s*[:|]\s*", line, maxsplit=1)
            if len(parts) == 2 and parts[1].strip():
                return self._clean_field_value(parts[1])
            if index + 1 < len(lines):
                return self._clean_field_value(lines[index + 1])
        return None

    def _clean_field_value(self, value: str) -> str:
        return self._clean_text(value).lstrip("|").strip()

    def _extract_reference_from_url(self, url: str) -> str:
        match = re.search(r"/job/([A-Z0-9]+)", url, re.IGNORECASE)
        return match.group(1) if match else url

    def _split_location(self, location: str | None) -> tuple[str | None, str | None]:
        if not location:
            return "United Kingdom", None
        location = self._clean_text(location)
        if "," in location:
            parts = [part.strip() for part in location.split(",") if part.strip()]
            return "United Kingdom", parts[0]
        return "United Kingdom", location

    def _derive_status(self, closes: str | None) -> str:
        if not closes:
            return "active"
        parsed = self._parse_jobs_ac_uk_date(closes)
        if parsed is None:
            return "active"
        return "closed" if parsed.date() < datetime.now(timezone.utc).date() else "active"

    def _parse_jobs_ac_uk_date(self, raw: str) -> datetime | None:
        cleaned = re.sub(r"(\d+)(st|nd|rd|th)", r"\1", raw.strip(), flags=re.IGNORECASE)
        for fmt in ("%d %B %Y", "%d %b %Y"):
            try:
                return datetime.strptime(cleaned, fmt).replace(tzinfo=timezone.utc)
            except ValueError:
                continue
        return None

    def _matches_scope(self, opportunity: SourceOpportunity, query: SourceQuery) -> bool:
        haystack = " ".join(
            part
            for part in [
                opportunity.title,
                opportunity.project_title or "",
                opportunity.description or "",
                opportunity.qualification_requirements or "",
            ]
            if part
        ).lower()

        if query.domain_tags:
            requested = {item.lower() for item in query.domain_tags}
            current = {item.lower() for item in opportunity.domain_tags}
            if not requested.intersection(current):
                return False

        if query.query:
            query_words = [word for word in re.split(r"\W+", query.query.lower()) if len(word) > 2]
            if query_words and not any(word in haystack for word in query_words):
                return False

        if query.countries and opportunity.country:
            normalized = {country.lower() for country in query.countries}
            if opportunity.country.lower() not in normalized:
                return False

        return True

    def _clean_project_title(self, title: str) -> str:
        value = re.sub(r"^PhD Studentship[:\-]?\s*", "", title, flags=re.IGNORECASE)
        value = re.sub(r"^PhD Studentship in\s*", "", value, flags=re.IGNORECASE)
        value = re.sub(r"^PhD Position[:\-]?\s*", "", value, flags=re.IGNORECASE)
        return value.strip() or title

    def _looks_like_phd_title(self, title: str) -> bool:
        lowered = title.lower()
        return "phd" in lowered or "doctoral" in lowered

    def _is_excluded_title(self, title: str) -> bool:
        lowered = title.lower()
        return any(
            marker in lowered
            for marker in [
                "msc",
                "master",
                "postdoc",
                "postdoctoral",
                "post-doctoral",
                "lecturer",
                "assistant professor",
                "research associate",
                "research assistant",
            ]
        )

    def _get_heading_text(self, soup: BeautifulSoup, tag_name: str) -> str | None:
        node = soup.find(tag_name)
        if node is None:
            return None
        return self._clean_text(node.get_text(" ", strip=True)) or None

    def _clean_text(self, value: str | None) -> str:
        return clean_text(value)
