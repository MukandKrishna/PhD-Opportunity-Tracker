"""FindAPhD source adapter."""

from __future__ import annotations

import re
from datetime import datetime, timezone
from urllib.parse import parse_qs, quote_plus, urljoin, urlparse

from bs4 import BeautifulSoup

from app.sources.base import OpportunitySource, SourceDescriptor, SourceOpportunity, SourceQuery
from app.sources.extraction import (
    clean_text,
    extract_contact_info,
    extract_labeled_value,
    extract_required_documents,
)
from app.sources.fetching import BrowserChallengeError, FetchOptions, fetch_text, looks_like_bot_challenge
from app.sources.link_validation import clean_optional_url, is_usable_external_url
from app.services.nlp import classify_domain_tags


class FindAPhDSource(OpportunitySource):
    descriptor = SourceDescriptor(
        source_name="findaphd",
        display_name="FindAPhD",
        trust_level="phd_specialist",
        category="phd_board",
        source_type="aggregator",
        live_ready=True,
        notes="High-value PhD-specific source. Uses listing-card extraction because detail pages are Cloudflare-heavy; source project links are retained for application review.",
    )
    MAX_LISTING_ITEMS = 20

    def build_search_url(self, query: str | None) -> str:
        if not query:
            return "https://www.findaphd.com/phds/latest/"
        return f"https://www.findaphd.com/phds/?Keywords={quote_plus(query)}"

    def fetch_opportunities(self, query: SourceQuery) -> list[SourceOpportunity]:
        listing_html = self._fetch_text(self.build_search_url(query.query))
        listing_items = self._parse_listing_opportunities(listing_html)
        results: list[SourceOpportunity] = []
        for item in listing_items[: self.MAX_LISTING_ITEMS]:
            if item is None or not self._matches_scope(item, query):
                continue
            results.append(item)

        return results

    def _parse_listing_opportunities(self, html: str) -> list[SourceOpportunity]:
        soup = BeautifulSoup(html, "lxml")
        results: list[SourceOpportunity] = []
        seen: set[str] = set()

        for card in soup.select(".phd-result"):
            anchor = card.find("a", href=True)
            if anchor is None:
                continue
            href = anchor.get("href", "")
            if not self._looks_like_project_href(href):
                continue
            detail_url = urljoin("https://www.findaphd.com", href)
            if detail_url in seen:
                continue
            seen.add(detail_url)

            title = self._clean_text(
                (card.select_one("h3") or card.select_one(".h4") or anchor).get_text(" ", strip=True)
            )
            if not title or self._is_excluded_title(title):
                continue

            description = self._clean_text(
                (card.select_one(".descFrag") or card.select_one(".phd-result__description") or card).get_text(
                    " ",
                    strip=True,
                )
            )
            description = re.sub(r"\bRead more\b", "", description, flags=re.IGNORECASE).strip()
            institution = self._clean_text(
                (card.select_one(".instLink") or card.select_one(".phd-result__dept-inst--inst")).get_text(
                    " ",
                    strip=True,
                )
            ) if (card.select_one(".instLink") or card.select_one(".phd-result__dept-inst--inst")) else None
            department = self._clean_text(card.select_one(".deptLink").get_text(" ", strip=True)) if card.select_one(".deptLink") else None

            card_text = self._clean_text(card.get_text(" ", strip=True))
            script_text = "\n".join(script.get_text(" ", strip=True) for script in card.find_all("script"))
            country = self._extract_script_value(script_text, "dynamicLocationCountryName")
            city = self._extract_script_value(script_text, "dynamicLocationCityName")
            supervisor_name = self._extract_listing_supervisor(card_text)
            deadline_text = self._extract_listing_deadline(card_text)
            funding = self._extract_listing_funding(card_text)
            domain_tags = classify_domain_tags(title, description, department)
            if not domain_tags:
                continue

            results.append(
                SourceOpportunity(
                    external_id=self._extract_external_id(detail_url),
                    source_name=self.descriptor.source_name,
                    source_url=detail_url,
                    official_url=None,
                    verification_status="aggregator_verified",
                    status=self._derive_status(deadline_text),
                    title=title,
                    project_title=self._clean_project_title(title),
                    institution=institution,
                    department=department,
                    lab=None,
                    country=country or None,
                    city=city or None,
                    domain_primary=domain_tags[0],
                    domain_tags=domain_tags,
                    supervisor_name=supervisor_name,
                    supervisor_profile_url=None,
                    funding=funding,
                    salary_stipend=funding,
                    duration_text=None,
                    start_date_text=None,
                    deadline_text=deadline_text,
                    qualification_requirements=None,
                    required_documents=[],
                    application_process="Review the FindAPhD project page and follow the listed application instructions.",
                    description=description or None,
                    contact_info=None,
                    last_seen_at=datetime.now(timezone.utc),
                )
            )

        return results

    def _fetch_text(self, url: str) -> str:
        try:
            return fetch_text(url, options=FetchOptions(source_name=self.descriptor.source_name))
        except BrowserChallengeError as exc:
            raise RuntimeError(
                "FindAPhD returned a browser challenge; use browser-backed collection or an approved feed."
            ) from exc

    def _parse_listing_urls(self, html: str) -> list[str]:
        soup = BeautifulSoup(html, "lxml")
        urls: list[str] = []
        seen: set[str] = set()

        for anchor in soup.find_all("a", href=True):
            href = anchor.get("href", "")
            title = self._clean_text(anchor.get_text(" ", strip=True))
            if not title or not self._looks_like_phd_title(title):
                continue
            if not self._looks_like_project_href(href):
                continue

            absolute_url = urljoin("https://www.findaphd.com", href)
            if absolute_url in seen:
                continue
            seen.add(absolute_url)
            urls.append(absolute_url)

        return urls

    def _parse_detail(self, detail_url: str, html: str) -> SourceOpportunity | None:
        soup = BeautifulSoup(html, "lxml")
        page_text = soup.get_text("\n", strip=True)
        if self._looks_like_bot_challenge(page_text):
            return None

        lines = [self._clean_text(line) for line in page_text.splitlines() if self._clean_text(line)]
        title = self._get_heading_text(soup, "h1")
        if not title or not self._looks_like_phd_title(title):
            return None

        institution = self._extract_institution(lines)
        country, city = self._extract_location(lines)
        deadline = self._extract_labeled_value(lines, ["Application Deadline", "Closing Date", "Deadline"])
        funding = self._extract_labeled_value(lines, ["Funding", "Funding Notes", "Funding Type"])
        duration = self._extract_labeled_value(lines, ["Duration", "Programme Length"])
        supervisor_name = self._extract_labeled_value(lines, ["Supervisor", "Supervisors", "Principal Supervisor"])
        description = self._extract_description(lines, title)
        required_documents = self._extract_required_documents(description)
        domain_tags = classify_domain_tags(title, description)

        if not domain_tags:
            return None

        official_url = self._extract_official_url(soup)
        supervisor_profile_url = self._extract_supervisor_profile_url(soup)

        return SourceOpportunity(
            external_id=self._extract_external_id(detail_url),
            source_name=self.descriptor.source_name,
            source_url=detail_url,
            official_url=official_url,
            verification_status="aggregator_verified" if is_usable_external_url(detail_url) else "aggregator_unverified",
            status="active",
            title=title,
            project_title=self._clean_project_title(title),
            institution=institution,
            department=None,
            lab=None,
            country=country,
            city=city,
            domain_primary=domain_tags[0],
            domain_tags=domain_tags,
            supervisor_name=supervisor_name,
            supervisor_profile_url=supervisor_profile_url,
            funding=funding,
            salary_stipend=funding,
            duration_text=duration,
            start_date_text=self._extract_labeled_value(lines, ["Start Date", "Start date"]),
            deadline_text=deadline,
            qualification_requirements=self._extract_qualification_requirements(description),
            required_documents=required_documents,
            application_process=self._extract_application_process(description),
            description=description or None,
            contact_info=self._extract_contact_info(description),
            last_seen_at=datetime.now(timezone.utc),
        )

    def _looks_like_bot_challenge(self, text: str) -> bool:
        return looks_like_bot_challenge(text)

    def _looks_like_project_href(self, href: str) -> bool:
        lowered = href.lower()
        return (
            "/phds/project/" in lowered
            or "/phds/programme/" in lowered
            or bool(re.search(r"/phds/.+\?p\d+", lowered))
        )

    def _looks_like_phd_title(self, title: str) -> bool:
        lowered = title.lower()
        if self._is_excluded_title(title):
            return False
        return "phd" in lowered or "doctoral" in lowered or "studentship" in lowered

    def _is_excluded_title(self, title: str) -> bool:
        lowered = title.lower()
        return "postdoc" in lowered or "post-doctoral" in lowered or "postdoctoral" in lowered

    def _extract_external_id(self, detail_url: str) -> str:
        parsed = urlparse(detail_url)
        bare_project_id = re.fullmatch(r"p(\d+)", parsed.query, flags=re.IGNORECASE)
        if bare_project_id:
            return bare_project_id.group(1)
        query = parse_qs(parsed.query)
        for key in ("p", "projectid"):
            if query.get(key):
                return query[key][0]
        slug = parsed.path.rstrip("/").split("/")[-1]
        return slug or detail_url

    def _extract_institution(self, lines: list[str]) -> str | None:
        for label in ("University", "Institution", "Organisation"):
            value = self._extract_labeled_value(lines, [label])
            if value:
                return value
        for line in lines[:12]:
            if "university" in line.lower() or "institute" in line.lower():
                return line
        return None

    def _extract_location(self, lines: list[str]) -> tuple[str | None, str | None]:
        location = self._extract_labeled_value(lines, ["Location"])
        if not location:
            return None, None
        parts = [part.strip() for part in location.split(",") if part.strip()]
        if len(parts) >= 2:
            return parts[-1], parts[0]
        if parts and parts[0].lower() in {"united kingdom", "uk", "france", "germany", "netherlands"}:
            return "United Kingdom" if parts[0].lower() == "uk" else parts[0], None
        return None, parts[0] if parts else None

    def _extract_labeled_value(self, lines: list[str], labels: list[str]) -> str | None:
        return extract_labeled_value(lines, labels)

    def _extract_description(self, lines: list[str], title: str) -> str:
        start = 0
        for index, line in enumerate(lines):
            if line == title:
                start = index + 1
                break
        return "\n".join(lines[start:]).strip()

    def _extract_official_url(self, soup: BeautifulSoup) -> str | None:
        for anchor in soup.find_all("a", href=True):
            label = self._clean_text(anchor.get_text(" ", strip=True)).lower()
            href = urljoin("https://www.findaphd.com", anchor.get("href", ""))
            host = urlparse(href).netloc.lower()
            if "findaphd.com" in host:
                continue
            if any(word in label for word in ("apply", "official", "project page", "university page")):
                return clean_optional_url(href)
        return None

    def _extract_supervisor_profile_url(self, soup: BeautifulSoup) -> str | None:
        for anchor in soup.find_all("a", href=True):
            label = self._clean_text(anchor.get_text(" ", strip=True)).lower()
            href = urljoin("https://www.findaphd.com", anchor.get("href", ""))
            if "supervisor" in label or "profile" in label:
                return clean_optional_url(href)
        return None

    def _extract_required_documents(self, text: str) -> list[str]:
        return extract_required_documents(text)

    def _extract_qualification_requirements(self, text: str) -> str | None:
        for marker in ("Entry requirements", "Eligibility", "Requirements"):
            match = re.search(rf"{marker}\s*[:\-]\s*(.+)", text, flags=re.IGNORECASE | re.DOTALL)
            if match:
                return self._clean_text(match.group(1)[:800])
        return None

    def _extract_application_process(self, text: str) -> str | None:
        for marker in ("How to apply", "Applications", "To apply"):
            match = re.search(rf"{marker}\s*[:\-]\s*(.+)", text, flags=re.IGNORECASE | re.DOTALL)
            if match:
                return self._clean_text(match.group(1)[:500])
        return None

    def _extract_contact_info(self, text: str) -> str | None:
        return extract_contact_info(text)

    def _derive_status(self, deadline_text: str | None) -> str:
        if not deadline_text or "year round" in deadline_text.lower():
            return "active"
        for fmt in ("%d %B %Y", "%d %b %Y", "%Y-%m-%d"):
            try:
                deadline = datetime.strptime(deadline_text, fmt).date()
                return "closed" if deadline < datetime.now(timezone.utc).date() else "active"
            except ValueError:
                continue
        return "active"

    def _extract_script_value(self, script_text: str, key: str) -> str | None:
        match = re.search(rf"{re.escape(key)}\s*=\s*\"([^\"]*)\"", script_text)
        return self._clean_text(match.group(1)) if match and match.group(1).strip() else None

    def _extract_listing_supervisor(self, text: str) -> str | None:
        match = re.search(
            r"Supervisors?:\s*(.+?)(?:\s+(?:\d{1,2}\s+\w+\s+\d{4}|Year round applications|PhD Research Project|Funded|Self-Funded)\b|$)",
            text,
            flags=re.IGNORECASE,
        )
        return self._clean_text(match.group(1)) if match else None

    def _extract_listing_deadline(self, text: str) -> str | None:
        if "Year round applications" in text:
            return "Year round applications"
        match = re.search(r"\b(\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)[a-z]*\s+\d{4})\b", text)
        return self._clean_text(match.group(1)) if match else None

    def _extract_listing_funding(self, text: str) -> str | None:
        patterns = [
            r"(Funded PhD Project \([^)]+\))",
            r"(Self-Funded PhD Students Only)",
            r"(Competition Funded PhD Project)",
        ]
        for pattern in patterns:
            match = re.search(pattern, text, flags=re.IGNORECASE)
            if match:
                return self._clean_text(match.group(1))
        return None

    def _matches_scope(self, opportunity: SourceOpportunity, query: SourceQuery) -> bool:
        if query.countries and opportunity.country:
            if opportunity.country.lower() not in {country.lower() for country in query.countries}:
                return False
        if query.domain_tags:
            requested = {item.lower() for item in query.domain_tags}
            current = {item.lower() for item in opportunity.domain_tags}
            if not requested.intersection(current):
                return False
        return True

    def _clean_project_title(self, title: str) -> str:
        return re.sub(r"^PhD Studentship[:\-]?\s*", "", title, flags=re.IGNORECASE).strip() or title

    def _get_heading_text(self, soup: BeautifulSoup, tag_name: str) -> str | None:
        node = soup.find(tag_name)
        if node is None:
            return None
        return self._clean_text(node.get_text(" ", strip=True)) or None

    def _clean_text(self, value: str | None) -> str:
        return clean_text(value)
