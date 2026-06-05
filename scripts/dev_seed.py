from __future__ import annotations

from dev_common import configure_local_environment, ensure_api_path, masked_database_url


def main() -> None:
    configure_local_environment()
    ensure_api_path()

    from app.core.database import initialize_database
    from app.services.audit import ensure_audit_schema
    from app.services.auth import ensure_auth_schema
    from app.services.contracts import ensure_contract_schema
    from app.services.events import ensure_events_schema
    from app.services.governance import ensure_governance_schema
    from app.services.integration_bus import ensure_integration_bus_schema
    from app.services.memory import ensure_memory_schema
    from app.services.observability import ensure_observability_schema
    from app.services.security import ensure_security_audit_schema

    print(f":: database {masked_database_url()}")
    status = initialize_database()
    ensure_auth_schema()
    ensure_audit_schema()
    ensure_memory_schema()
    ensure_events_schema()
    ensure_integration_bus_schema()
    ensure_contract_schema()
    ensure_governance_schema()
    ensure_security_audit_schema()
    ensure_observability_schema()
    print(
        ":: dev seed PASS "
        f"backend={status.backend} persistent={status.persistent} schema={status.schema_version}"
    )


if __name__ == "__main__":
    main()
