from __future__ import annotations

import argparse
from pathlib import Path

from dev_common import configure_local_environment, ensure_api_path, is_safe_local_database_url


def reset_sqlite(database_url: str) -> None:
    raw_path = database_url.removeprefix("sqlite:///")
    if raw_path == ":memory:":
        print(":: sqlite memory database does not need reset")
        return
    path = Path(raw_path).expanduser().resolve()
    if path.exists():
        path.unlink()
        print(f":: removed {path}")
    else:
        print(f":: sqlite file not found: {path}")


def reset_postgres(database_url: str) -> None:
    import psycopg

    with psycopg.connect(database_url, autocommit=True) as connection:
        with connection.cursor() as cursor:
            cursor.execute("DROP SCHEMA IF EXISTS public CASCADE")
            cursor.execute("CREATE SCHEMA public")
            cursor.execute("GRANT ALL ON SCHEMA public TO public")
    print(":: local PostgreSQL public schema reset")


def main() -> None:
    parser = argparse.ArgumentParser(description="Reset the local development database.")
    parser.add_argument("--yes", action="store_true", help="Confirm destructive local reset.")
    parser.add_argument("--allow-sqlite", action="store_true")
    args = parser.parse_args()

    if not args.yes:
        raise SystemExit("Refusing to reset without --yes.")

    configure_local_environment(prefer_sqlite=args.allow_sqlite)
    ensure_api_path()

    from app.core.config import get_settings
    from app.core.database import get_database_backend

    database_url = get_settings().database_url
    if not is_safe_local_database_url(database_url):
        raise SystemExit("Refusing to reset a database URL that does not look local.")

    backend = get_database_backend(database_url)
    if backend == "sqlite":
        reset_sqlite(database_url)
    elif backend == "postgresql":
        reset_postgres(database_url)
    else:
        raise SystemExit(f"Unsupported backend: {backend}")

    print(":: dev reset PASS")


if __name__ == "__main__":
    main()
