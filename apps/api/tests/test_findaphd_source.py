import pytest

from app.sources.base import SourceQuery
from app.sources.findaphd import FindAPhDSource


LISTING_HTML = """
<html>
  <body>
    <a href="/phds/project/ai-enabled-digital-accessibility/?p123456">
      PhD Studentship: AI-enabled digital accessibility
    </a>
    <a href="/phds/project/non-target-biology/?p999999">
      Biology research internship
    </a>
  </body>
</html>
"""


DETAIL_HTML = """
<html>
  <body>
    <h1>PhD Studentship: AI-enabled digital accessibility</h1>
    <p>University of Surrey</p>
    <p>Location: Guildford, United Kingdom</p>
    <p>Funding: Fully funded studentship</p>
    <p>Duration: 3 years</p>
    <p>Application Deadline: 30 June 2026</p>
    <p>Supervisor: Dr Alex Researcher</p>
    <p>
      This project uses artificial intelligence, machine learning, and RAG
      methods to improve accessibility.
    </p>
    <p>
      Entry requirements: strong master's degree in computer science or a
      related discipline.
    </p>
    <p>Please submit a CV, cover letter, research proposal and transcripts.</p>
    <a href="https://www.surrey.ac.uk/postgraduate/research/ai-accessibility">
      Apply on university page
    </a>
    <a href="https://www.surrey.ac.uk/people/alex-researcher">
      Supervisor profile
    </a>
  </body>
</html>
"""


def test_listing_parser_keeps_real_project_urls():
    source = FindAPhDSource()
    urls = source._parse_listing_urls(LISTING_HTML)

    assert urls == [
        "https://www.findaphd.com/phds/project/ai-enabled-digital-accessibility/?p123456"
    ]


def test_detail_parser_extracts_valid_links_and_fields():
    source = FindAPhDSource()
    item = source._parse_detail(
        "https://www.findaphd.com/phds/project/ai-enabled-digital-accessibility/?p123456",
        DETAIL_HTML,
    )

    assert item is not None
    assert item.external_id == "123456"
    assert item.institution == "University of Surrey"
    assert item.country == "United Kingdom"
    assert item.city == "Guildford"
    assert item.official_url == "https://www.surrey.ac.uk/postgraduate/research/ai-accessibility"
    assert item.supervisor_profile_url == "https://www.surrey.ac.uk/people/alex-researcher"
    assert item.deadline_text == "30 June 2026"
    assert "AI" in item.domain_tags
    assert "ML" in item.domain_tags
    assert "RAG" in item.domain_tags
    assert "CV" in item.required_documents
    assert "Cover Letter" in item.required_documents
    assert "Research Proposal" in item.required_documents
    assert "Transcripts" in item.required_documents


def test_scope_matching_respects_domain_filters():
    source = FindAPhDSource()
    item = source._parse_detail(
        "https://www.findaphd.com/phds/project/ai-enabled-digital-accessibility/?p123456",
        DETAIL_HTML,
    )

    assert item is not None
    assert source._matches_scope(item, SourceQuery(domain_tags=["RAG"]))
    assert not source._matches_scope(item, SourceQuery(domain_tags=["Agents"]))


def test_fetch_rejects_cloudflare_challenge(monkeypatch):
    source = FindAPhDSource()

    def fake_fetch(_url: str) -> str:
        raise RuntimeError(
            "FindAPhD returned a browser challenge; use browser-backed collection or an approved feed."
        )

    monkeypatch.setattr(source, "_fetch_text", fake_fetch)

    with pytest.raises(RuntimeError, match="browser challenge"):
        source.fetch_opportunities(SourceQuery(query="machine learning"))
