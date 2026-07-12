from app.sources.academictransfer import AcademicTransferSource
from app.sources.base import SourceQuery


LISTING_HTML = """
<html>
  <body>
    <a href="/en/jobs/361105/phd-position-scientific-machine-learning-toward-scientific-foundation-models/"></a>
    <a href="/en/jobs/361343/postdoctoral-researcher-in-learning-from-interaction-signals/"></a>
    <a href="/en/jobs/361142/phd-student-machine-learning-for-semiconductor-wafer-metrology/"></a>
  </body>
</html>
"""


DETAIL_HTML = """
<html>
  <head>
    <script type="application/ld+json">
      {
        "@context": "https://schema.org",
        "@type": "WebPage",
        "mainEntity": {
          "@context": "http://schema.org",
          "@type": "JobPosting",
          "validThrough": "2026-06-14T23:59:59+02:00",
          "title": "PhD Position Scientific Machine Learning, Toward Scientific Foundation Models",
          "description": "<strong>Job description</strong><br>We invite applications for a fully funded PhD position in Scientific Machine Learning and foundation models.<br><br><strong>Job requirements</strong><br>Doing a PhD requires strong programming, machine learning, and English skills.<br><br>Doctoral candidates will be offered a 4-year period of employment.<br>If you would like more information about this vacancy or the selection procedure, please contact Dr. Jing Sun, via jing.sun@tudelft.nl.<br>Are you interested in this vacancy? Please apply no later than 14 June 2026. You can apply online. Please include your CV, cover letter and transcripts.",
          "baseSalary": {
            "@type": "MonetaryAmount",
            "currency": "EUR",
            "value": {
              "@type": "QuantitativeValue",
              "unitText": "MONTH",
              "minValue": 3059,
              "maxValue": 3881
            }
          },
          "jobLocation": {
            "@type": "Place",
            "address": {
              "@type": "PostalAddress",
              "addressLocality": "Delft",
              "addressCountry": "NL"
            }
          },
          "hiringOrganization": {
            "@type": "Organization",
            "name": "Delft University of Technology (TU Delft)"
          },
          "identifier": {
            "@type": "PropertyValue",
            "name": "AcademicTransfer",
            "value": "361105"
          }
        }
      }
    </script>
  </head>
  <body>
    <h1>PhD Position Scientific Machine Learning, Toward Scientific Foundation Models</h1>
    <a href="https://www.academictransfer.com/en/jobs/361105/phd-position-scientific-machine-learning-toward-scientific-foundation-models/apply/">
      Apply now
    </a>
  </body>
</html>
"""


def test_listing_parser_keeps_phd_urls_and_skips_postdocs():
    source = AcademicTransferSource()
    urls = source._parse_listing_urls(LISTING_HTML)

    assert urls == [
        "https://www.academictransfer.com/en/jobs/361105/phd-position-scientific-machine-learning-toward-scientific-foundation-models/",
        "https://www.academictransfer.com/en/jobs/361142/phd-student-machine-learning-for-semiconductor-wafer-metrology/",
    ]


def test_detail_parser_extracts_structured_fields_and_apply_link():
    source = AcademicTransferSource()
    item = source._parse_detail(
        "https://www.academictransfer.com/en/jobs/361105/phd-position-scientific-machine-learning-toward-scientific-foundation-models/",
        DETAIL_HTML,
    )

    assert item is not None
    assert item.external_id == "361105"
    assert item.source_name == "academictransfer"
    assert item.official_url == "https://www.academictransfer.com/en/jobs/361105/phd-position-scientific-machine-learning-toward-scientific-foundation-models/apply/"
    assert item.institution == "Delft University of Technology (TU Delft)"
    assert item.country == "Netherlands"
    assert item.city == "Delft"
    assert item.deadline_text == "2026-06-14"
    assert item.salary_stipend == "EUR 3059 - 3881 / month"
    assert item.duration_text == "4-year period of employment"
    assert item.supervisor_name == "Jing Sun"
    assert item.contact_info == "jing.sun@tudelft.nl"
    assert "ML" in item.domain_tags
    assert "CV" in item.required_documents
    assert "Cover Letter" in item.required_documents
    assert "Transcripts" in item.required_documents


def test_scope_matching_respects_domain_filters():
    source = AcademicTransferSource()
    item = source._parse_detail(
        "https://www.academictransfer.com/en/jobs/361105/phd-position-scientific-machine-learning-toward-scientific-foundation-models/",
        DETAIL_HTML,
    )

    assert item is not None
    assert source._matches_scope(item, SourceQuery(domain_tags=["ML"]))
    assert not source._matches_scope(item, SourceQuery(domain_tags=["RAG"]))
