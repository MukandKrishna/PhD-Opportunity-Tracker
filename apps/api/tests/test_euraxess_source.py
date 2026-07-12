from app.sources.base import SourceQuery
from app.sources.euraxess import EuraxessSource


LISTING_HTML = """
<html>
  <body>
    <a href="/jobs/444476">
      Research Studentships (for students of a course that does not award an academic degree) - (BL106/2026-IST-ID)
    </a>
    <a href="/jobs/444470">
      Post-Doctoral Researcher Department of Speech and Hearing Sciences
    </a>
    <a href="/jobs/444466">
      Assistant professor at the Institute of Computer Science
    </a>
  </body>
</html>
"""


DETAIL_HTML = """
<html>
  <body>
    <h1>Job offer</h1>
    <h1 class="ecl-content-block__title">
      Research Studentships (for students of a course that does not award an academic degree) - (BL106/2026-IST-ID)
    </h1>
    <h2>Job Information</h2>
    <dl>
      <dt>Organisation/Company</dt>
      <dd>Associação do Instituto Superior Técnico para a Investigação e Desenvolvimento _IST-ID</dd>
      <dt>Department</dt>
      <dd>DRH</dd>
      <dt>Research Field</dt>
      <dd>Engineering » Computer engineering</dd>
      <dt>Application Deadline</dt>
      <dd>26 Jun 2026 - 23:59 (Europe/Lisbon)</dd>
      <dt>Country</dt>
      <dd>Portugal</dd>
      <dt>Offer Starting Date</dt>
      <dd>15 Jun 2026</dd>
      <dt>E-Mail</dt>
      <dd>cristinadeoliveira@ist-id.pt</dd>
      <dt>City</dt>
      <dd>Lisbon</dd>
    </dl>
    <h2>Offer Description</h2>
    <p>
      Applications are open for 1 Research Studentship within a multimodal AI project.
      Missing data is a challenging problem when developing machine learning systems.
      Duration: 3 months.
    </p>
    <h2>Where to apply</h2>
    <a href="https://isr.tecnico.ulisboa.pt/scholarships/">Apply now</a>
    <h2>Requirements</h2>
    <p>Please submit your CV, motivation letter and transcripts.</p>
    <h2>Work Location(s)</h2>
    <dl>
      <dt>Country</dt>
      <dd>Portugal</dd>
      <dt>City</dt>
      <dd>Lisbon</dd>
    </dl>
  </body>
</html>
"""


def test_listing_parser_keeps_doctoral_research_urls_and_skips_postdocs():
    source = EuraxessSource()
    urls = source._parse_listing_urls(LISTING_HTML)

    assert urls == ["https://euraxess.ec.europa.eu/jobs/444476"]


def test_detail_parser_extracts_fields_and_apply_link():
    source = EuraxessSource()
    item = source._parse_detail("https://euraxess.ec.europa.eu/jobs/444476", DETAIL_HTML)

    assert item is not None
    assert item.external_id == "444476"
    assert item.source_name == "euraxess"
    assert item.official_url == "https://isr.tecnico.ulisboa.pt/scholarships/"
    assert item.institution == "Associação do Instituto Superior Técnico para a Investigação e Desenvolvimento _IST-ID"
    assert item.department == "DRH"
    assert item.country == "Portugal"
    assert item.city == "Lisbon"
    assert item.start_date_text == "15 Jun 2026"
    assert item.deadline_text == "26 Jun 2026 - 23:59 (Europe/Lisbon)"
    assert item.contact_info == "cristinadeoliveira@ist-id.pt"
    assert item.duration_text == "3 months"
    assert "AI" in item.domain_tags
    assert "ML" in item.domain_tags
    assert "CV" in item.required_documents
    assert "Cover Letter" in item.required_documents
    assert "Transcripts" in item.required_documents


def test_scope_matching_respects_domain_filters():
    source = EuraxessSource()
    item = source._parse_detail("https://euraxess.ec.europa.eu/jobs/444476", DETAIL_HTML)

    assert item is not None
    assert source._matches_scope(item, SourceQuery(domain_tags=["ML"]))
    assert not source._matches_scope(item, SourceQuery(domain_tags=["RAG"]))
