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
    assert settings.database_url_source == "default"


def test_settings_accept_database_url_alias_for_vercel() -> None:
    settings = Settings.from_mapping(
        {
            "ECOSYSTEM_API_ENVIRONMENT": "staging",
            "DATABASE_URL": "postgresql://user:pass@example.com:5432/ecosystem",
        }
    )

    assert settings.environment == "staging"
    assert settings.database_url == "postgresql://user:pass@example.com:5432/ecosystem"
    assert settings.database_url_source == "DATABASE_URL"


def test_explicit_ecosystem_database_url_wins_over_alias() -> None:
    settings = Settings.from_mapping(
        {
            "DATABASE_URL": "postgresql://user:pass@example.com:5432/cloud",
            "ECOSYSTEM_API_DATABASE_URL": "sqlite:///:memory:",
        }
    )

    assert settings.database_url == "sqlite:///:memory:"
    assert settings.database_url_source == "ECOSYSTEM_API_DATABASE_URL"


def test_settings_ignore_blank_vercel_environment_values() -> None:
    settings = Settings.from_mapping(
        {
            "ECOSYSTEM_API_ENVIRONMENT": "",
            "VERCEL_ENV": "preview",
            "ECOSYSTEM_API_SERVICE_NAME": "",
            "ECOSYSTEM_API_VERSION": "",
            "ECOSYSTEM_API_COMMIT": "",
            "ECOSYSTEM_API_DEBUG": "",
            "ECOSYSTEM_API_DATABASE_URL": "",
            "DATABASE_URL": "postgresql://user:pass@example.com:5432/cloud",
        }
    )

    assert settings.environment == "staging"
    assert settings.service_name == "ecosystem-foundation-api"
    assert settings.version == "0.1.0"
    assert settings.commit == "unknown"
    assert settings.debug is False
    assert settings.database_url == "postgresql://user:pass@example.com:5432/cloud"
    assert settings.database_url_source == "DATABASE_URL"


def test_settings_derive_production_environment_from_vercel() -> None:
    settings = Settings.from_mapping(
        {
            "ECOSYSTEM_API_ENVIRONMENT": "",
            "VERCEL_ENV": "production",
        }
    )

    assert settings.environment == "production"


def test_settings_prefer_vercel_git_commit_sha_over_manual_commit() -> None:
    settings = Settings.from_mapping(
        {
            "ECOSYSTEM_API_COMMIT": "oldsha1",
            "VERCEL_GIT_COMMIT_SHA": "1234567890abcdef",
        }
    )

    assert settings.commit == "1234567"


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
