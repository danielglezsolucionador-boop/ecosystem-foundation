from __future__ import annotations

import argparse
import sys

from dev_common import API_DIR, REPO_ROOT, configure_local_environment, run_command


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the full local validation suite.")
    parser.add_argument(
        "--allow-sqlite",
        action="store_true",
        help="Allow SQLite fallback when PostgreSQL is not available.",
    )
    args = parser.parse_args()

    configure_local_environment(prefer_sqlite=args.allow_sqlite)
    run_command([sys.executable, "-m", "compileall", "apps/api", "api", "-q"])
    run_command([sys.executable, "-m", "pytest", "-q"], cwd=API_DIR)
    run_command([sys.executable, "scripts/validate_v1.py"], cwd=REPO_ROOT)
    validate_command = [sys.executable, "scripts/dev_validate.py"]
    if args.allow_sqlite:
        validate_command.append("--allow-sqlite")
    run_command(validate_command, cwd=REPO_ROOT)
    print(":: dev test all PASS")


if __name__ == "__main__":
    main()
