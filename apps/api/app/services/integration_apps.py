from datetime import UTC, datetime
from functools import lru_cache
import json
import os
from pathlib import Path

from app.schemas.integration_apps import IntegrationAppDiscovery, IntegrationAppProfile

DATA_PATH = Path(__file__).resolve().parents[1] / "data"
INTEGRATION_APP_PROFILES_PATH = DATA_PATH / "integration_app_profiles.json"

LOCAL_DISCOVERY_PATHS: dict[str, tuple[Path, ...]] = {
    "hermes": (
        Path(
            "C:/Users/admin/Documents/Codex/2026-05-20/"
            "fase-render-cloud-stabilization-objetivo-inicializar/"
            "hermes-knowledge-core"
        ),
    ),
    "pluma": (
        Path("C:/Users/admin/Desktop/pluma"),
    ),
}


def utc_now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


@lru_cache
def list_integration_app_profiles() -> tuple[IntegrationAppProfile, ...]:
    raw_profiles = json.loads(
        INTEGRATION_APP_PROFILES_PATH.read_text(encoding="utf-8")
    )
    return tuple(IntegrationAppProfile(**item) for item in raw_profiles)


def get_integration_app_profile(app_id: str) -> IntegrationAppProfile | None:
    normalized_id = app_id.strip().lower()
    return next(
        (
            profile
            for profile in list_integration_app_profiles()
            if profile.app_id == normalized_id
        ),
        None,
    )


def configured_repository_path(app_id: str) -> Path | None:
    env_name = f"{app_id.strip().upper()}_KNOWLEDGE_CORE_PATH"
    configured = os.getenv(env_name)
    if configured:
        return Path(configured)

    for candidate in LOCAL_DISCOVERY_PATHS.get(app_id.strip().lower(), ()):
        if candidate.exists():
            return candidate

    return None


def discover_integration_app(app_id: str) -> IntegrationAppDiscovery | None:
    profile = get_integration_app_profile(app_id)
    if profile is None:
        return None

    repository_path = configured_repository_path(profile.app_id)
    repository_detected = bool(repository_path and repository_path.exists())
    evidence_found: list[str] = []
    missing_evidence: list[str] = []
    evidence_source = "none"

    if repository_path and repository_path.exists():
        for relative_file in profile.evidence_files:
            if (repository_path / relative_file).exists():
                evidence_found.append(relative_file)
            else:
                missing_evidence.append(relative_file)
        evidence_source = "runtime_repository"
    elif profile.evidence_files_verified:
        verified_files = set(profile.evidence_files_verified)
        evidence_found = [
            relative_file
            for relative_file in profile.evidence_files
            if relative_file in verified_files
        ]
        missing_evidence = [
            relative_file
            for relative_file in profile.evidence_files
            if relative_file not in verified_files
        ]
        evidence_source = "versioned_local_discovery_snapshot"
    else:
        missing_evidence = list(profile.evidence_files)

    blockers = list(profile.blockers)
    if not repository_detected and not evidence_found:
        blockers.append(
            "Repository path is not available in this runtime; configure "
            f"{profile.app_id.upper()}_KNOWLEDGE_CORE_PATH for local discovery."
        )

    health_status = (
        "local_evidence_found"
        if repository_detected and evidence_found
        else "local_evidence_snapshot_found"
        if evidence_found and not missing_evidence
        else "blocked_missing_repository_evidence"
    )

    return IntegrationAppDiscovery(
        app_id=profile.app_id,
        app_name=profile.app_name,
        integration_status=profile.integration_status,
        contract_id=profile.contract_id,
        repository_detected=repository_detected,
        repository_path=str(repository_path) if repository_detected and repository_path else None,
        evidence_source=evidence_source,
        evidence_repository_commit=profile.evidence_repository_commit,
        evidence_files_expected=profile.evidence_files,
        evidence_files_found=evidence_found,
        missing_evidence_files=missing_evidence,
        expected_capabilities=profile.expected_capabilities,
        health_status=health_status,
        blockers=blockers,
        external_connection_enabled=profile.external_connection_enabled,
        discovered_at=utc_now(),
    )
