"""Reproducible audit: run from repository root with dependencies installed.
No deployments, provider requests, or paid APIs. Uses isolated local SQLite.
"""
from pathlib import Path
import os
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory(prefix="dropshipping-audit-") as work:
    env = os.environ.copy()
    # Do not inherit configured external services or database credentials.
    for key in list(env):
        if any(word in key.upper() for word in ("TOKEN", "SECRET", "API_KEY", "PASSWORD", "DATABASE_URL", "VERCEL", "LINKEDIN")):
            env.pop(key, None)
    env.update(ECOSYSTEM_API_ENVIRONMENT="local",
               ECOSYSTEM_API_DATABASE_URL="sqlite:///" + str(Path(work) / "audit.db"),
               CONTROL_CENTER_AUTH_ENABLED="true",
               CEREBRO_LLM_ENABLED="false", ARSENAL_API_BROKER_ENABLED="false",
               LINKEDIN_POSTING_ENABLED="false")
    commands = [
        [sys.executable, "-m", "compileall", "-q", "apps/api"],
        [sys.executable, "-m", "pytest", "-q", "apps/api/tests", "-k", "dropshipping"],
    ]
    if "--full" in sys.argv[1:]:
        commands[1] = [sys.executable, "-m", "pytest", "-q", "apps/api/tests"]
    if "--junit" in sys.argv[1:]:
        report = Path(sys.argv[sys.argv.index("--junit") + 1]).resolve()
        commands[1].extend(["--junitxml", str(report)])
    for cmd in commands:
        subprocess.run(cmd, cwd=ROOT, env=env, check=True)
