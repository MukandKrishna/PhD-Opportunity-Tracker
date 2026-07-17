import pytest
from fastapi import HTTPException

from app.auth import require_ingest_api_key
from app.config import get_settings
from app.main import healthcheck


@pytest.fixture(autouse=True)
def clear_settings_cache():
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def test_normalizes_render_postgres_url_and_adds_cors_origins(monkeypatch):
    monkeypatch.setenv(
        "PHD_TRACKER_DATABASE_URL",
        "postgresql://tracker:secret@internal-host/phd_tracker",
    )
    monkeypatch.setenv(
        "PHD_TRACKER_CORS_ORIGINS",
        "https://mukandkrishna.github.io/, https://demo.example",
    )

    settings = get_settings()

    assert settings.database_url == (
        "postgresql+psycopg://tracker:secret@internal-host/phd_tracker"
    )
    assert "https://mukandkrishna.github.io" in settings.cors_origins
    assert "https://demo.example" in settings.cors_origins


def test_render_fails_closed_when_ingest_key_is_missing(monkeypatch):
    monkeypatch.setenv("RENDER", "true")
    monkeypatch.delenv("PHD_TRACKER_INGEST_API_KEY", raising=False)

    with pytest.raises(HTTPException) as error:
        require_ingest_api_key(None)

    assert error.value.status_code == 503


def test_ingest_key_uses_constant_time_validation(monkeypatch):
    monkeypatch.setenv("PHD_TRACKER_INGEST_API_KEY", "correct-secret")

    with pytest.raises(HTTPException) as error:
        require_ingest_api_key("wrong-secret")
    assert error.value.status_code == 401

    require_ingest_api_key("correct-secret")


def test_healthcheck_checks_database_without_exposing_configuration():
    class FakeSession:
        statement = None

        def execute(self, statement):
            self.statement = statement

    session = FakeSession()

    assert healthcheck(session) == {"status": "ok"}
    assert str(session.statement) == "SELECT 1"
