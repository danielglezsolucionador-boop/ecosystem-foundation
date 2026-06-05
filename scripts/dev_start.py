from __future__ import annotations

import argparse

from dev_common import configure_local_environment, ensure_api_path, masked_database_url


def main() -> None:
    parser = argparse.ArgumentParser(description="Start the local Ecosystem Foundation API.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--reload", action="store_true")
    parser.add_argument(
        "--allow-sqlite",
        action="store_true",
        help="Use SQLite fallback when PostgreSQL is not available.",
    )
    args = parser.parse_args()

    configure_local_environment(prefer_sqlite=args.allow_sqlite)
    ensure_api_path()

    import uvicorn

    print(f":: starting Ecosystem Foundation API on http://{args.host}:{args.port}")
    print(f":: database {masked_database_url()}")
    uvicorn.run(
        "app.main:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        app_dir="apps/api",
    )


if __name__ == "__main__":
    main()
