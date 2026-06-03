import pytest

from app.core.config import Settings, parse_bool, parse_csv


def test_settings_default_to_safe_local_values() -> None:
    settings = Settings.from_mapping({})

    assert settings.service_name == "ecosystem-foundation-api"
    assert settings.environment == "local"
    assert settings.version == "0.1.0"
    assert settings.commit == "unknown"
    assert settings.cors_origins == ("http://localhost:5173",)
    assert settings.debug is False
    assert settings.database_url == "sqlite:///./var/ecosystem_foundation.db"


def test_settings_accept_database_url_alias_for_vercel() -> None:
    settings = Settings.from_mapping(
        {
            "ECOSYSTEM_API_ENVIRONMENT": "staging",
            "DATABASE_URL": "postgresql://user:pass@example.com:5432/ecosystem",
        }
    )

    assert settings.environment == "staging"
    assert settings.database_url == "postgresql://user:pass@example.com:5432/ecosystem"


def test_explicit_ecosystem_database_url_wins_over_alias() -> None:
    settings = Settings.from_mapping(
        {
            "DATABASE_URL": "postgresql://user:pass@example.com:5432/cloud",
            "ECOSYSTEM_API_DATABASE_URL": "sqlite:///:memory:",
        }
    )

    assert settings.database_url == "sqlite:///:memory:"


def test_settings_reject_invalid_environment() -> None:
    with pytest.raises(RuntimeError):
        Settings.from_mapping({"ECOSYSTEM_API_ENVIRONMENT": "demo"})


def test_parse_helpers() -> None:
    assert parse_bool("true") is True
    assert parse_bool("false") is False
    assert parse_csv("http://localhost:5173, https://example.test") == (
        "http://localhost:5173",
        "https://example.test",
    )
