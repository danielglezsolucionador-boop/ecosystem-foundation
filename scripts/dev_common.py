from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlparse


REPO_ROOT = Path(__file__).resolve().parents[1]
API_DIR = REPO_ROOT / "apps" / "api"
LOCAL_ENV_PATH = REPO_ROOT / ".env.local"
LOCAL_DATABASE_URL = (
    "postgresql://ecosystem_local:ecosystem_local@127.0.0.1:55432/"
    "ecosystem_foundation_local?connect_timeout=3"
)
SQLITE_DATABASE_URL = "sqlite:///./var/ecosystem_foundation_dev.db"
LOCAL_ADMIN_EMAIL = "ceo.local@example.com"
LOCAL_ADMIN_PASSWORD = "example-local-control-center-password"
LOCAL_ADMIN_NAME = "Local CEO"


def load_env_file(path: Path = LOCAL_ENV_PATH) -> None:
    if not path.exists():
        return

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key:
            os.environ[key] = value


def configure_local_environment(*, prefer_sqlite: bool = False) -> None:
    load_env_file()
    os.environ.setdefault("ECOSYSTEM_API_ENVIRONMENT", "local")
    os.environ.setdefault("ECOSYSTEM_API_SERVICE_NAME", "ecosystem-foundation-api")
    os.environ.setdefault("ECOSYSTEM_API_VERSION", "0.1.0")
    os.environ.setdefault("ECOSYSTEM_API_COMMIT", "local-dev")
    os.environ.setdefault(
        "ECOSYSTEM_API_CORS_ORIGINS",
        "http://127.0.0.1:8000,http://localhost:8000,http://localhost:5173,http://127.0.0.1:5173",
    )
    os.environ.setdefault("ECOSYSTEM_API_DEBUG", "true")
    os.environ.setdefault(
        "ECOSYSTEM_API_DATABASE_URL",
        SQLITE_DATABASE_URL if prefer_sqlite else LOCAL_DATABASE_URL,
    )
    os.environ.setdefault("CONTROL_CENTER_ADMIN_EMAIL", LOCAL_ADMIN_EMAIL)
    os.environ.setdefault("CONTROL_CENTER_ADMIN_PASSWORD", LOCAL_ADMIN_PASSWORD)
    os.environ.setdefault("CONTROL_CENTER_ADMIN_NAME", LOCAL_ADMIN_NAME)


def ensure_api_path() -> None:
    api_path = str(API_DIR)
    if api_path not in sys.path:
        sys.path.insert(0, api_path)


def run_command(command: list[str], *, cwd: Path = REPO_ROOT) -> None:
    print(f":: {' '.join(command)}")
    completed = subprocess.run(command, cwd=cwd, text=True)
    if completed.returncode != 0:
        raise SystemExit(completed.returncode)


def masked_database_url() -> str:
    value = os.environ.get("ECOSYSTEM_API_DATABASE_URL") or os.environ.get("DATABASE_URL") or ""
    if not value:
        return "not_configured"
    parsed = urlparse(value)
    if not parsed.scheme:
        return "configured_unparsed"
    host = parsed.hostname or "local"
    port = f":{parsed.port}" if parsed.port else ""
    db_name = parsed.path.lstrip("/") or "database"
    return f"{parsed.scheme}://***@{host}{port}/{db_name}"


def is_safe_local_database_url(database_url: str) -> bool:
    parsed = urlparse(database_url)
    if parsed.scheme.startswith("sqlite"):
        raw_path = database_url.removeprefix("sqlite:///")
        if raw_path == ":memory:":
            return True
        path = Path(raw_path).expanduser().resolve()
        return path == REPO_ROOT / "var" / path.name or REPO_ROOT in path.parents

    if parsed.scheme not in {"postgresql", "postgres"}:
        return False

    host = parsed.hostname or ""
    db_name = parsed.path.lstrip("/")
    username = parsed.username or ""
    local_host = host in {"127.0.0.1", "localhost", "::1"}
    local_port = parsed.port in {5432, 55432, None}
    local_name = "local" in db_name.lower() or db_name == "ecosystem_foundation_local"
    local_user = "local" in username.lower() or username == "ecosystem_local"
    return local_host and local_port and local_name and local_user
