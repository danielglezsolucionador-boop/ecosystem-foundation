from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app
from app.schemas.auth import ControlCenterRole
from app.services.arsenal import ArsenalError, get_resource_for_office
from auth_helpers import auth_headers


client = TestClient(app)
CEO_HEADERS = auth_headers(client, ControlCenterRole.ceo)


def resource_payload(**overrides):
    resource_id = f"arsenal-test-resource-{uuid4()}"
    payload = {
        "id": resource_id,
        "name": f"Versioned Internal Tool {uuid4()}",
        "type": "TOOL",
        "category": "automatizaciones",
        "version": "v1",
        "status": "active",
        "owner_office": "FORJA",
        "allowed_offices": ["CEREBRO", "FORJA", "AUDITORIA"],
        "location": f"internal://arsenal/tests/{resource_id}",
        "runtime": "metadata_only_test_runtime",
        "description": (
            "Recurso tecnico interno registrado como metadata de ARSENAL CORE."
        ),
        "input_schema": {"input": "object"},
        "output_schema": {"output": "object"},
        "replaces": None,
        "notes": "Test resource without external runtime.",
        "available_for_sombra": False,
        "readiness": "testing",
    }
    payload.update(overrides)
    return payload


def test_arsenal_core_seeds_initial_resources_without_secrets() -> None:
    response = client.get("/api/v1/arsenal/resources", headers=CEO_HEADERS)

    assert response.status_code == 200
    resources = response.json()
    by_name = {resource["name"]: resource for resource in resources}
    assert by_name["OpenAI API provider"]["readiness"] == "pending_secret"
    assert (
        by_name["LinkedIn OAuth connector"]["readiness"]
        == "pending_credentials"
    )
    assert by_name["Header/CSP Auditor"]["readiness"] == "planned"
    assert by_name["Report Normalizer"]["readiness"] == "planned"
    assert by_name["Sombra Toolbelt"]["readiness"] == "external_registered"
    assert by_name["Centinela Defensive Rules"]["readiness"] == "planned"
    assert all(resource["secrets_stored"] is False for resource in resources)
    assert "sk-" not in response.text


def test_register_resource_and_query_by_office_category_status() -> None:
    payload = resource_payload()

    created = client.post(
        "/api/v1/arsenal/resources",
        headers=CEO_HEADERS,
        json=payload,
    )
    queried = client.get(
        "/api/v1/arsenal/resources",
        headers=CEO_HEADERS,
        params={
            "name": payload["name"],
            "type": "TOOL",
            "office": "FORJA",
            "category": "automatizaciones",
            "status": "active",
            "active_only": "true",
        },
    )

    assert created.status_code == 201
    assert created.json()["id"] == payload["id"]
    assert queried.status_code == 200
    assert payload["id"] in {
        resource["id"] for resource in queried.json()
    }


def test_cerebro_can_consult_all_core_resources() -> None:
    resource = get_resource_for_office("CEREBRO", "OpenAI API provider")

    assert resource.name == "OpenAI API provider"
    assert resource.readiness == "pending_secret"
    assert resource.secrets_stored is False


def test_sombra_only_receives_authorized_resources() -> None:
    response = client.get(
        "/api/v1/arsenal/resources",
        headers=CEO_HEADERS,
        params={"office": "SOMBRA"},
    )
    toolbelt = get_resource_for_office("SOMBRA", "Sombra Toolbelt")

    assert response.status_code == 200
    resources = response.json()
    assert resources
    assert all(resource["available_for_sombra"] is True for resource in resources)
    assert toolbelt.name == "Sombra Toolbelt"
    assert toolbelt.available_for_sombra is True


def test_sombra_cannot_use_non_authorized_editorial_resource() -> None:
    response = client.get(
        "/api/v1/arsenal/resources/arsenal-tool-report-normalizer",
        headers=CEO_HEADERS,
        params={"office": "SOMBRA"},
    )

    assert response.status_code == 403
    assert (
        response.json()["detail"]["error"]
        == "arsenal_resource_not_authorized_for_office"
    )


def test_replace_marks_old_version_and_blocks_obsolete_usage() -> None:
    old_payload = resource_payload(
        name=f"Replaceable Tool {uuid4()}",
        version="v1",
    )
    old = client.post(
        "/api/v1/arsenal/resources",
        headers=CEO_HEADERS,
        json=old_payload,
    )
    assert old.status_code == 201

    new_payload = resource_payload(
        id=f"{old_payload['id']}-v2",
        name=old_payload["name"],
        version="v2",
    )
    replacement = client.post(
        f"/api/v1/arsenal/resources/{old_payload['id']}/replace",
        headers=CEO_HEADERS,
        json=new_payload,
    )
    old_after = client.get(
        f"/api/v1/arsenal/resources/{old_payload['id']}",
        headers=CEO_HEADERS,
    )

    assert replacement.status_code == 201
    assert replacement.json()["status"] == "active"
    assert replacement.json()["replaces"] == old_payload["id"]
    assert old_after.status_code == 200
    assert old_after.json()["status"] == "replaced"
    assert old_after.json()["replaced_by"] == new_payload["id"]

    try:
        get_resource_for_office("CEREBRO", old_payload["id"])
    except ArsenalError as error:
        assert error.status_code == 409
        assert error.detail["error"] == "arsenal_resource_obsolete"
        assert error.detail["active_resource_id"] == new_payload["id"]
    else:
        raise AssertionError("obsolete ARSENAL resource returned for CEREBRO")


def test_disable_resource_removes_it_from_office_usage() -> None:
    payload = resource_payload()
    created = client.post(
        "/api/v1/arsenal/resources",
        headers=CEO_HEADERS,
        json=payload,
    )
    disabled = client.post(
        f"/api/v1/arsenal/resources/{payload['id']}/disable",
        headers=CEO_HEADERS,
    )
    office_resources = client.get(
        "/api/v1/arsenal/resources",
        headers=CEO_HEADERS,
        params={"office": "FORJA"},
    )

    assert created.status_code == 201
    assert disabled.status_code == 200
    assert disabled.json()["status"] == "disabled"
    assert payload["id"] not in {
        resource["id"] for resource in office_resources.json()
    }


def test_arsenal_core_rejects_secret_fields() -> None:
    response = client.post(
        "/api/v1/arsenal/resources",
        headers=CEO_HEADERS,
        json=resource_payload(input_schema={"api_key": "placeholder-only"}),
    )

    assert response.status_code == 400
    assert (
        response.json()["detail"]["error"]
        == "arsenal_secret_payload_rejected"
    )
