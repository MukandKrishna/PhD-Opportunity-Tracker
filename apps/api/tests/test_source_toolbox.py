import httpx

from app.sources import fetching
from app.sources.extraction import (
    extract_labeled_value,
    extract_required_documents,
    html_to_lines,
)
from app.sources.fetching import FetchOptions, _response_to_text, fetch_text, looks_like_bot_challenge


class _FakeResponse:
    def __init__(self, text: str, status_code: int = 200):
        self.text = text
        self.status_code = status_code
        self.request = httpx.Request("GET", "https://example.test/page")


class _FakeClient:
    def __init__(self, response: _FakeResponse):
        self.response = response

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return None

    def get(self, _url: str):
        return self.response


def test_fetch_text_uses_scrapling_fallback_for_browser_challenge(monkeypatch):
    challenge = _FakeResponse("Checking your browser before accessing the site")

    def fake_client(**_kwargs):
        return _FakeClient(challenge)

    monkeypatch.setattr(fetching.httpx, "Client", fake_client)
    monkeypatch.setattr(fetching, "_fetch_with_scrapling", lambda _url, _options: "<html>real page</html>")

    text = fetch_text("https://example.test/page", options=FetchOptions(source_name="example"))

    assert text == "<html>real page</html>"


def test_scrapling_response_conversion_uses_body_when_text_is_empty():
    class Response:
        text = ""
        html = None
        body = b"<html>body page</html>"

    assert _response_to_text(Response()) == "<html>body page</html>"


def test_bot_challenge_detection_catches_common_markers():
    assert looks_like_bot_challenge("Please verify you are a human")
    assert looks_like_bot_challenge("cf_chl_12345")
    assert not looks_like_bot_challenge('<script src="https://hcaptcha.com/1/api.js"></script>')
    assert not looks_like_bot_challenge("<html><h1>PhD Position</h1></html>")


def test_labeled_value_parser_handles_inline_and_next_line_values():
    lines = [
        "Application Deadline:",
        "30 June 2026",
        "Funding | Fully funded studentship",
    ]

    assert extract_labeled_value(lines, ["Application Deadline"]) == "30 June 2026"
    assert extract_labeled_value(lines, ["Funding"]) == "Fully funded studentship"


def test_document_extraction_and_noise_cleanup():
    text = "Please upload your CV, motivation letter, research proposal, transcripts and references."
    assert extract_required_documents(text) == [
        "CV",
        "Cover Letter",
        "Research Proposal",
        "Transcripts",
        "References",
    ]

    lines = html_to_lines(
        """
        <html>
          <body>
            <nav>Navigation noise</nav>
            <main><h1>PhD Position in Machine Learning</h1></main>
            <aside>Related jobs in AI</aside>
          </body>
        </html>
        """
    )
    assert lines == ["PhD Position in Machine Learning"]
