import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]


def test_vercel_json_routes_to_python_entrypoint() -> None:
    config = json.loads((REPO_ROOT / "vercel.json").read_text(encoding="utf-8"))

    assert config["version"] == 2
    assert config["builds"][0]["src"] == "api/index.py"
    assert config["builds"][0]["use"] == "@vercel/python"
    assert config["routes"][0]["dest"] == "api/index.py"


def test_vercel_entrypoint_exports_fastapi_app() -> None:
    entrypoint = (REPO_ROOT / "api" / "index.py").read_text(encoding="utf-8")

    assert "from app.main import app" in entrypoint
    assert "apps" in entrypoint
    assert "api" in entrypoint


def test_requirements_include_postgres_driver() -> None:
    requirements = (REPO_ROOT / "requirements.txt").read_text(encoding="utf-8")

    assert "fastapi" in requirements
    assert "psycopg[binary]" in requirements
