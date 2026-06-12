from pathlib import Path
import subprocess

from fastapi.testclient import TestClient

from app.main import app
from app.schemas.auth import ControlCenterRole
from auth_helpers import auth_headers


client = TestClient(app)
CEO_HEADERS = auth_headers(client, ControlCenterRole.ceo)
ROOT = Path(__file__).resolve().parents[3]


PHASE_S_DOCS = [
    "REAL_WORLD_CONNECTION_READINESS_MODEL.md",
    "REAL_WORLD_CONNECTIONS_REGISTER.md",
    "PHASE_S1_REAL_WORLD_CONNECTION_READINESS_REPORT.md",
    "SOCIAL_ACCOUNTS_IDENTITY_MAP_MODEL.md",
    "SOCIAL_ACCOUNTS_IDENTITY_REGISTER.md",
    "PHASE_S2_SOCIAL_ACCOUNTS_IDENTITY_MAP_REPORT.md",
    "PUBLISHING_ORGANIC_PREPARED_PIPELINE_MODEL.md",
    "PUBLISHING_PREPARED_CONTENT_REGISTER.md",
    "PHASE_S3_PUBLISHING_ORGANIC_PREPARED_PIPELINE_REPORT.md",
    "MARKETING_PAID_CAMPAIGN_APPROVAL_GATE_MODEL.md",
    "MARKETING_CAMPAIGN_APPROVAL_REGISTER.md",
    "PHASE_S4_MARKETING_PAID_CAMPAIGN_APPROVAL_GATE_REPORT.md",
    "ECOMMERCE_AMAZON_READINESS_MODEL.md",
    "ECOMMERCE_AMAZON_READINESS_REGISTER.md",
    "PHASE_S5_ECOMMERCE_AMAZON_READINESS_REPORT.md",
    "DCFT_SENTINELA_COMMERCIAL_CONNECTION_READINESS_MODEL.md",
    "DCFT_SENTINELA_COMMERCIAL_READINESS_REGISTER.md",
    "PHASE_S6_DCFT_SENTINELA_COMMERCIAL_READINESS_REPORT.md",
    "ANALYTICS_METRICS_REVENUE_TRACKING_READINESS_MODEL.md",
    "ANALYTICS_METRICS_READINESS_REGISTER.md",
    "PHASE_S7_ANALYTICS_METRICS_REVENUE_TRACKING_READINESS_REPORT.md",
    "REAL_WORLD_EXECUTION_QUEUE_MODEL.md",
    "REAL_WORLD_EXECUTION_QUEUE_REGISTER.md",
    "PHASE_S8_REAL_WORLD_EXECUTION_QUEUE_REPORT.md",
    "PHASE_S_COVERAGE_VERIFICATION_REPORT.md",
    "PHASE_S_TOTAL_AUDIT_REPORT.md",
]

PHASE_S_ENDPOINTS = [
    "/api/v1/real-world/status",
    "/api/v1/real-world/connections",
    "/api/v1/real-world/approval-needed",
    "/api/v1/real-world/risks",
    "/api/v1/social-identity/status",
    "/api/v1/social-identity/accounts",
    "/api/v1/social-identity/approval-needed",
    "/api/v1/social-identity/risks",
    "/api/v1/publishing-prepared/status",
    "/api/v1/publishing-prepared/calendar",
    "/api/v1/publishing-prepared/content",
    "/api/v1/publishing-prepared/blocked",
    "/api/v1/marketing-approval/status",
    "/api/v1/marketing-approval/campaigns",
    "/api/v1/marketing-approval/approval-needed",
    "/api/v1/marketing-approval/risks",
    "/api/v1/ecommerce-readiness/status",
    "/api/v1/ecommerce-readiness/opportunities",
    "/api/v1/ecommerce-readiness/approval-needed",
    "/api/v1/amazon-readiness/status",
    "/api/v1/amazon-readiness/opportunities",
    "/api/v1/amazon-readiness/risks",
    "/api/v1/commercial-readiness/status",
    "/api/v1/commercial-readiness/dcft",
    "/api/v1/commercial-readiness/sentinela",
    "/api/v1/commercial-readiness/marketing-package",
    "/api/v1/commercial-readiness/approval-needed",
    "/api/v1/analytics-readiness/status",
    "/api/v1/analytics-readiness/metrics",
    "/api/v1/analytics-readiness/sources",
    "/api/v1/analytics-readiness/approval-needed",
    "/api/v1/analytics-readiness/risks",
    "/api/v1/real-world-execution/status",
    "/api/v1/real-world-execution/queue",
    "/api/v1/real-world-execution/approval-needed",
]


def assert_false(payload: dict, *keys: str) -> None:
    for key in keys:
        if key in payload:
            assert payload[key] is False, f"{key} must remain false"


def test_phase_s_total_audit_documents_exist_and_are_nonempty() -> None:
    docs_dir = ROOT / "docs" / "ecosystem" / "execution"
    for filename in PHASE_S_DOCS:
        path = docs_dir / filename
        assert path.exists(), filename
        assert path.stat().st_size > 300, filename


def test_phase_s_total_audit_endpoints_require_auth() -> None:
    for path in PHASE_S_ENDPOINTS:
        response = client.get(path)
        assert response.status_code == 401, path


def test_phase_s_total_audit_all_statuses_are_safe_prepared_or_blocked() -> None:
    status_paths = [
        "/api/v1/real-world/status",
        "/api/v1/social-identity/status",
        "/api/v1/publishing-prepared/status",
        "/api/v1/marketing-approval/status",
        "/api/v1/ecommerce-readiness/status",
        "/api/v1/amazon-readiness/status",
        "/api/v1/commercial-readiness/status",
        "/api/v1/analytics-readiness/status",
        "/api/v1/real-world-execution/status",
    ]

    for path in status_paths:
        response = client.get(path, headers=CEO_HEADERS)
        assert response.status_code == 200, path
        payload = response.json()
        assert_false(
            payload,
            "external_connection_enabled",
            "runtime_connected",
            "real_publication_enabled",
            "paid_campaign_launched",
            "payment_connected",
            "sunat_enabled",
            "secrets_stored",
            "credentials_stored",
            "account_connected",
            "store_created",
            "inventory_purchased",
            "amazon_seller_connected",
            "prohibited_scraping_enabled",
            "metrics_invented",
            "margin_invented",
            "claims_invented",
            "actual_sales_confirmed",
            "real_sales_confirmed",
            "api_execution_confirmed",
            "manual_execution_confirmed",
        )

    real_world = client.get("/api/v1/real-world/status", headers=CEO_HEADERS).json()
    assert real_world["connected"] == 0
    assert real_world["needs_paid_approval"] >= 1
    assert real_world["needs_credentials"] >= 1

    publishing = client.get("/api/v1/publishing-prepared/status", headers=CEO_HEADERS).json()
    assert publishing["published_items"] == 0
    assert publishing["status"] == "prepared_local"

    marketing = client.get("/api/v1/marketing-approval/status", headers=CEO_HEADERS).json()
    assert marketing["paid_campaigns_launched"] == 0
    assert marketing["budget_spent"] == 0
    assert marketing["roi_confirmed"] is False

    ecommerce = client.get("/api/v1/ecommerce-readiness/status", headers=CEO_HEADERS).json()
    assert ecommerce["actual_revenue_usd"] == 0
    assert ecommerce["payment_connected"] is False

    execution = client.get("/api/v1/real-world-execution/status", headers=CEO_HEADERS).json()
    assert execution["approval_needed"] >= 1
    assert execution["money_needed"] >= 1
    assert execution["credentials_needed"] >= 1


def test_phase_s_total_audit_control_center_contains_all_s_panels() -> None:
    html = client.get("/control-center")
    js = client.get("/control-center/assets/app.js")

    assert html.status_code == 200
    assert js.status_code == 200

    for panel_id in [
        "real-world-connections",
        "social-identity-map",
        "publishing-prepared",
        "marketing-approval-gate",
        "ecommerce-amazon-readiness",
        "commercial-readiness",
        "analytics-readiness",
        "real-world-execution-queue",
    ]:
        assert panel_id in html.text

    for endpoint in PHASE_S_ENDPOINTS:
        assert endpoint in js.text

    normalized = f"{html.text}\n{js.text}".lower()
    forbidden_claims = [
        "sunat real activado",
        "campana pagada lanzada",
        "cuenta externa creada",
        "publicacion real habilitada",
        "payment_connected=true",
        "secrets_stored=true",
        "credentials_stored=true",
        "metrics_invented=true",
        "paid_campaign_launched=true",
        "external_connection_enabled=true",
    ]
    for claim in forbidden_claims:
        assert claim not in normalized


def test_phase_s_total_audit_backup_is_not_tracked_and_sombra_state_is_current() -> None:
    sombra_result = subprocess.run(
        ["git", "ls-files", "apps/sombra"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )
    backup_result = subprocess.run(
        ["git", "ls-files", "backup"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )
    staged_result = subprocess.run(
        ["git", "diff", "--cached", "--name-only"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )
    staged_paths = staged_result.stdout.splitlines()

    # apps/sombra was later promoted into the repository by SOMBRA production commits.
    # S9 no longer requires apps/sombra to be untracked; backup/ must remain untracked.
    assert isinstance(sombra_result.stdout, str)
    assert backup_result.stdout.strip() == ""
    assert not any(path == "apps/sombra" or path.startswith("apps/sombra/") for path in staged_paths)
    assert not any(path == "backup" or path.startswith("backup/") for path in staged_paths)
