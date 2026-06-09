from fastapi.testclient import TestClient
import pytest

from app.main import app
from app.schemas.auth import ControlCenterRole
from auth_helpers import auth_headers


client = TestClient(app)
CEO_HEADERS = auth_headers(client, ControlCenterRole.ceo)
OPERATOR_HEADERS = auth_headers(client, ControlCenterRole.operator)
AUDITOR_HEADERS = auth_headers(client, ControlCenterRole.auditor)
SERVICE_HEADERS = auth_headers(client, ControlCenterRole.service)


def create_review(
    *,
    object_type: str = "cerebro_task",
    reference: str = "cerebro-task-test",
    source: str = "test-suite",
    headers: dict[str, str] = CEO_HEADERS,
) -> dict:
    response = client.post(
        "/api/v1/auditoria/reviews",
        json={
            "object_type": object_type,
            "reference": reference,
            "source": source,
            "priority": "p1",
            "criteria": ["functional_quality", "security", "ceo_standard"],
            "observations": ["Review created by test suite."],
        },
        headers=headers,
    )
    assert response.status_code == 201
    return response.json()


@pytest.mark.parametrize(
    ("method", "path"),
    [
        ("GET", "/api/v1/auditoria/status"),
        ("GET", "/api/v1/auditoria/reviews"),
        ("POST", "/api/v1/auditoria/reviews"),
        ("GET", "/api/v1/auditoria/queue"),
    ],
)
def test_auditoria_endpoints_require_auth(method: str, path: str) -> None:
    unauthenticated = TestClient(app)
    if method == "POST":
        response = unauthenticated.post(
            path,
            json={
                "object_type": "cerebro_task",
                "reference": "missing-auth",
                "source": "test",
            },
        )
    else:
        response = unauthenticated.get(path)

    assert response.status_code == 401


def test_ceo_can_create_review_and_it_appears_in_queue() -> None:
    review = create_review()
    detail = client.get(f"/api/v1/auditoria/reviews/{review['id']}", headers=CEO_HEADERS)
    queue = client.get("/api/v1/auditoria/queue", headers=CEO_HEADERS)
    status = client.get("/api/v1/auditoria/status", headers=CEO_HEADERS)

    assert review["status"] == "pending_review"
    assert review["external_connection_enabled"] is False
    assert review["runtime_connected"] is False
    assert detail.status_code == 200
    assert detail.json()["id"] == review["id"]
    assert any(item["id"] == review["id"] for item in queue.json())
    assert status.status_code == 200
    assert status.json()["status"] == "auditoria_operational_internal"


def test_auditor_can_decide_and_operator_cannot_approve() -> None:
    review = create_review(reference="operator-approval-boundary")
    unauthorized = client.post(
        f"/api/v1/auditoria/reviews/{review['id']}/decision",
        json={"decision": "approved", "auditor": "operator"},
        headers=OPERATOR_HEADERS,
    )
    approved = client.post(
        f"/api/v1/auditoria/reviews/{review['id']}/decision",
        json={
            "decision": "approved",
            "auditor": "auditoria-test",
            "observations": ["Quality and safety are acceptable."],
            "criteria_results": {"security": "pass"},
        },
        headers=AUDITOR_HEADERS,
    )

    assert unauthorized.status_code == 403
    assert unauthorized.json()["detail"]["error"] == "auditoria_role_not_authorized"
    assert approved.status_code == 200
    assert approved.json()["status"] == "approved"
    assert approved.json()["decision"] == "approved"
    assert approved.json()["auditor"] == "auditoria-test"


def test_service_user_cannot_create_or_decide_reviews() -> None:
    create_attempt = client.post(
        "/api/v1/auditoria/reviews",
        json={
            "object_type": "risk",
            "reference": "service-forbidden",
            "source": "service",
        },
        headers=SERVICE_HEADERS,
    )
    review = create_review(reference="service-decision-forbidden")
    decision_attempt = client.post(
        f"/api/v1/auditoria/reviews/{review['id']}/decision",
        json={"decision": "approved", "auditor": "service"},
        headers=SERVICE_HEADERS,
    )

    assert create_attempt.status_code == 403
    assert decision_attempt.status_code == 403


def test_cerebro_can_send_task_to_auditoria_through_internal_bus() -> None:
    response = client.post(
        "/api/v1/cerebro/tasks",
        json={
            "title": "Revisar cabina humana",
            "description": "AUDITORIA debe revisar calidad, riesgo y claridad.",
            "destination": "AUDITORIA",
            "priority": "p1",
        },
        headers=CEO_HEADERS,
    )
    task = response.json()
    review_id = task["handler_result"]["review_id"]
    review = client.get(f"/api/v1/auditoria/reviews/{review_id}", headers=CEO_HEADERS)
    bus_audit = client.get("/api/v1/integration-bus/audit", headers=CEO_HEADERS)

    assert response.status_code == 201
    assert task["destination"] == "auditor"
    assert task["route_dispatched"] is True
    assert task["handler_result"]["result"] == "audit_review_created"
    assert review.status_code == 200
    assert review.json()["reference"] == task["id"]
    assert review.json()["source"] == "cerebro"
    assert any(item["action"] == "audit_review_created" for item in bus_audit.json())


def test_auditoria_can_block_route_and_approve_internal_route_review() -> None:
    blocked_review = create_review(
        object_type="bus_route",
        reference="cerebro_to_nube_future",
    )
    blocked = client.post(
        f"/api/v1/auditoria/reviews/{blocked_review['id']}/decision",
        json={
            "decision": "blocked",
            "auditor": "auditoria-test",
            "blockages": ["NUBE local remains documentary; no deployment is executed."],
        },
        headers=AUDITOR_HEADERS,
    )
    approved_review = create_review(
        object_type="bus_route",
        reference="cerebro_to_pluma_future",
    )
    approved = client.post(
        f"/api/v1/auditoria/reviews/{approved_review['id']}/decision",
        json={
            "decision": "approved",
            "auditor": "auditoria-test",
            "observations": ["Internal prepared route can remain available."],
        },
        headers=AUDITOR_HEADERS,
    )
    bus_audit = client.get("/api/v1/integration-bus/audit", headers=CEO_HEADERS)

    assert blocked.status_code == 200
    assert blocked.json()["status"] == "blocked"
    assert approved.status_code == 200
    assert approved.json()["status"] == "approved"
    assert any(item["action"] == "audit_blocked" for item in bus_audit.json())
    assert any(item["action"] == "audit_approved" for item in bus_audit.json())


@pytest.mark.parametrize(
    "reference",
    [
        "dcft",
        "sentinela",
        "arsenal",
        "cerebro_to_dcft_future",
        "cerebro_to_sentinela_future",
        "cerebro_to_arsenal_future",
    ],
)
def test_auditoria_cannot_unlock_protected_products_or_routes(reference: str) -> None:
    review = create_review(
        object_type="protected_product",
        reference=reference,
    )
    response = client.post(
        f"/api/v1/auditoria/reviews/{review['id']}/decision",
        json={
            "decision": "approved",
            "auditor": "auditoria-test",
            "observations": ["Attempted protected unlock."],
        },
        headers=AUDITOR_HEADERS,
    )
    detail = client.get(f"/api/v1/auditoria/reviews/{review['id']}", headers=CEO_HEADERS)

    assert response.status_code == 403
    assert response.json()["detail"]["error"] == "protected_product_cannot_be_unlocked_by_auditoria"
    assert detail.json()["status"] == "blocked"
    assert detail.json()["external_connection_enabled"] is False
    assert detail.json()["runtime_connected"] is False


def test_auditoria_audit_trail_has_no_secrets_or_tokens() -> None:
    review = create_review(reference="audit-trail-clean-scan")
    decided = client.post(
        f"/api/v1/auditoria/reviews/{review['id']}/decision",
        json={
            "decision": "observed",
            "auditor": "auditoria-test",
            "observations": ["Needs clearer CEO wording."],
        },
        headers=AUDITOR_HEADERS,
    ).json()
    audit_event_id = decided["audit_event_ids"][-1]
    event = client.get(f"/api/v1/audit/events/{audit_event_id}", headers=CEO_HEADERS).json()
    serialized = str(event).lower()

    assert event["source"] == "auditoria.operational_judge"
    assert "password" not in serialized
    assert "bearer" not in serialized
    assert "token" not in serialized
    assert "secret" not in serialized
