from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


DEFAULT_BASE_URL = "https://ecosystem-foundation.vercel.app"
BLOCK_3_APPS = {
    "comercio_autonomo": "comercio_autonomo.discovery.v1",
    "buscador_de_tendencias": "buscador_de_tendencias.discovery.v1",
}


@dataclass(frozen=True)
class HttpResult:
    status: int
    payload: Any
    text: str


def env_required(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise SystemExit(f"Missing required environment variable: {name}")
    return value


def request_json(
    base_url: str,
    method: str,
    path: str,
    *,
    token: str | None = None,
    body: dict[str, Any] | None = None,
    expected: int = 200,
) -> HttpResult:
    headers = {"Accept": "application/json"}
    data = None
    if token:
        headers["Authorization"] = f"Bearer {token}"
    if body is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(body).encode("utf-8")

    request = Request(f"{base_url.rstrip('/')}{path}", data=data, headers=headers, method=method)
    try:
        with urlopen(request, timeout=30) as response:
            text = response.read().decode("utf-8")
            status = int(response.status)
    except HTTPError as exc:
        text = exc.read().decode("utf-8", errors="replace")
        status = int(exc.code)

    try:
        payload = json.loads(text) if text else {}
    except json.JSONDecodeError:
        payload = {}

    if status != expected:
        preview = text[:240].replace("\n", " ")
        raise RuntimeError(f"{method} {path} expected {expected}, got {status}: {preview}")
    return HttpResult(status=status, payload=payload, text=text)


def assert_field(payload: dict[str, Any], key: str, expected: Any, label: str) -> None:
    actual = payload.get(key)
    if actual != expected:
        raise RuntimeError(f"{label} expected {key}={expected!r}, got {actual!r}")


def assert_block3_discovery(base_url: str, token: str) -> None:
    app_registry = request_json(base_url, "GET", "/api/v1/apps", token=token).payload
    if not isinstance(app_registry, list):
        raise RuntimeError("App Registry list did not return a list")

    control_apps = request_json(base_url, "GET", "/api/v1/control-center/apps", token=token).payload
    control_by_id = {item.get("id"): item for item in control_apps if isinstance(item, dict)}

    gates = request_json(base_url, "GET", "/api/v1/governance/integration-gates", token=token).payload
    gates_by_id = {item.get("app_id"): item for item in gates if isinstance(item, dict)}

    services = request_json(base_url, "GET", "/api/v1/integration-bus/services", token=token).payload
    service_items = services.get("services", services) if isinstance(services, dict) else services
    services_by_id = {item.get("id"): item for item in service_items if isinstance(item, dict)}

    events_catalog = request_json(base_url, "GET", "/api/v1/events/catalog", token=token).payload
    event_ids = {item.get("id") for item in events_catalog if isinstance(item, dict)}

    for app_id, contract_id in BLOCK_3_APPS.items():
        registry = request_json(base_url, "GET", f"/api/v1/apps/{app_id}", token=token).payload
        if registry.get("id") != app_id:
            raise RuntimeError(f"App registry missing {app_id}")
        assert_field(registry, "touch_policy", "integration_prepared_no_runtime_connection", app_id)

        if app_id not in control_by_id:
            raise RuntimeError(f"Control Center missing {app_id}")
        if control_by_id[app_id].get("external_connection_enabled") is not False:
            raise RuntimeError(f"Control Center app {app_id} enabled an external connection")

        if app_id not in gates_by_id:
            raise RuntimeError(f"Governance gate missing {app_id}")
        if gates_by_id[app_id].get("protected") is not False:
            raise RuntimeError(f"Governance gate for {app_id} should not be protected")

        if app_id not in services_by_id:
            raise RuntimeError(f"Integration Bus service missing {app_id}")
        if services_by_id[app_id].get("external_connection_enabled") is not False:
            raise RuntimeError(f"Integration Bus service {app_id} enabled an external connection")

        profile = request_json(base_url, "GET", f"/api/v1/integrations/apps/{app_id}", token=token).payload
        assert_field(profile, "integration_status", "prepared_for_discovery", app_id)
        assert_field(profile, "external_connection_enabled", False, app_id)

        discovery = request_json(base_url, "GET", f"/api/v1/integrations/apps/{app_id}/discovery", token=token).payload
        assert_field(discovery, "external_connection_enabled", False, f"{app_id} discovery")
        assert_field(discovery, "contract_id", contract_id, f"{app_id} discovery")

        query = urlencode({"app_id": app_id})
        contracts = request_json(base_url, "GET", f"/api/v1/contracts?{query}", token=token).payload
        if not any(item.get("id") == contract_id for item in contracts if isinstance(item, dict)):
            raise RuntimeError(f"Contract {contract_id} missing in production")

        event_type = f"platform.{app_id}.discovery.completed"
        if event_type not in event_ids:
            raise RuntimeError(f"Event catalog missing {event_type}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate authenticated Block 3 production state.")
    parser.add_argument("--base-url", default=os.environ.get("ECOSYSTEM_PRODUCTION_BASE_URL", DEFAULT_BASE_URL))
    parser.add_argument("--expected-commit", default=os.environ.get("ECOSYSTEM_EXPECTED_COMMIT", ""))
    args = parser.parse_args()

    email = env_required("CONTROL_CENTER_ADMIN_EMAIL")
    password = env_required("CONTROL_CENTER_ADMIN_PASSWORD")
    base_url = args.base_url.rstrip("/")

    for path in ["/", "/health", "/readiness", "/runtime/status", "/version"]:
        request_json(base_url, "GET", path)
        print(f":: {path} PASS")

    version = request_json(base_url, "GET", "/version").payload
    commit = str(version.get("commit", ""))
    if args.expected_commit and commit != args.expected_commit:
        raise RuntimeError(f"/version expected commit {args.expected_commit}, got {commit}")
    print(f":: production commit {commit or 'unknown'} PASS")

    runtime = request_json(base_url, "GET", "/runtime/status").payload
    database = runtime.get("database", {})
    if database.get("backend") != "postgresql" or database.get("persistent") is not True:
        raise RuntimeError(f"Production database is not persistent PostgreSQL: {database}")
    print(":: production database postgresql persistent PASS")

    login = request_json(
        base_url,
        "POST",
        "/api/v1/auth/login",
        body={"email": email, "password": password},
    ).payload
    token = str(login.get("token") or "")
    if not token.startswith("ccs_"):
        raise RuntimeError("Login did not return a Control Center session token")
    print(":: /api/v1/auth/login PASS")

    me = request_json(base_url, "GET", "/api/v1/auth/me", token=token).payload
    if str(me.get("email", "")).lower() != email.lower():
        raise RuntimeError("/api/v1/auth/me returned a different user")
    print(":: /api/v1/auth/me PASS")

    protected_paths = [
        "/api/v1/control-center",
        "/api/v1/control-center/apps",
        "/api/v1/governance",
        "/api/v1/governance/integration-gates",
        "/api/v1/integration-bus/status",
        "/api/v1/integration-bus/services",
        "/api/v1/contracts/status",
        "/api/v1/contracts",
        "/api/v1/audit",
        "/api/v1/observability/status",
    ]
    for path in protected_paths:
        request_json(base_url, "GET", path, token=token)
        print(f":: {path} authenticated PASS")

    assert_block3_discovery(base_url, token)
    print(":: Block 3 discovery profiles PASS")
    print(":: production authenticated validation PASS")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f":: production authenticated validation BLOCKED: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
