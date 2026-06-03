from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
API_DIR = REPO_ROOT / "apps" / "api"
SECRET_PATTERNS = [
    re.compile(r"sk-[A-Za-z0-9_-]{16,}"),
    re.compile(r"(?i)(api[_-]?key|secret|token|password)\s*=\s*['\"]?[^'\"\s]+"),
]
SKIP_PARTS = {
    ".git",
    ".pytest_cache",
    "__pycache__",
    ".venv",
    "venv",
    "node_modules",
    "outputs",
    "work",
}
SKIP_SUFFIXES = {".pyc", ".db", ".log"}


def run(command: list[str], cwd: Path = REPO_ROOT) -> None:
    print(f":: {' '.join(command)}")
    completed = subprocess.run(command, cwd=cwd, text=True)
    if completed.returncode != 0:
        raise SystemExit(completed.returncode)


def secret_scan() -> None:
    findings: list[str] = []
    for path in REPO_ROOT.rglob("*"):
        if not path.is_file():
            continue
        if any(part in SKIP_PARTS for part in path.parts):
            continue
        if path.suffix in SKIP_SUFFIXES:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for pattern in SECRET_PATTERNS:
            for match in pattern.finditer(text):
                findings.append(f"{path.relative_to(REPO_ROOT)}:{match.start()}")

    if findings:
        print("Secret scan findings:")
        for finding in findings:
            print(f"- {finding}")
        raise SystemExit(1)

    print(":: secret scan PASS")


def main() -> None:
    run([sys.executable, "-m", "compileall", "apps/api", "api", "-q"])
    run([sys.executable, "-m", "pytest", "-q"], cwd=API_DIR)
    run([sys.executable, "-c", "from api.index import app; print(app.title)"])
    secret_scan()
    print(":: V1 validation PASS")


if __name__ == "__main__":
    main()
