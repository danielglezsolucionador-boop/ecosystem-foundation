from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT = REPO_ROOT / "work" / "command_core_production_auth_close.mjs"


def test_command_core_close_script_redacts_sensitive_output() -> None:
    text = SCRIPT.read_text(encoding="utf-8")

    assert "function redactSensitive" in text
    assert "function safeLogError" in text
    assert "async function safeApiGet" in text
    assert "BLOCKED DAILY CENTER" in text
    assert "Authorization: Bearer [REDACTED]" in text
    assert "ccs_[REDACTED]" in text
    assert "error.stack" not in text
    assert "console.error(error" not in text


def test_command_core_close_script_avoids_raw_authorization_logging() -> None:
    text = SCRIPT.read_text(encoding="utf-8")
    unsafe_patterns = [
        "console.log(headers",
        "console.error(headers",
        "console.log(token",
        "console.error(token",
        "console.log(`Bearer",
        "console.error(`Bearer",
    ]

    for pattern in unsafe_patterns:
        assert pattern not in text
