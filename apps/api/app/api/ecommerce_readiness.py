from fastapi import APIRouter, Depends, HTTPException, status

from app.schemas.auth import AuthenticatedUser, ControlCenterRole
from app.schemas.ecommerce_readiness import AmazonReadinessStatus, CommerceOpportunity, EcommerceReadinessStatus
from app.services.auth import get_current_user, require_control_center_user
from app.services.ecommerce_readiness import (
    get_amazon_readiness_status,
    get_ecommerce_readiness_status,
    list_amazon_opportunities,
    list_amazon_risks,
    list_ecommerce_approval_needed,
    list_ecommerce_opportunities,
)

ecommerce_router = APIRouter(
    prefix="/api/v1/ecommerce-readiness",
    tags=["ecommerce-readiness"],
    dependencies=[Depends(require_control_center_user)],
)
amazon_router = APIRouter(
    prefix="/api/v1/amazon-readiness",
    tags=["amazon-readiness"],
    dependencies=[Depends(require_control_center_user)],
)

READ_ROLES = {
    ControlCenterRole.ceo,
    ControlCenterRole.admin,
    ControlCenterRole.operator,
    ControlCenterRole.auditor,
}


def require_commerce_read(user: AuthenticatedUser) -> None:
    if user.role not in READ_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error": "commerce_readiness_role_not_authorized", "role": user.role.value},
        )


@ecommerce_router.get("/status", response_model=EcommerceReadinessStatus)
def read_ecommerce_readiness_status(
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> EcommerceReadinessStatus:
    require_commerce_read(current_user)
    return get_ecommerce_readiness_status()


@ecommerce_router.get("/opportunities", response_model=list[CommerceOpportunity])
def read_ecommerce_readiness_opportunities(
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> list[CommerceOpportunity]:
    require_commerce_read(current_user)
    return list_ecommerce_opportunities()


@ecommerce_router.get("/approval-needed", response_model=list[CommerceOpportunity])
def read_ecommerce_readiness_approval_needed(
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> list[CommerceOpportunity]:
    require_commerce_read(current_user)
    return list_ecommerce_approval_needed()


@amazon_router.get("/status", response_model=AmazonReadinessStatus)
def read_amazon_readiness_status(
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> AmazonReadinessStatus:
    require_commerce_read(current_user)
    return get_amazon_readiness_status()


@amazon_router.get("/opportunities", response_model=list[CommerceOpportunity])
def read_amazon_readiness_opportunities(
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> list[CommerceOpportunity]:
    require_commerce_read(current_user)
    return list_amazon_opportunities()


@amazon_router.get("/risks", response_model=list[CommerceOpportunity])
def read_amazon_readiness_risks(
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> list[CommerceOpportunity]:
    require_commerce_read(current_user)
    return list_amazon_risks()

# Dropshipping PE: stateless simulations only. Existing auth and role controls apply.
from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field
from app.services.dropshipping_pe_offline import UnitEconomics
from app.services.dropshipping_pe_operations import Event, operation_status, simulate_order


class FinancialScenario(BaseModel):
    model_config = ConfigDict(extra="forbid")
    price: Decimal = Field(gt=0, le=100000, max_digits=12, decimal_places=2)
    supplier_cost: Decimal = Field(ge=0, le=100000, max_digits=12, decimal_places=2)
    delivered_shipping: Decimal = Field(ge=0, le=100000, max_digits=12, decimal_places=2)
    failed_shipping: Decimal = Field(ge=0, le=100000, max_digits=12, decimal_places=2)
    advertising_per_order: Decimal = Field(ge=0, le=100000, max_digits=12, decimal_places=2)
    delivery_rate: Decimal = Field(gt=0, le=1, decimal_places=4)
    payment_rate: Decimal = Field(ge=0, le=1, decimal_places=4)
    reserve_per_delivery: Decimal = Field(ge=0, le=100000, max_digits=12, decimal_places=2)
    vat_rate: Decimal = Field(default=Decimal("0.18"), ge=0, le=1, decimal_places=4)


class OrderSimulation(BaseModel):
    model_config = ConfigDict(extra="forbid")
    events: list[Event] = Field(default_factory=list, max_length=8)


@ecommerce_router.get("/dropshipping-pe/status")
def dropshipping_status(current_user: AuthenticatedUser = Depends(get_current_user)) -> dict:
    require_commerce_read(current_user)
    return operation_status()


@ecommerce_router.post("/dropshipping-pe/financial-scenario")
def dropshipping_financial_scenario(
    payload: FinancialScenario, current_user: AuthenticatedUser = Depends(get_current_user)
) -> dict:
    require_commerce_read(current_user)
    value = UnitEconomics(**payload.model_dump()).contribution_per_delivery()
    return {"mode": "simulation", "currency": "PEN", "contribution_per_delivery": str(value),
            "meets_provisional_target": value >= Decimal("15"), "live_enabled": False}


@ecommerce_router.post("/dropshipping-pe/order-simulation")
def dropshipping_order_simulation(
    payload: OrderSimulation, current_user: AuthenticatedUser = Depends(get_current_user)
) -> dict:
    require_commerce_read(current_user)
    try:
        return simulate_order(payload.events)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
