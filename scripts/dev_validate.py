from __future__ import annotations

import argparse

from dev_common import configure_local_environment, ensure_api_path, masked_database_url


REQUIRED_PUBLIC_ENDPOINTS = [
    "/",
    "/health",
    "/readiness",
    "/runtime/status",
    "/version",
    "/api/v1/apps",
    "/api/v1/apps/hermes",
    "/api/v1/integrations/apps/hermes/discovery",
]

REQUIRED_DATABASE_ENDPOINTS = [
    "/api/v1/integration-bus",
    "/api/v1/contracts?app_id=hermes",
]

REQUIRED_PROTECTED_ENDPOINTS = [
    "/api/v1/auth/me",
    "/api/v1/control-center",
    "/api/v1/control-center/apps",
    "/api/v1/governance/integration-gates",
    "/api/v1/observability/status",
]


def assert_status(response, expected: int, label: str) -> dict:
    if response.status_code != expected:
        raise RuntimeError(f"{label} expected {expected}, got {response.status_code}: {response.text}")
    try:
        return response.json()
    except Exception:
        return {}


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate the local ecosystem foundation runtime.")
    parser.add_argument(
        "--allow-sqlite",
        action="store_true",
        help="Allow SQLite fallback for validation when PostgreSQL is not available.",
    )
    args = parser.parse_args()

    configure_local_environment(prefer_sqlite=args.allow_sqlite)
    ensure_api_path()

    from fastapi.testclient import TestClient

    from app.main import app

    client = TestClient(app, raise_server_exceptions=False)
    print(f":: database {masked_database_url()}")

    for path in REQUIRED_PUBLIC_ENDPOINTS:
        payload = assert_status(client.get(path), 200, path)
        print(f":: {path} PASS")

    runtime = assert_status(client.get("/runtime/status"), 200, "/runtime/status")
    database = runtime["database"]
    if database["status"] != "connected":
        raise RuntimeError(
            "Local database is not connected. Start PostgreSQL with docker compose up -d postgres "
            f"or use --allow-sqlite for fallback validation. Detail: {database}"
        )
    if not args.allow_sqlite and database["backend"] != "postgresql":
        raise RuntimeError(
            "Local validation requires PostgreSQL. Start Docker Compose or pass --allow-sqlite for fallback validation."
        )
    if args.allow_sqlite and database["backend"] not in {"postgresql", "sqlite"}:
        raise RuntimeError(f"Unsupported local database backend: {database['backend']}")

    for path in REQUIRED_DATABASE_ENDPOINTS:
        assert_status(client.get(path), 200, path)
        print(f":: {path} PASS")

    login = assert_status(
        client.post(
            "/api/v1/auth/login",
            json={
                "email": "ceo.local@example.com",
                "password": "example-local-control-center-password",
            },
        ),
        200,
        "/api/v1/auth/login",
    )
    headers = {"Authorization": f"Bearer {login['token']}"}
    print(":: /api/v1/auth/login PASS")

    for path in REQUIRED_PROTECTED_ENDPOINTS:
        assert_status(client.get(path, headers=headers), 200, path)
        print(f":: {path} PASS")

    control_center_html = client.get("/control-center")
    if control_center_html.status_code != 200 or "Control Center" not in control_center_html.text:
        raise RuntimeError("/control-center HTML validation failed")
    print(":: /control-center HTML PASS")

    hermes = assert_status(
        client.get("/api/v1/integrations/apps/hermes/discovery"),
        200,
        "/api/v1/integrations/apps/hermes/discovery",
    )
    if hermes["external_connection_enabled"]:
        raise RuntimeError("Hermes discovery must not enable external runtime connections.")
    print(
        ":: local validation PASS "
        f"database={database['backend']} hermes={hermes['health_status']}"
    )


if __name__ == "__main__":
    main()
