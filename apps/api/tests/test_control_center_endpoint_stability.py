import json

from fastapi.testclient import TestClient

from app.core.database import connect, sql_placeholder
from app.main import app
from app.schemas.auth import ControlCenterRole
from app.services import cerebro as cerebro_service
from app.services import product_readiness as product_readiness_service
from app.services import publishing as publishing_service
from app.services import revenue as revenue_service
from auth_helpers import auth_headers


client = TestClient(app)
CEO_HEADERS = auth_headers(client, ControlCenterRole.ceo)


CONTROL_CENTER_GET_ENDPOINTS = [
    "/api/v1/auth/me",
    "/api/v1/control-center",
    "/api/v1/control-center/apps",
    "/api/v1/governance/auth-boundary?role_id=ceo",
    "/api/v1/cerebro/status",
    "/api/v1/cerebro/chief-of-staff/status",
    "/api/v1/cerebro/goals",
    "/api/v1/cerebro/missions",
    "/api/v1/cerebro/alerts",
    "/api/v1/cerebro/revenue",
    "/api/v1/cerebro/approval-requests",
    "/api/v1/cerebro/checkpoints/morning",
    "/api/v1/cerebro/checkpoints/midday",
    "/api/v1/cerebro/checkpoints/evening",
    "/api/v1/departments",
    "/api/v1/departments/audits",
    "/api/v1/revenue/status",
    "/api/v1/revenue/goals",
    "/api/v1/revenue/opportunities",
    "/api/v1/revenue/approval-requests",
    "/api/v1/revenue/department-contribution",
    "/api/v1/revenue/daily-report",
    "/api/v1/revenue/sprint/status",
    "/api/v1/revenue/sprint/routes",
    "/api/v1/revenue/sprint/missions",
    "/api/v1/revenue/sprint/daily",
    "/api/v1/revenue/sprint/risks",
    "/api/v1/revenue/sprint/approval-needed",
    "/api/v1/arsenal/status",
    "/api/v1/arsenal/catalog",
    "/api/v1/arsenal/categories",
    "/api/v1/arsenal/risks",
    "/api/v1/arsenal/readiness",
    "/api/v1/missions",
    "/api/v1/missions/active",
    "/api/v1/missions/reports/daily",
    "/api/v1/workday/status",
    "/api/v1/workday/morning",
    "/api/v1/workday/midday",
    "/api/v1/workday/evening",
    "/api/v1/workday/alerts",
    "/api/v1/workday/priority-changes",
    "/api/v1/workday/report",
    "/api/v1/upgrades/status",
    "/api/v1/upgrades/packages",
    "/api/v1/publishing/status",
    "/api/v1/publishing/channels",
    "/api/v1/publishing/calendar",
    "/api/v1/publishing/content",
    "/api/v1/publishing/growth",
    "/api/v1/product-readiness/status",
    "/api/v1/product-readiness/dcft",
    "/api/v1/product-readiness/sentinela",
    "/api/v1/product-readiness/gaps",
    "/api/v1/product-readiness/marketing-package",
    "/api/v1/ceo/daily-center",
    "/api/v1/ceo/morning",
    "/api/v1/ceo/evening",
    "/api/v1/ceo/decisions",
    "/api/v1/integration-bus/status",
    "/api/v1/integration-bus/routes",
    "/api/v1/integration-bus/prepared-routes",
    "/api/v1/contracts",
    "/api/v1/contracts/status",
    "/api/v1/auditoria/status",
    "/api/v1/auditoria/reviews",
    "/api/v1/auditoria/queue",
    "/api/v1/nube/status",
    "/api/v1/nube/projects",
    "/api/v1/nube/deployments",
    "/api/v1/nube/health-checks",
    "/api/v1/nube/risks",
    "/api/v1/nube/costs",
    "/api/v1/governance",
    "/api/v1/governance/reports",
    "/api/v1/governance/decisions",
    "/api/v1/governance/approvals",
    "/api/v1/governance/integration-gates",
    "/api/v1/governance/policies",
    "/api/v1/governance/risks",
    "/api/v1/governance/audit",
    "/api/v1/audit",
    "/api/v1/observability/status",
]


def insert_payload(table_name: str, item_id: str, raw_payload: object) -> None:
    placeholder = sql_placeholder()
    payload_json = raw_payload if isinstance(raw_payload, str) else json.dumps(raw_payload)
    with connect() as connection:
        connection.execute(
            f"""
            INSERT INTO {table_name} (id, payload_json, created_at, updated_at)
            VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder})
            ON CONFLICT(id) DO UPDATE SET
                payload_json = excluded.payload_json,
                updated_at = excluded.updated_at
            """,
            (item_id, payload_json, "2026-06-09T00:00:00Z", "2026-06-09T00:00:00Z"),
        )
        connection.commit()


def test_control_center_endpoints_do_not_return_500_with_auth() -> None:
    for endpoint in CONTROL_CENTER_GET_ENDPOINTS:
        response = client.get(endpoint, headers=CEO_HEADERS)
        assert response.status_code == 200, endpoint


def test_protected_endpoints_still_require_auth() -> None:
    for endpoint in [
        "/api/v1/cerebro/chief-of-staff/status",
        "/api/v1/revenue/sprint/approval-needed",
        "/api/v1/publishing/status",
        "/api/v1/product-readiness/status",
        "/api/v1/control-center",
    ]:
        response = client.get(endpoint)
        assert response.status_code == 401, endpoint


def test_chief_of_staff_status_survives_missing_and_legacy_payloads() -> None:
    cerebro_service.ensure_cerebro_schema()
    insert_payload(cerebro_service.CEREBRO_MISSIONS_TABLE, "r8_bad_mission", "{bad-json")
    insert_payload(cerebro_service.CEREBRO_ALERTS_TABLE, "r8_incomplete_alert", {"id": "only_id"})
    insert_payload(cerebro_service.CEREBRO_APPROVAL_REQUESTS_TABLE, "r8_bad_approval", {"id": "only_id"})

    response = client.get("/api/v1/cerebro/chief-of-staff/status", headers=CEO_HEADERS)

    assert response.status_code == 200
    payload = response.json()
    assert payload["motto"] == "El tiempo es dinero"
    assert payload["external_connection_enabled"] is False
    assert payload["runtime_connected"] is False
    assert payload["sunat_enabled"] is False


def test_revenue_sprint_approval_needed_safe_fallback_does_not_invent_money() -> None:
    revenue_service.ensure_revenue_schema()
    insert_payload(revenue_service.REVENUE_SPRINT_ROUTES_TABLE, "r8_bad_route", {"id": "only_id"})

    response = client.get("/api/v1/revenue/sprint/approval-needed", headers=CEO_HEADERS)

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["count"] == len(payload["items"])
    assert payload["real_revenue_confirmed"] is False
    assert payload["payment_connected"] is False


def test_publishing_and_product_readiness_ignore_bad_rows_without_false_claims() -> None:
    publishing_service.ensure_publishing_schema()
    insert_payload(publishing_service.CONTENT_ITEMS_TABLE, "r8_bad_content", {"id": "only_id"})
    product_readiness_service.ensure_product_readiness_schema()
    insert_payload(product_readiness_service.PRODUCT_READINESS_GAPS_TABLE, "r8_bad_gap", "{bad-json")

    publishing = client.get("/api/v1/publishing/status", headers=CEO_HEADERS)
    readiness = client.get("/api/v1/product-readiness/status", headers=CEO_HEADERS)

    assert publishing.status_code == 200
    assert readiness.status_code == 200
    publishing_payload = publishing.json()
    readiness_payload = readiness.json()
    assert publishing_payload["paid_campaigns_launched"] == 0
    assert publishing_payload["payment_connected"] is False
    assert readiness_payload["marketing_owner"] == "MARKETING"
    assert readiness_payload["products_with_own_sales_goal"] == 0
