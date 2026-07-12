from app.sources.base import SourceQuery
from app.sources.inria import InriaSource, _ListingCandidate


DETAIL_HTML = """
<html>
  <body>
    <h1>PhD Position F/M Distributed Training of Machine Learning Models with Malicious Clients</h1>
    <p>Contract type : Fixed-term contract</p>
    <p>Level of qualifications required : Graduate degree or equivalent</p>
    <p>Fonction : PhD Position</p>
    <h2>Context</h2>
    <p>This PhD thesis focuses on distributed learning, privacy, and machine learning security.</p>
    <h2>Skills</h2>
    <p>Strong background in probability, optimization, statistical machine learning, and Python.</p>
    <h2>Remuneration</h2>
    <p>Duration: 36 months</p>
    <p>Gross Salary per month: 2300 €</p>
    <h2>General Information</h2>
    <p>Theme/Domain : Optimization, machine learning and statistical methods</p>
    <p>Town/city : Sophia Antipolis</p>
    <p>Inria Center : Centre Inria d'Université Côte d'Azur</p>
    <p>Starting date : 2026-10-01</p>
    <p>Duration of contract : 3 years</p>
    <p>Deadline to apply : 2026-06-21</p>
    <h2>Instruction to apply</h2>
    <p>Please submit online your resume, cover letter and transcripts.</p>
    <h2>Contacts</h2>
    <p>Inria Team : NEO</p>
    <p>PhD Supervisor :</p>
    <p>Neglia Giovanni / Giovanni.Neglia@inria.fr</p>
    <a href="https://www-sop.inria.fr/members/Giovanni.Neglia/">Supervisor profile</a>
  </body>
</html>
"""


LISTING_HTML = """
<html>
  <body>
    <a href="/public/classic/en/offres/2026-10076">
      PhD Position F/M Distributed Training of Machine Learning Models with Malicious Clients
    </a>
    <a href="/public/classic/en/offres/2026-10053">
      Post-Doctoral Research Visit F/M Embedded Systems, Neural Networks and Privacy-preserving Embedded Edge AI Techniques
    </a>
  </body>
</html>
"""


def test_parse_listing_only_keeps_phd_entries():
    source = InriaSource()
    items = source._parse_listing(LISTING_HTML)

    assert len(items) == 1
    assert items[0].external_id == "2026-10076"


def test_parse_detail_extracts_expected_fields():
    source = InriaSource()
    candidate = _ListingCandidate(
        external_id="2026-10076",
        title="PhD Position F/M Distributed Training of Machine Learning Models with Malicious Clients",
        url="https://jobs.inria.fr/public/classic/en/offres/2026-10076",
    )

    item = source._parse_detail(candidate, DETAIL_HTML)

    assert item is not None
    assert item.institution == "Inria"
    assert item.country == "France"
    assert item.city == "Sophia Antipolis"
    assert item.lab == "NEO"
    assert item.supervisor_name == "Neglia Giovanni"
    assert item.supervisor_profile_url == "https://www-sop.inria.fr/members/Giovanni.Neglia/"
    assert item.duration_text == "3 years"
    assert item.start_date_text == "2026-10-01"
    assert item.deadline_text == "2026-06-21"
    assert "ML" in item.domain_tags
    assert "CV" in item.required_documents
    assert "Cover Letter" in item.required_documents
    assert "Transcripts" in item.required_documents


def test_scope_filters_non_target_records_without_tags():
    source = InriaSource()
    candidate = _ListingCandidate(
        external_id="2026-10076",
        title="PhD Position F/M Distributed Training of Machine Learning Models with Malicious Clients",
        url="https://jobs.inria.fr/public/classic/en/offres/2026-10076",
    )
    item = source._parse_detail(candidate, DETAIL_HTML)

    assert item is not None
    assert source._matches_scope(item, SourceQuery(query="machine learning", domain_tags=["ML"]))
    assert not source._matches_scope(item, SourceQuery(domain_tags=["RAG"]))
