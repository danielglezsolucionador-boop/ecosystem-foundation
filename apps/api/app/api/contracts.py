from fastapi import APIRouter, HTTPException, status as http_status

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
from app.services.contracts import (
    ContractValidationError,
    check_contract_compatibility,
    create_contract,
    get_contract,
    get_contract_status,
    list_contract_audit,
    list_contract_versions,
    list_contracts,
    update_contract,
    validate_contract_payload,
)

router = APIRouter(prefix="/api/v1/contracts", tags=["contracts"])


@router.get("", response_model=list[ContractRecord])
def read_contracts(app_id: str | None = None) -> list[ContractRecord]:
    return list_contracts(app_id=app_id)


@router.post("", response_model=ContractRecord, status_code=http_status.HTTP_201_CREATED)
def register_contract(contract: ContractCreate) -> ContractRecord:
    try:
        return create_contract(contract)
    except ContractValidationError as exc:
        raise HTTPException(status_code=400, detail=exc.detail) from exc


@router.get("/status", response_model=ContractStatus)
def read_contract_status() -> ContractStatus:
    return get_contract_status()


@router.get("/audit", response_model=list[ContractAuditEvent])
def read_contract_audit() -> list[ContractAuditEvent]:
    return list_contract_audit()


@router.get("/{contract_id}", response_model=ContractRecord)
def read_contract(contract_id: str) -> ContractRecord:
    contract = get_contract(contract_id)

    if contract is None:
        raise HTTPException(
            status_code=404,
            detail={
                "error": "contract_not_found",
                "contract_id": contract_id,
            },
        )

    return contract


@router.put("/{contract_id}", response_model=ContractRecord)
def replace_contract(contract_id: str, update: ContractUpdate) -> ContractRecord:
    try:
        contract = update_contract(contract_id, update)
    except ContractValidationError as exc:
        raise HTTPException(status_code=400, detail=exc.detail) from exc

    if contract is None:
        raise HTTPException(
            status_code=404,
            detail={
                "error": "contract_not_found",
                "contract_id": contract_id,
            },
        )

    return contract


@router.post(
    "/{contract_id}/validate",
    response_model=ContractPayloadValidationResult,
)
def validate_payload(
    contract_id: str,
    request: ContractPayloadValidationRequest,
) -> ContractPayloadValidationResult:
    result = validate_contract_payload(contract_id, request)

    if result is None:
        raise HTTPException(
            status_code=404,
            detail={
                "error": "contract_not_found",
                "contract_id": contract_id,
            },
        )

    return result


@router.get("/{contract_id}/versions", response_model=list[ContractVersion])
def read_contract_versions(contract_id: str) -> list[ContractVersion]:
    versions = list_contract_versions(contract_id)

    if versions is None:
        raise HTTPException(
            status_code=404,
            detail={
                "error": "contract_not_found",
                "contract_id": contract_id,
            },
        )

    return versions


@router.post(
    "/{contract_id}/compatibility-check",
    response_model=ContractCompatibilityResult,
)
def compatibility_check(
    contract_id: str,
    request: ContractCompatibilityRequest,
) -> ContractCompatibilityResult:
    try:
        result = check_contract_compatibility(contract_id, request)
    except ContractValidationError as exc:
        raise HTTPException(status_code=400, detail=exc.detail) from exc

    if result is None:
        raise HTTPException(
            status_code=404,
            detail={
                "error": "contract_not_found",
                "contract_id": contract_id,
            },
        )

    return result
