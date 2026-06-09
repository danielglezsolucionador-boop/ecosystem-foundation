from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class WorkdayPhase(StrEnum):
    morning = "morning"
    midday = "midday"
    evening = "evening"


class WorkdayAlertCategory(StrEnum):
    revenue_opportunity = "revenue_opportunity"
    trend = "trend"
    security_risk = "security_risk"
    legal_tax_risk = "legal_tax_risk"
    production_down = "production_down"
    critical_blocker = "critical_blocker"
    temporary_opportunity = "temporary_opportunity"
    revenue_goal = "revenue_goal"
    low_signal = "low_signal"


class WorkdaySchedule(BaseModel):
    timezone: str = "America/Lima"
    morning_time: str = "08:00"
    midday_time: str = "13:00"
    evening_time: str = "19:00"
    scheduler_status: str = "prepared"
    manual_trigger_available: bool = True


class WorkdayStartRequest(BaseModel):
    date: str | None = Field(default=None, max_length=20)
    timezone: str = Field(default="America/Lima", max_length=80)


class WorkdayAlertEvaluateRequest(BaseModel):
    title: str = Field(min_length=1, max_length=180)
    summary: str = Field(min_length=1, max_length=1200)
    category: WorkdayAlertCategory = WorkdayAlertCategory.low_signal
    relevance_score: int = Field(default=50, ge=0, le=100)
    why_it_matters: str | None = Field(default=None, max_length=1000)
    opportunity: str | None = Field(default=None, max_length=1000)
    threat: str | None = Field(default=None, max_length=1000)
    recommended_action: str = Field(default="Registrar y observar.", max_length=1000)
    departments_involved: list[str] = Field(default_factory=list)
    dafo: dict[str, str] = Field(default_factory=dict)
    economic_impact_usd: float | None = Field(default=None, ge=0)
    requires_money: bool = False
    risk_level: str = Field(default="controlled", max_length=80)


class WorkdayPriorityChangeCreate(BaseModel):
    previous_priority: str = Field(min_length=1, max_length=300)
    new_priority: str = Field(min_length=1, max_length=300)
    reason: str = Field(min_length=1, max_length=1000)
    opportunity_or_risk: str = Field(default="operational", max_length=500)
    economic_impact_usd: float | None = Field(default=None, ge=0)
    departments_affected: list[str] = Field(default_factory=list)
    report_to_ceo: str = Field(default="CEREBRO reporta el cambio al CEO.", max_length=1000)


class WorkdayCheckpoint(BaseModel):
    id: str = Field(min_length=1)
    workday_id: str = Field(min_length=1)
    phase: WorkdayPhase
    date: str = Field(min_length=1)
    timezone: str = "America/Lima"
    schedule_time: str = Field(min_length=1)
    headline: str = Field(min_length=1)
    summary: str = Field(min_length=1)
    active_missions: list[dict[str, Any]] = Field(default_factory=list)
    priorities: list[str] = Field(default_factory=list)
    departments: list[str] = Field(default_factory=list)
    opportunities: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    blockers: list[str] = Field(default_factory=list)
    decisions_by_cerebro: list[str] = Field(default_factory=list)
    requires_ceo: list[str] = Field(default_factory=list)
    estimated_economic_impact: str = Field(default="unknown", min_length=1)
    action_plan: list[str] = Field(default_factory=list)
    report: str = Field(min_length=1)
    generated_at: str = Field(min_length=1)
    external_connection_enabled: bool = False
    runtime_connected: bool = False
    sunat_enabled: bool = False


class WorkdayAlert(BaseModel):
    id: str = Field(min_length=1)
    workday_id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    summary: str = Field(min_length=1)
    category: WorkdayAlertCategory
    relevance_score: int = Field(ge=0, le=100)
    interrupt_ceo: bool
    why_it_matters: str = Field(min_length=1)
    opportunity: str | None = None
    threat: str | None = None
    recommended_action: str = Field(min_length=1)
    departments_involved: list[str] = Field(default_factory=list)
    dafo: dict[str, str] = Field(default_factory=dict)
    economic_impact_usd: float | None = None
    requires_money: bool = False
    requires_ceo_approval: bool = False
    included_in_ceo_feed: bool = False
    audit_event_id: str | None = None
    created_at: str = Field(min_length=1)
    external_connection_enabled: bool = False
    runtime_connected: bool = False
    payment_connected: bool = False
    sunat_enabled: bool = False


class WorkdayPriorityChange(BaseModel):
    id: str = Field(min_length=1)
    workday_id: str = Field(min_length=1)
    previous_priority: str = Field(min_length=1)
    new_priority: str = Field(min_length=1)
    reason: str = Field(min_length=1)
    opportunity_or_risk: str = Field(min_length=1)
    economic_impact_usd: float | None = None
    departments_affected: list[str] = Field(default_factory=list)
    moment: str = Field(min_length=1)
    report_to_ceo: str = Field(min_length=1)
    requires_ceo_approval: bool = False
    audit_event_id: str | None = None
    external_connection_enabled: bool = False
    runtime_connected: bool = False


class WorkdaySession(BaseModel):
    id: str = Field(min_length=1)
    date: str = Field(min_length=1)
    timezone: str = "America/Lima"
    morning_plan: dict[str, Any] = Field(default_factory=dict)
    midday_status: dict[str, Any] = Field(default_factory=dict)
    evening_report: dict[str, Any] = Field(default_factory=dict)
    active_missions: list[dict[str, Any]] = Field(default_factory=list)
    priority_changes: list[WorkdayPriorityChange] = Field(default_factory=list)
    alerts: list[WorkdayAlert] = Field(default_factory=list)
    revenue_progress: dict[str, Any] = Field(default_factory=dict)
    ecommerce_progress: dict[str, Any] = Field(default_factory=dict)
    blockers: list[str] = Field(default_factory=list)
    CEO_requests: list[str] = Field(default_factory=list)
    scheduler_status: str = "prepared"
    manual_trigger_available: bool = True
    generated_at: str = Field(min_length=1)
    created_at: str = Field(min_length=1)
    updated_at: str = Field(min_length=1)
    external_connection_enabled: bool = False
    runtime_connected: bool = False
    payment_connected: bool = False
    sunat_enabled: bool = False


class WorkdayStatus(BaseModel):
    status: str = Field(min_length=1)
    date: str = Field(min_length=1)
    timezone: str = "America/Lima"
    schedule: WorkdaySchedule = Field(default_factory=WorkdaySchedule)
    scheduler_status: str = "prepared"
    manual_trigger_available: bool = True
    active_missions: int = 0
    priority_changes: int = 0
    relevant_alerts: int = 0
    revenue_progress: dict[str, Any] = Field(default_factory=dict)
    ecommerce_progress: dict[str, Any] = Field(default_factory=dict)
    blockers: list[str] = Field(default_factory=list)
    CEO_requests: list[str] = Field(default_factory=list)
    generated_at: str = Field(min_length=1)
    external_connection_enabled: bool = False
    runtime_connected: bool = False
    payment_connected: bool = False
    sunat_enabled: bool = False


class WorkdayReport(BaseModel):
    status: str = Field(min_length=1)
    session: WorkdaySession
    morning: dict[str, Any] = Field(default_factory=dict)
    midday: dict[str, Any] = Field(default_factory=dict)
    evening: dict[str, Any] = Field(default_factory=dict)
    alerts: list[WorkdayAlert] = Field(default_factory=list)
    priority_changes: list[WorkdayPriorityChange] = Field(default_factory=list)
    generated_at: str = Field(min_length=1)
    external_connection_enabled: bool = False
    runtime_connected: bool = False
