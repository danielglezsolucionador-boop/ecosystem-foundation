from datetime import UTC, datetime
import json
from typing import Any
from uuid import uuid4

from app.core.database import connect, initialize_database, sql_placeholder
from app.schemas.contracts import (
    ContractAuditEvent,
    ContractCompatibilityRequest,
    ContractCompatibilityResult,
    ContractCreate,
    ContractPayloadValidationRequest,
    ContractPayloadValidationResult,
    ContractRecord,
    ContractStatus,
    ContractUpdate,
    ContractVersion,
)
from app.services.app_registry import get_registered_app

CONTRACTS_TABLE = "ecosystem_contracts"
CONTRACT_VERSIONS_TABLE = "ecosystem_contract_versions"
CONTRACT_AUDIT_TABLE = "ecosystem_contract_audit_events"
CONTROLLED_CONTRACT_SEEDS: tuple[dict[str, Any], ...] = (
    {
        "id": "hermes.discovery.v1",
        "app_id": "hermes",
        "name": "Hermes Discovery Contract V1",
        "version": "v1",
        "status": "prepared_for_discovery",
        "schema": {
            "type": "object",
            "required": [
                "app_id",
                "status",
                "repository_detected",
                "external_connection_enabled",
            ],
            "properties": {
                "app_id": {"type": "string"},
                "status": {"type": "string"},
                "repository_detected": {"type": "boolean"},
                "evidence_count": {"type": "integer"},
                "blockers": {"type": "array"},
                "external_connection_enabled": {"type": "boolean"},
            },
        },
        "description": (
            "Controlled Hermes discovery payload. It validates local evidence "
            "shape and keeps runtime connection disabled."
        ),
    },
)


class ContractValidationError(RuntimeError):
    def __init__(self, detail: dict[str, object]) -> None:
        self.detail = detail
        super().__init__(str(detail))


def utc_now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def row_value(row: Any, key: str) -> Any:
    return row[key]


def ensure_contract_schema() -> None:
    initialize_database()

    with connect() as connection:
        connection.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {CONTRACTS_TABLE} (
                id TEXT PRIMARY KEY,
                app_id TEXT NOT NULL,
                name TEXT NOT NULL,
                version TEXT NOT NULL,
                status TEXT NOT NULL,
                schema_json TEXT NOT NULL,
                description TEXT NOT NULL,
                breaking_change_detected INTEGER NOT NULL,
                external_connection_enabled INTEGER NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        connection.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {CONTRACT_VERSIONS_TABLE} (
                id TEXT PRIMARY KEY,
                contract_id TEXT NOT NULL,
                sequence INTEGER NOT NULL,
                action TEXT NOT NULL,
                payload_json TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        connection.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {CONTRACT_AUDIT_TABLE} (
                id TEXT PRIMARY KEY,
                contract_id TEXT NOT NULL,
                action TEXT NOT NULL,
                status TEXT NOT NULL,
                detail TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        seed_controlled_contracts(connection, sql_placeholder())
        connection.commit()


def seed_controlled_contracts(connection: Any, placeholder: str) -> None:
    for seed in CONTROLLED_CONTRACT_SEEDS:
        if get_registered_app(str(seed["app_id"])) is None:
            continue

        existing = connection.execute(
            f"SELECT id FROM {CONTRACTS_TABLE} WHERE id = {placeholder}",
            (seed["id"],),
        ).fetchone()
        if existing:
            continue

        now = utc_now()
        record = ContractRecord(
            id=str(seed["id"]),
            app_id=str(seed["app_id"]),
            name=str(seed["name"]),
            version=str(seed["version"]),
            status=str(seed["status"]),
            contract_schema=seed["schema"],
            description=str(seed["description"]),
            breaking_change_detected=False,
            external_connection_enabled=False,
            created_at=now,
            updated_at=now,
        )
        connection.execute(
            f"""
            INSERT INTO {CONTRACTS_TABLE} (
                id, app_id, name, version, status, schema_json, description,
                breaking_change_detected, external_connection_enabled, created_at, updated_at
            )
            VALUES (
                {placeholder}, {placeholder}, {placeholder}, {placeholder},
                {placeholder}, {placeholder}, {placeholder}, {placeholder},
                {placeholder}, {placeholder}, {placeholder}
            )
            """,
            (
                record.id,
                record.app_id,
                record.name,
                record.version,
                record.status,
                json.dumps(record.contract_schema, sort_keys=True),
                record.description,
                0,
                0,
                record.created_at,
                record.updated_at,
            ),
        )
        insert_contract_version(connection, record, "seed_controlled_contract", placeholder)
        insert_contract_audit(
            connection,
            record.id,
            "seed",
            "success",
            "Controlled integration contract seeded without external connection.",
            placeholder,
        )


def row_to_contract(row: Any) -> ContractRecord:
    return ContractRecord(
        id=row_value(row, "id"),
        app_id=row_value(row, "app_id"),
        name=row_value(row, "name"),
        version=row_value(row, "version"),
        status=row_value(row, "status"),
        contract_schema=json.loads(row_value(row, "schema_json")),
        description=row_value(row, "description"),
        breaking_change_detected=bool(row_value(row, "breaking_change_detected")),
        external_connection_enabled=bool(row_value(row, "external_connection_enabled")),
        created_at=row_value(row, "created_at"),
        updated_at=row_value(row, "updated_at"),
    )


def validate_contract_schema(schema: dict[str, Any]) -> None:
    if schema.get("type") != "object":
        raise ContractValidationError(
            {
                "error": "contract_schema_must_be_object",
            }
        )
    if not isinstance(schema.get("properties"), dict):
        raise ContractValidationError(
            {
                "error": "contract_schema_properties_required",
            }
        )
    required = schema.get("required", [])
    if not isinstance(required, list):
        raise ContractValidationError(
            {
                "error": "contract_schema_required_must_be_list",
            }
        )


def value_matches_type(value: Any, expected_type: str) -> bool:
    if expected_type == "string":
        return isinstance(value, str)
    if expected_type == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if expected_type == "number":
        return isinstance(value, int | float) and not isinstance(value, bool)
    if expected_type == "boolean":
        return isinstance(value, bool)
    if expected_type == "object":
        return isinstance(value, dict)
    if expected_type == "array":
        return isinstance(value, list)
    return False


def validate_payload_against_schema(
    schema: dict[str, Any],
    payload: dict[str, Any],
) -> list[str]:
    errors: list[str] = []
    required = schema.get("required", [])
    properties = schema.get("properties", {})

    for field in required:
        if field not in payload:
            errors.append(f"missing_required_field:{field}")

    for field, definition in properties.items():
        if field not in payload:
            continue
        expected_type = definition.get("type")
        if expected_type and not value_matches_type(payload[field], expected_type):
            errors.append(f"invalid_type:{field}:{expected_type}")

    return errors


def detect_breaking_changes(
    current_schema: dict[str, Any],
    proposed_schema: dict[str, Any],
) -> list[str]:
    current_required = set(current_schema.get("required", []))
    proposed_required = set(proposed_schema.get("required", []))
    current_properties = current_schema.get("properties", {})
    proposed_properties = proposed_schema.get("properties", {})
    breaking_changes: list[str] = []

    for field in sorted(proposed_required - current_required):
        breaking_changes.append(f"added_required_field:{field}")

    for field in sorted(set(current_properties) - set(proposed_properties)):
        breaking_changes.append(f"removed_property:{field}")

    for field in sorted(set(current_properties) & set(proposed_properties)):
        current_type = current_properties[field].get("type")
        proposed_type = proposed_properties[field].get("type")
        if current_type != proposed_type:
            breaking_changes.append(
                f"changed_type:{field}:{current_type}->{proposed_type}"
            )

    return breaking_changes


def insert_contract_version(
    connection: Any,
    contract: ContractRecord,
    action: str,
    placeholder: str,
) -> ContractVersion:
    row = connection.execute(
        f"""
        SELECT COUNT(*) AS count
        FROM {CONTRACT_VERSIONS_TABLE}
        WHERE contract_id = {placeholder}
        """,
        (contract.id,),
    ).fetchone()
    version = ContractVersion(
        id=str(uuid4()),
        contract_id=contract.id,
        sequence=row_value(row, "count") + 1,
        action=action,
        payload=contract,
        created_at=utc_now(),
    )
    connection.execute(
        f"""
        INSERT INTO {CONTRACT_VERSIONS_TABLE}
            (id, contract_id, sequence, action, payload_json, created_at)
        VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder})
        """,
        (
            version.id,
            version.contract_id,
            version.sequence,
            version.action,
            version.model_dump_json(),
            version.created_at,
        ),
    )
    return version


def insert_contract_audit(
    connection: Any,
    contract_id: str,
    action: str,
    status: str,
    detail: str,
    placeholder: str,
) -> ContractAuditEvent:
    audit = ContractAuditEvent(
        id=str(uuid4()),
        contract_id=contract_id,
        action=action,
        status=status,
        detail=detail,
        created_at=utc_now(),
    )
    connection.execute(
        f"""
        INSERT INTO {CONTRACT_AUDIT_TABLE}
            (id, contract_id, action, status, detail, created_at)
        VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder})
        """,
        (
            audit.id,
            audit.contract_id,
            audit.action,
            audit.status,
            audit.detail,
            audit.created_at,
        ),
    )
    return audit


def create_contract(contract: ContractCreate) -> ContractRecord:
    ensure_contract_schema()
    validate_contract_schema(contract.contract_schema)

    if get_registered_app(contract.app_id) is None:
        raise ContractValidationError(
            {
                "error": "app_not_registered",
                "app_id": contract.app_id,
            }
        )

    placeholder = sql_placeholder()
    now = utc_now()
    record = ContractRecord(
        id=str(uuid4()),
        app_id=contract.app_id.strip().lower(),
        name=contract.name,
        version=contract.version,
        status=contract.status,
        contract_schema=contract.contract_schema,
        description=contract.description,
        breaking_change_detected=False,
        external_connection_enabled=False,
        created_at=now,
        updated_at=now,
    )

    with connect() as connection:
        connection.execute(
            f"""
            INSERT INTO {CONTRACTS_TABLE} (
                id, app_id, name, version, status, schema_json, description,
                breaking_change_detected, external_connection_enabled, created_at, updated_at
            )
            VALUES (
                {placeholder}, {placeholder}, {placeholder}, {placeholder},
                {placeholder}, {placeholder}, {placeholder}, {placeholder},
                {placeholder}, {placeholder}, {placeholder}
            )
            """,
            (
                record.id,
                record.app_id,
                record.name,
                record.version,
                record.status,
                json.dumps(record.contract_schema, sort_keys=True),
                record.description,
                0,
                0,
                record.created_at,
                record.updated_at,
            ),
        )
        insert_contract_version(connection, record, "create", placeholder)
        insert_contract_audit(
            connection,
            record.id,
            "create",
            "success",
            "Contract registered without external app connection.",
            placeholder,
        )
        connection.commit()

    return record


def list_contracts(app_id: str | None = None) -> list[ContractRecord]:
    ensure_contract_schema()
    placeholder = sql_placeholder()
    where = ""
    params: tuple[str, ...] = ()

    if app_id:
        where = f"WHERE app_id = {placeholder}"
        params = (app_id.strip().lower(),)

    with connect() as connection:
        rows = connection.execute(
            f"""
            SELECT
                id, app_id, name, version, status, schema_json, description,
                breaking_change_detected, external_connection_enabled, created_at, updated_at
            FROM {CONTRACTS_TABLE}
            {where}
            ORDER BY updated_at DESC
            """,
            params,
        ).fetchall()

    return [row_to_contract(row) for row in rows]


def get_contract(contract_id: str) -> ContractRecord | None:
    ensure_contract_schema()
    placeholder = sql_placeholder()

    with connect() as connection:
        row = connection.execute(
            f"""
            SELECT
                id, app_id, name, version, status, schema_json, description,
                breaking_change_detected, external_connection_enabled, created_at, updated_at
            FROM {CONTRACTS_TABLE}
            WHERE id = {placeholder}
            """,
            (contract_id,),
        ).fetchone()

    return row_to_contract(row) if row else None


def update_contract(
    contract_id: str,
    update: ContractUpdate,
) -> ContractRecord | None:
    current = get_contract(contract_id)
    if current is None:
        return None

    proposed_schema = (
        update.contract_schema
        if update.contract_schema is not None
        else current.contract_schema
    )
    validate_contract_schema(proposed_schema)
    breaking_changes = detect_breaking_changes(current.contract_schema, proposed_schema)
    placeholder = sql_placeholder()
    updated = ContractRecord(
        id=current.id,
        app_id=current.app_id,
        name=update.name if update.name is not None else current.name,
        version=update.version if update.version is not None else current.version,
        status=update.status if update.status is not None else current.status,
        contract_schema=proposed_schema,
        description=update.description
        if update.description is not None
        else current.description,
        breaking_change_detected=bool(breaking_changes),
        external_connection_enabled=False,
        created_at=current.created_at,
        updated_at=utc_now(),
    )

    with connect() as connection:
        connection.execute(
            f"""
            UPDATE {CONTRACTS_TABLE}
            SET
                name = {placeholder},
                version = {placeholder},
                status = {placeholder},
                schema_json = {placeholder},
                description = {placeholder},
                breaking_change_detected = {placeholder},
                external_connection_enabled = {placeholder},
                updated_at = {placeholder}
            WHERE id = {placeholder}
            """,
            (
                updated.name,
                updated.version,
                updated.status,
                json.dumps(updated.contract_schema, sort_keys=True),
                updated.description,
                1 if updated.breaking_change_detected else 0,
                0,
                updated.updated_at,
                updated.id,
            ),
        )
        insert_contract_version(connection, updated, update.change_reason, placeholder)
        insert_contract_audit(
            connection,
            updated.id,
            "update",
            "breaking_change_detected" if breaking_changes else "success",
            ";".join(breaking_changes) if breaking_changes else "Contract updated.",
            placeholder,
        )
        connection.commit()

    return updated


def validate_contract_payload(
    contract_id: str,
    request: ContractPayloadValidationRequest,
) -> ContractPayloadValidationResult | None:
    contract = get_contract(contract_id)
    if contract is None:
        return None

    errors = validate_payload_against_schema(contract.contract_schema, request.payload)
    placeholder = sql_placeholder()
    result = ContractPayloadValidationResult(
        contract_id=contract.id,
        valid=not errors,
        errors=errors,
    )

    with connect() as connection:
        insert_contract_audit(
            connection,
            contract.id,
            "validate_payload",
            "success" if result.valid else "failed",
            "Payload valid." if result.valid else ";".join(errors),
            placeholder,
        )
        connection.commit()

    return result


def check_contract_compatibility(
    contract_id: str,
    request: ContractCompatibilityRequest,
) -> ContractCompatibilityResult | None:
    contract = get_contract(contract_id)
    if contract is None:
        return None

    validate_contract_schema(request.proposed_schema)
    breaking_changes = detect_breaking_changes(
        contract.contract_schema,
        request.proposed_schema,
    )
    result = ContractCompatibilityResult(
        contract_id=contract.id,
        compatible=not breaking_changes,
        breaking_changes=breaking_changes,
        checked_at=utc_now(),
    )
    placeholder = sql_placeholder()

    with connect() as connection:
        insert_contract_audit(
            connection,
            contract.id,
            "compatibility_check",
            "compatible" if result.compatible else "breaking_change_detected",
            "Compatible schema." if result.compatible else ";".join(breaking_changes),
            placeholder,
        )
        connection.commit()

    return result


def list_contract_versions(contract_id: str) -> list[ContractVersion] | None:
    if get_contract(contract_id) is None:
        return None

    placeholder = sql_placeholder()
    with connect() as connection:
        rows = connection.execute(
            f"""
            SELECT payload_json
            FROM {CONTRACT_VERSIONS_TABLE}
            WHERE contract_id = {placeholder}
            ORDER BY sequence DESC
            """,
            (contract_id,),
        ).fetchall()

    return [ContractVersion(**json.loads(row_value(row, "payload_json"))) for row in rows]


def list_contract_audit() -> list[ContractAuditEvent]:
    ensure_contract_schema()

    with connect() as connection:
        rows = connection.execute(
            f"""
            SELECT id, contract_id, action, status, detail, created_at
            FROM {CONTRACT_AUDIT_TABLE}
            ORDER BY created_at DESC
            """
        ).fetchall()

    return [
        ContractAuditEvent(
            id=row_value(row, "id"),
            contract_id=row_value(row, "contract_id"),
            action=row_value(row, "action"),
            status=row_value(row, "status"),
            detail=row_value(row, "detail"),
            created_at=row_value(row, "created_at"),
        )
        for row in rows
    ]


def get_contract_status() -> ContractStatus:
    ensure_contract_schema()

    with connect() as connection:
        contracts_row = connection.execute(
            f"SELECT COUNT(*) AS count FROM {CONTRACTS_TABLE}"
        ).fetchone()
        versions_row = connection.execute(
            f"SELECT COUNT(*) AS count FROM {CONTRACT_VERSIONS_TABLE}"
        ).fetchone()
        audit_row = connection.execute(
            f"SELECT COUNT(*) AS count FROM {CONTRACT_AUDIT_TABLE}"
        ).fetchone()

    return ContractStatus(
        status="contracts_operational",
        contracts=row_value(contracts_row, "count"),
        versions=row_value(versions_row, "count"),
        audit_events=row_value(audit_row, "count"),
        external_connections_enabled=False,
    )
