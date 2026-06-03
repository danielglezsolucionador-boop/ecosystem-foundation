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

