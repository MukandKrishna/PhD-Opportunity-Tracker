from app.sources.base import SourceQuery
from app.sources.jobs_ac_uk import JobsAcUkSource


LISTING_HTML = """
<html>
  <body>
    <a href="/job/DRK299/phd-studentship-intrinsically-aligned-machine-learning">
      PhD Studentship: Intrinsically-aligned machine learning
    </a>
    <a href="/job/AAA111/lecturer-in-computer-science">
      Lecturer in Computer Science
    </a>
    <a href="/job/BBB222/msc-by-research-studentship-machine-learning">
      MSc by Research Studentship: machine learning
    </a>
  </body>
</html>
"""


DETAIL_HTML = """
<html>
  <body>
    <h1>PhD Studentship: Intrinsically-aligned machine learning</h1>
    <h3>Oxford Brookes University - Faculty of Health, Science and Technology - School of ECM</h3>
    <table>
      <tr><th>Qualification Type:</th><td>PhD</td></tr>
      <tr><th>Location:</th><td>Oxford</td></tr>
      <tr><th>Funding for:</th><td>UK Students, EU Students, International Students</td></tr>
      <tr><th>Funding amount:</th><td>GBP 21,805 p.a.</td></tr>
      <tr><th>Hours:</th><td>Full Time</td></tr>
      <tr><th>Placed On:</th><td>1st May 2026</td></tr>
      <tr><th>Closes:</th><td>22nd May 2026</td></tr>
    </table>
    <main>
      <p>3 Year Full-time PhD Studentship Funded by Leverhulme Trust</p>
      <p>Eligibility: Open to Applications from Home and International students</p>
      <p>Bursary p.a.: GBP 21,805</p>
      <p>Start Date: 14th September 2026</p>
      <p>Application deadline: 22nd May 2026</p>
      <p>Course length (full time): 3 years</p>
      <p>Director of Studies: Prof Fabio Cuzzolin, Dr Matthias Rolf</p>
      <p>Entry Requirements: At least an upper second class degree in a Science or Technology discipline.</p>
      <p>Essential Criteria: Good working knowledge of machine learning and deep learning.</p>
      <p>Please submit your CV, cover letter, transcripts and references.</p>
      <a href="https://www.brookes.ac.uk/study/postgraduate/research/apply">Apply online</a>
    </main>
  </body>
</html>
"""


def test_listing_parser_keeps_only_phd_urls():
    source = JobsAcUkSource()
    urls = source._parse_listing_urls(LISTING_HTML)

    assert urls == [
        "https://www.jobs.ac.uk/job/DRK299/phd-studentship-intrinsically-aligned-machine-learning"
    ]


def test_detail_parser_extracts_core_fields():
    source = JobsAcUkSource()
    item = source._parse_detail(
        "https://www.jobs.ac.uk/job/DRK299/phd-studentship-intrinsically-aligned-machine-learning",
        DETAIL_HTML,
    )

    assert item is not None
    assert item.external_id == "DRK299"
    assert item.institution == "Oxford Brookes University"
    assert item.country == "United Kingdom"
    assert item.city == "Oxford"
    assert item.salary_stipend == "GBP 21,805 p.a."
    assert item.official_url == "https://www.brookes.ac.uk/study/postgraduate/research/apply"
    assert item.duration_text == "3 years"
    assert item.start_date_text == "14th September 2026"
    assert item.supervisor_name == "Prof Fabio Cuzzolin, Dr Matthias Rolf"
    assert "ML" in item.domain_tags
    assert "DL" in item.domain_tags
    assert "CV" in item.required_documents
    assert "Cover Letter" in item.required_documents
    assert "Transcripts" in item.required_documents


def test_detail_parser_preserves_jobs_ac_uk_advert_content_classes():
    html = """
    <html>
      <body>
        <article class="j-advert">
          <h1>PhD Studentship - AI-Driven Fault Diagnosis for Wind Turbine Generators</h1>
          <h3>University of East Anglia - School of Engineering</h3>
          <table>
            <tr><th>Qualification Type:</th><td>PhD</td></tr>
            <tr><th>Location:</th><td>Norwich</td></tr>
            <tr><th>Closes:</th><td>31st July 2026</td></tr>
          </table>
          <main>
            <p>This doctoral project studies artificial intelligence for wind turbine diagnosis.</p>
            <a href="https://www.uea.ac.uk/apply/postgraduate/research">Apply online</a>
          </main>
        </article>
      </body>
    </html>
    """
    source = JobsAcUkSource()
    item = source._parse_detail("https://www.jobs.ac.uk/job/DRV961/example", html)

    assert item is not None
    assert item.title == "PhD Studentship - AI-Driven Fault Diagnosis for Wind Turbine Generators"
    assert item.official_url == "https://www.uea.ac.uk/apply/postgraduate/research"
    assert "AI" in item.domain_tags


def test_scope_matching_respects_domain_filters():
    source = JobsAcUkSource()
    item = source._parse_detail(
        "https://www.jobs.ac.uk/job/DRK299/phd-studentship-intrinsically-aligned-machine-learning",
        DETAIL_HTML,
    )

    assert item is not None
    assert source._matches_scope(item, SourceQuery(domain_tags=["ML"]))
    assert not source._matches_scope(item, SourceQuery(domain_tags=["RAG"]))


def test_detail_parser_ignores_related_jobs_when_tagging():
    html = """
    <html>
      <body>
        <h1>PhD Studentship - Stability of Soap Films and Foams</h1>
        <h3>University of East Anglia - School of Mathematics</h3>
        <table>
          <tr><th>Qualification Type:</th><td>PhD</td></tr>
          <tr><th>Location:</th><td>Norwich</td></tr>
          <tr><th>Closes:</th><td>31st July 2026</td></tr>
        </table>
        <main>
          <p>This project studies nonlinear fluid mechanics and laboratory foam stability.</p>
          <p>Start date:</p>
          <p>1 October 2026</p>
          <p>Location(s):</p>
          <p>PhD Studentship - Wave Dynamics on Complex Networks: From Graph Theory to Machine Learning</p>
        </main>
      </body>
    </html>
    """
    source = JobsAcUkSource()
    item = source._parse_detail("https://www.jobs.ac.uk/job/DRV979/example", html)

    assert item is None
