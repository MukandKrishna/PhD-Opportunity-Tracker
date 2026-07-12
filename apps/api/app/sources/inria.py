"""Inria source adapter."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timezone
from urllib.parse import urljoin

from bs4 import BeautifulSoup, Tag

from app.sources.base import OpportunitySource, SourceDescriptor, SourceOpportunity, SourceQuery
from app.sources.extraction import clean_text, extract_contact_info, extract_required_documents
from app.sources.fetching import FetchOptions, fetch_text
from app.services.nlp import classify_domain_tags


@dataclass
class _ListingCandidate:
    external_id: str
    title: str
    url: str


class InriaSource(OpportunitySource):
    descriptor = SourceDescriptor(
        source_name="inria",
        display_name="Inria Jobs",
        trust_level="official",
        category="official_institute",
        source_type="official",
        live_ready=True,
        notes="Official Inria job board with detailed PhD vacancy pages. Live parser enabled for targeted AI / CS / ML opportunities.",
    )

    BASE_URL = "https://jobs.inria.fr/public/classic/en/offres"
    FIELD_LABELS = {
        "contract_type": "Contract type",
        "qualification_level": "Level of qualifications required",
        "function": "Fonction",
        "theme_domain": "Theme/Domain",
        "city": "Town/city",
        "inria_center": "Inria Center",
        "starting_date": "Starting date",
        "duration_contract": "Duration of contract",
        "deadline": "Deadline to apply",
        "inria_team": "Inria Team",
        "phd_supervisor": "PhD Supervisor",
        "salary_month": "Gross Salary per month",
        "remuneration_duration": "Duration",
        "location": "Location",
    }

    def build_search_url(self) -> str:
        return self.BASE_URL

    def fetch_opportunities(self, query: SourceQuery) -> list[SourceOpportunity]:
        listing_html = self._fetch_text(self.build_search_url())
        candidates = self._parse_listing(listing_html)
        opportunities: list[SourceOpportunity] = []

        for candidate in candidates:
            detail_html = self._fetch_text(candidate.url)
            opportunity = self._parse_detail(candidate, detail_html)
            if opportunity is None:
                continue
            if not self._matches_scope(opportunity, query):
                continue
            opportunities.append(opportunity)

        return opportunities

    def _fetch_text(self, url: str) -> str:
        return fetch_text(url, options=FetchOptions(source_name=self.descriptor.source_name))

    def _parse_listing(self, html: str) -> list[_ListingCandidate]:
        soup = BeautifulSoup(html, "lxml")
        candidates: list[_ListingCandidate] = []
        seen: set[str] = set()

        for anchor in soup.find_all("a", href=True):
            href = anchor.get("href", "")
            title = self._clean_text(anchor.get_text(" ", strip=True))
            match = re.search(r"/offres/(\d{4}-\d+)", href)
            if not match or not title:
                continue
            external_id = match.group(1)
            if external_id in seen:
                continue
            if not self._is_phd_title(title):
                continue

            seen.add(external_id)
            candidates.append(
                _ListingCandidate(
                    external_id=external_id,
                    title=title,
                    url=urljoin(self.BASE_URL, href),
                )
            )

        return candidates

    def _parse_detail(self, candidate: _ListingCandidate, html: str) -> SourceOpportunity | None:
        soup = BeautifulSoup(html, "lxml")
        page_text = soup.get_text("\n", strip=True)
        lines = [self._clean_text(line) for line in page_text.splitlines() if self._clean_text(line)]
        sections = self._extract_sections(soup)

        title = self._get_heading_text(soup, "h1") or candidate.title
        context_text = sections.get("Context", {}).get("text", "")
        skills_text = sections.get("Skills", {}).get("text", "")
        objectives_text = sections.get("Research objectives", {}).get("text", "")
        assignment_text = sections.get("Assignment", {}).get("text", "")
        instruction_text = sections.get("Instruction to apply", {}).get("text", "")
        contacts_text = sections.get("Contacts", {}).get("text", "")
        remuneration_text = sections.get("Remuneration", {}).get("text", "")
        general_info_text = sections.get("General Information", {}).get("text", "")

        description = "\n\n".join(
            part
            for part in [context_text, objectives_text, assignment_text]
            if part
        ).strip()

        qualification_parts = [
            self._extract_field(lines, self.FIELD_LABELS["qualification_level"]),
            skills_text,
        ]
        qualification_requirements = "\n\n".join(part for part in qualification_parts if part).strip() or None

        supervisor_name, supervisor_profile_url = self._extract_supervisor_info(sections)
        inria_team = self._extract_field(lines, self.FIELD_LABELS["inria_team"])
        inria_center = self._extract_field(lines, self.FIELD_LABELS["inria_center"])
        city = self._extract_field(lines, self.FIELD_LABELS["city"]) or self._extract_field(lines, self.FIELD_LABELS["location"])
        duration = (
            self._extract_field(lines, self.FIELD_LABELS["duration_contract"])
            or self._extract_field(lines, self.FIELD_LABELS["remuneration_duration"])
        )
        salary_month = self._extract_field(lines, self.FIELD_LABELS["salary_month"])
        contract_type = self._extract_field(lines, self.FIELD_LABELS["contract_type"])
        deadline_text = self._extract_field(lines, self.FIELD_LABELS["deadline"])
        start_date_text = self._extract_field(lines, self.FIELD_LABELS["starting_date"])
        theme_domain = self._extract_field(lines, self.FIELD_LABELS["theme_domain"])
        required_documents = self._extract_required_documents("\n".join([instruction_text, qualification_requirements or "", description]))
        status = self._derive_status(deadline_text)
        domain_tags = classify_domain_tags(title, theme_domain, description, qualification_requirements)
        domain_primary = domain_tags[0] if domain_tags else None

        funding = ", ".join(part for part in [contract_type, salary_month] if part) or None
        project_title = self._clean_project_title(title)

        return SourceOpportunity(
            external_id=candidate.external_id,
            source_name=self.descriptor.source_name,
            source_url=candidate.url,
            official_url=candidate.url,
            verification_status="official",
            status=status,
            title=title,
            project_title=project_title,
            institution="Inria",
            department=inria_center,
            lab=inria_team,
            country="France",
            city=city,
            domain_primary=domain_primary,
            domain_tags=domain_tags,
            supervisor_name=supervisor_name,
            supervisor_profile_url=supervisor_profile_url,
            funding=funding,
            salary_stipend=salary_month or remuneration_text or None,
            duration_text=duration,
            start_date_text=start_date_text,
            deadline_text=deadline_text,
            qualification_requirements=qualification_requirements,
            required_documents=required_documents,
            application_process=instruction_text or None,
            description=description or None,
            contact_info=extract_contact_info(contacts_text) or contacts_text or None,
            last_seen_at=datetime.now(timezone.utc),
        )

    def _extract_sections(self, soup: BeautifulSoup) -> dict[str, dict[str, object]]:
        sections: dict[str, dict[str, object]] = {}
        headings = soup.find_all(["h2", "h3"])

        for heading in headings:
            title = self._clean_text(heading.get_text(" ", strip=True))
            if not title:
                continue

            texts: list[str] = []
            links: list[tuple[str, str]] = []
            sibling = heading.next_sibling

            while sibling is not None:
                if isinstance(sibling, Tag) and sibling.name in {"h1", "h2", "h3"}:
                    break
                if isinstance(sibling, Tag):
                    text = self._clean_text(sibling.get_text("\n", strip=True))
                    if text:
                        texts.append(text)
                    if sibling.name == "a" and sibling.get("href"):
                        link_text = self._clean_text(sibling.get_text(" ", strip=True))
                        links.append((link_text, sibling.get("href", "").strip()))
                    for anchor in sibling.find_all("a", href=True):
                        link_text = self._clean_text(anchor.get_text(" ", strip=True))
                        href = anchor.get("href", "").strip()
                        if href:
                            links.append((link_text, href))
                sibling = sibling.next_sibling

            sections[title] = {
                "text": "\n".join(texts).strip(),
                "links": links,
            }

        return sections

    def _extract_field(self, lines: list[str], label: str) -> str | None:
        label_lower = label.lower()
        for index, line in enumerate(lines):
            line_lower = line.lower()
            if not line_lower.startswith(label_lower):
                continue

            parts = re.split(r"\s*:\s*", line, maxsplit=1)
            if len(parts) == 2 and parts[1].strip():
                return parts[1].strip()

            if index + 1 < len(lines):
                return lines[index + 1].strip()
        return None

    def _extract_supervisor_info(self, sections: dict[str, dict[str, object]]) -> tuple[str | None, str | None]:
        contacts = sections.get("Contacts", {})
        contact_text = str(contacts.get("text", "") or "")
        contact_links = list(contacts.get("links", []) or [])

        supervisor_name = None
        lines = [self._clean_text(line) for line in contact_text.splitlines() if self._clean_text(line)]
        for index, line in enumerate(lines):
            if line.lower().startswith("phd supervisor"):
                if index + 1 < len(lines):
                    supervisor_name = lines[index + 1].split("/")[0].strip() or None
                    break

        supervisor_profile_url = None
        for link_text, href in contact_links:
            if "linkedin.com" in href or "sites.google.com" in href or "inria.fr" in href:
                supervisor_profile_url = href
                if supervisor_name is None and link_text:
                    supervisor_name = link_text.split("/")[0].strip()
                break

        return supervisor_name, supervisor_profile_url

    def _extract_required_documents(self, text: str) -> list[str]:
        return extract_required_documents(text)

    def _derive_status(self, deadline_text: str | None) -> str:
        if not deadline_text:
            return "active"
        try:
            deadline = datetime.strptime(deadline_text, "%Y-%m-%d").date()
            today = datetime.now(timezone.utc).date()
            return "closed" if deadline < today else "active"
        except ValueError:
            return "active"

    def _clean_project_title(self, title: str) -> str:
        project_title = re.sub(r"^PhD Position\s+[FM/ ]+\s*", "", title, flags=re.IGNORECASE).strip()
        project_title = re.sub(r"^Doctorant\s+[FH/ ]+\s*", "", project_title, flags=re.IGNORECASE).strip()
        project_title = re.sub(r"^\-+\s*", "", project_title).strip()
        return project_title or title

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

        if query.countries and opportunity.country:
            if opportunity.country.lower() not in {country.lower() for country in query.countries}:
                return False

        if query.domain_tags:
            requested = {item.lower() for item in query.domain_tags}
            current = {item.lower() for item in opportunity.domain_tags}
            if not requested.intersection(current):
                return False
        elif not opportunity.domain_tags:
            return False

        if query.query:
            query_words = [word for word in re.split(r"\W+", query.query.lower()) if len(word) > 2]
            if query_words and not any(word in haystack for word in query_words):
                return False

        return True

    def _is_phd_title(self, title: str) -> bool:
        lowered = title.lower()
        if "postdoc" in lowered or "post-doctoral" in lowered or "post doctoral" in lowered:
            return False
        return "phd" in lowered or "doctorant" in lowered or "doctoral" in lowered

    def _get_heading_text(self, soup: BeautifulSoup, tag_name: str) -> str | None:
        node = soup.find(tag_name)
        if node is None:
            return None
        return self._clean_text(node.get_text(" ", strip=True)) or None

    def _clean_text(self, value: str | None) -> str:
        return clean_text(value)
