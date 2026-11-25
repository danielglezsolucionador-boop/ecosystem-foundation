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

from app.services.dropshipping_pe_catalog import MockQuote, Provider, catalog, compare


class HypotheticalQuote(BaseModel):
    model_config = ConfigDict(extra="forbid")
    provider: Provider
    economics: FinancialScenario


class ProviderComparison(BaseModel):
    model_config = ConfigDict(extra="forbid")
    candidate_id: str = Field(pattern=r"^PE-[0-9]{3}$")
    quotes: list[HypotheticalQuote] = Field(min_length=1, max_length=3)


@ecommerce_router.get("/dropshipping-pe/catalog")
def dropshipping_catalog(current_user: AuthenticatedUser = Depends(get_current_user)) -> dict:
    require_commerce_read(current_user)
    return {"mode": "research", "items": catalog(), "live_enabled": False}


@ecommerce_router.post("/dropshipping-pe/provider-comparison")
def dropshipping_provider_comparison(
    payload: ProviderComparison, current_user: AuthenticatedUser = Depends(get_current_user)
) -> dict:
    require_commerce_read(current_user)
    try:
        return compare(payload.candidate_id, [
            MockQuote(q.provider, UnitEconomics(**q.economics.model_dump()))
            for q in payload.quotes
        ])
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

from app.services.dropshipping_pe_pipeline import PipelineScenario, pipeline_contract, simulate_pipeline


@ecommerce_router.get("/dropshipping-pe/pipeline-contract")
def dropshipping_pipeline_contract(current_user: AuthenticatedUser = Depends(get_current_user)) -> dict:
    require_commerce_read(current_user)
    return pipeline_contract()


@ecommerce_router.post("/dropshipping-pe/pipeline-simulation")
def dropshipping_pipeline_simulation(
    payload: PipelineScenario, current_user: AuthenticatedUser = Depends(get_current_user)
) -> dict:
    require_commerce_read(current_user)
    try:
        return simulate_pipeline(payload)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

from contextlib import contextmanager
from typing import Literal
from app.core.config import get_settings
from app.core.database import connect
from app.services.auth import control_center_auth_enabled
from app.services.dropshipping_pe_evidence import EvidenceStore, PLAYBOOKS, playbook


def require_evidence_access(user: AuthenticatedUser) -> None:
    require_commerce_read(user)
    if not control_center_auth_enabled():
        raise HTTPException(status_code=403, detail="Real authentication required")


@contextmanager
def local_demo_evidence_store():
    settings = get_settings()
    if (settings.environment != "local" or not settings.database_url.startswith("sqlite:///")
            or settings.database_url == "sqlite:///:memory:"):
        raise HTTPException(status_code=503, detail="Persistent evidence rehearsal is local SQLite only")
    db = connect(settings.database_url)
    try:
        with db:
            store = EvidenceStore(db)
            store.initialize()
            yield store
    finally:
        db.close()


class DemoEvidenceSubmission(BaseModel):
    model_config = ConfigDict(extra="forbid")
    candidate: str = Field(pattern=r"^PE-[0-9]{3}$")
    provider: Provider
    kind: Literal["stock", "cost", "logistics", "sample", "checkout", "legal"]
    reference: str = Field(pattern=r"^DEMO-[0-9]{1,8}$")


class DemoEvidenceReview(BaseModel):
    model_config = ConfigDict(extra="forbid")
    decision: Literal["accepted_demo", "rejected_demo"]


@ecommerce_router.get("/dropshipping-pe/playbooks")
def dropshipping_playbooks(current_user: AuthenticatedUser = Depends(get_current_user)) -> dict:
    require_evidence_access(current_user)
    return {"mode": "simulation", "items": [{"intent": intent, **playbook(intent)} for intent in PLAYBOOKS],
            "live_enabled": False}


@ecommerce_router.get("/dropshipping-pe/evidence")
def dropshipping_evidence(current_user: AuthenticatedUser = Depends(get_current_user)) -> dict:
    require_evidence_access(current_user)
    with local_demo_evidence_store() as store:
        return store.snapshot()


@ecommerce_router.post("/dropshipping-pe/evidence", status_code=201)
def submit_dropshipping_evidence(
    payload: DemoEvidenceSubmission, current_user: AuthenticatedUser = Depends(get_current_user)
) -> dict:
    require_evidence_access(current_user)
    try:
        with local_demo_evidence_store() as store:
            eid = store.submit(payload.candidate, payload.provider.value, payload.kind,
                               payload.reference, current_user.id, current_user.role.value)
        return {"id": eid, "mode": "simulation", "live_enabled": False, "approved_for_sale": False}
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@ecommerce_router.post("/dropshipping-pe/evidence/{evidence_id}/review")
def review_dropshipping_evidence(
    evidence_id: str, payload: DemoEvidenceReview,
    current_user: AuthenticatedUser = Depends(get_current_user)
) -> dict:
    require_evidence_access(current_user)
    try:
        with local_demo_evidence_store() as store:
            store.review(evidence_id, payload.decision, current_user.id, current_user.role.value)
        return {"mode": "simulation", "decision": payload.decision,
                "live_enabled": False, "approved_for_sale": False}
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

from app.services.dropshipping_pe_growth import (
    CampaignScenario, CreativeChecklist, creative_plan, evaluate_campaign, evaluate_creative,
)


@ecommerce_router.get("/dropshipping-pe/growth/creative-plan")
def dropshipping_creative_plan(
    candidate: str, platform: Literal["facebook", "instagram", "tiktok"],
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> dict:
    require_evidence_access(current_user)
    try:
        return creative_plan(candidate, platform)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@ecommerce_router.post("/dropshipping-pe/growth/creative-review")
def dropshipping_creative_review(
    payload: CreativeChecklist, current_user: AuthenticatedUser = Depends(get_current_user),
) -> dict:
    require_evidence_access(current_user)
    return evaluate_creative(payload)


@ecommerce_router.post("/dropshipping-pe/growth/campaign-simulation")
def dropshipping_campaign_simulation(
    payload: CampaignScenario, current_user: AuthenticatedUser = Depends(get_current_user),
) -> dict:
    require_evidence_access(current_user)
    return evaluate_campaign(payload)

import os
from fastapi import Header
from typing import Annotated
from app.services.dropshipping_pe_order_store import (
    DemoOrder, SignedDemoEvent, OrderStore, OrderId, Conflict, Paused,
)


@contextmanager
def local_demo_order_store():
    settings = get_settings()
    if (settings.environment != "local" or not settings.database_url.startswith("sqlite:///")
            or settings.database_url == "sqlite:///:memory:"):
        raise HTTPException(status_code=503, detail="Persistent order rehearsal is local SQLite only")
    db = connect(settings.database_url)
    try:
        store = OrderStore(db)
        store.initialize()
        yield store
    finally:
        db.close()


def demo_order_error(exc):
    code = 403 if isinstance(exc, PermissionError) else 409 if isinstance(exc, (Conflict, Paused)) else 422
    if isinstance(exc, RuntimeError):
        code = 503
    return HTTPException(status_code=code, detail=str(exc))


class DemoPause(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    paused: bool


@ecommerce_router.get("/dropshipping-pe/persistent-orders")
def list_demo_orders(current_user: AuthenticatedUser = Depends(get_current_user)) -> dict:
    require_evidence_access(current_user)
    with local_demo_order_store() as store:
        return store.snapshot()


@ecommerce_router.post("/dropshipping-pe/persistent-orders")
def create_demo_order(payload: DemoOrder, current_user: AuthenticatedUser = Depends(get_current_user)) -> dict:
    require_evidence_access(current_user)
    try:
        with local_demo_order_store() as store:
            return store.create(payload,current_user.id,current_user.role.value)
    except (PermissionError, ValueError) as exc:
        raise demo_order_error(exc) from exc


@ecommerce_router.get("/dropshipping-pe/persistent-orders/{order_id}")
def get_demo_order(order_id: OrderId, current_user: AuthenticatedUser = Depends(get_current_user)) -> dict:
    require_evidence_access(current_user)
    try:
        with local_demo_order_store() as store:
            return store.get(order_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@ecommerce_router.post("/dropshipping-pe/demo-events")
def receive_demo_event(payload: SignedDemoEvent,
                       signature: Annotated[str | None, Header(alias="X-Demo-Signature")] = None,
                       current_user: AuthenticatedUser = Depends(get_current_user)) -> dict:
    require_evidence_access(current_user)
    try:
        with local_demo_order_store() as store:
            return store.receive(payload,signature,os.environ.get("DROPSHIPPING_DEMO_EVENT_SECRET"),
                                 current_user.id,current_user.role.value)
    except (PermissionError, ValueError, RuntimeError) as exc:
        raise demo_order_error(exc) from exc


@ecommerce_router.post("/dropshipping-pe/demo-pause")
def pause_demo_orders(payload: DemoPause, current_user: AuthenticatedUser = Depends(get_current_user)) -> dict:
    require_evidence_access(current_user)
    try:
        with local_demo_order_store() as store:
            return store.set_paused(payload.paused,current_user.id,current_user.role.value)
    except PermissionError as exc:
        raise demo_order_error(exc) from exc

from app.services.dropshipping_pe_tasks import DemoTask, TaskStore


@contextmanager
def local_demo_task_store():
    with local_demo_order_store() as order_store:
        store = TaskStore(order_store.db)
        store.initialize()
        yield store


@ecommerce_router.get("/dropshipping-pe/tasks")
def list_demo_tasks(current_user: AuthenticatedUser = Depends(get_current_user)) -> dict:
    require_evidence_access(current_user)
    with local_demo_task_store() as store:
        return store.snapshot()


@ecommerce_router.post("/dropshipping-pe/tasks")
def enqueue_demo_task(payload: DemoTask, current_user: AuthenticatedUser = Depends(get_current_user)) -> dict:
    require_evidence_access(current_user)
    try:
        with local_demo_task_store() as store:
            return store.enqueue(payload,current_user.id,current_user.role.value)
    except (PermissionError, ValueError) as exc:
        raise demo_order_error(exc) from exc


@ecommerce_router.post("/dropshipping-pe/tasks/tick")
def tick_demo_task(current_user: AuthenticatedUser = Depends(get_current_user)) -> dict:
    require_evidence_access(current_user)
    try:
        with local_demo_task_store() as store:
            return store.tick(current_user.id,current_user.role.value)
    except (PermissionError, ValueError) as exc:
        raise demo_order_error(exc) from exc


@ecommerce_router.post("/dropshipping-pe/tasks/{task_id}/acknowledge")
def acknowledge_demo_task(task_id: Annotated[str, Field(pattern=r"^TASK-[0-9a-f]{32}$")],
                          current_user: AuthenticatedUser = Depends(get_current_user)) -> dict:
    require_evidence_access(current_user)
    try:
        with local_demo_task_store() as store:
            return store.acknowledge(task_id,current_user.id,current_user.role.value)
    except (PermissionError, ValueError) as exc:
        raise demo_order_error(exc) from exc
