from __future__ import annotations

import asyncio
from datetime import UTC, datetime
import json
from pathlib import Path
from typing import Any

from apps.sombra.alerts import AlertGenerationEngine, DailyIntelligenceBriefing, ProactiveAlertProtocol
from apps.sombra.analysis import SombraAnalysisPipeline
from apps.sombra.collector import CollectorScheduler
from apps.sombra.collector.agents import SombraAbuseAgent, SombraCVEAgent, SombraPasteAgent, SombraRSSAgent
from apps.sombra.communication import CEOAlertCodeSystem, InboundOrderProcessor, OutboundTransmissionEngine
from apps.sombra.identity import IdentityManager
from apps.sombra.integrations import (
    CerebroConnector,
    CerebroOrderHandler,
    ForjaConnector,
    ForjaSignalBuilder,
    SentinelaConnector,
)
from apps.sombra.memory import BlackBoxAuditCore, ClientMemoryLayer, DatabaseConnection, GlobalMemoryLayer
from apps.sombra.memory.ceo_protection import CEOProtectionProfile
from apps.sombra.memory.database import LOG_DIR
from apps.sombra.monitoring import AICostMonitor, ModelRouter, SombraHealthMonitor, SombraMetrics, SombraWatchdog
from apps.sombra.security import HardeningChecker, IntrusionDetectionSystem, LockdownProtocol


CORE_LOG = LOG_DIR / "core.log"
COLLECTOR_TIMEOUT_SECONDS = 12
MAX_PACKAGES_PER_AGENT = 3
SYSTEM_BANNER = (
    "=" * 31
    + "\nSOMBRA INTELLIGENCE SYSTEM\n"
    + "STATUS: OPERATIONAL\n"
    + "CLASSIFICATION: CLASSIFIED\n"
    + "=" * 31
)


class SombraCore:
    def __init__(self) -> None:
        self.database = DatabaseConnection()
        self.blackbox = BlackBoxAuditCore(self.database)
        self.collector_scheduler = CollectorScheduler(
            agents=[
                SombraCVEAgent(results_per_page=10),
                SombraRSSAgent(max_items_per_feed=1),
                SombraAbuseAgent(max_items=2),
                SombraPasteAgent(max_items=1),
            ]
        )
        self.analysis_pipeline = SombraAnalysisPipeline()
        self.global_memory = GlobalMemoryLayer(self.database)
        self.client_memory = ClientMemoryLayer(self.database)
        self.identity_manager = IdentityManager(self.database, self.blackbox)
        self.outbound_engine = OutboundTransmissionEngine(self.database, self.blackbox)
        self.inbound_processor = InboundOrderProcessor(self.database, self.blackbox)
        self.alert_generator = AlertGenerationEngine(self.database, self.blackbox)
        self.proactive_protocol = ProactiveAlertProtocol()
        self.intrusion_detector = IntrusionDetectionSystem(self.database, self.blackbox)
        self.lockdown_protocol = LockdownProtocol(self.database, self.blackbox)
        self.health_monitor = SombraHealthMonitor()
        self.watchdog = SombraWatchdog(self.database)
        self.metrics = SombraMetrics(self.database)
        self.model_router = ModelRouter(self.database, self.blackbox)
        self.ai_cost_monitor = AICostMonitor(self.database, self.blackbox, self.model_router)
        self.ceo_alert_codes = CEOAlertCodeSystem(self.database, self.blackbox)
        self.ceo_protection_profile = CEOProtectionProfile(self.database, self.blackbox)
        self.briefing_engine = DailyIntelligenceBriefing(
            self.database,
            self.ai_cost_monitor,
            self.model_router,
            self.ceo_protection_profile,
        )
        self.hardening_checker = HardeningChecker(self.database)
        self.cerebro_connector = CerebroConnector(
            self.database,
            self.blackbox,
            self.health_monitor,
            self.metrics,
            self.lockdown_protocol,
        )
        self.cerebro_order_handler = CerebroOrderHandler(
            self.database,
            self.blackbox,
            self.inbound_processor,
        )
        self.sentinela_connector = SentinelaConnector(self.database, self.blackbox)
        self.forja_connector = ForjaConnector(self.database, self.blackbox)
        self.forja_signal_builder = ForjaSignalBuilder()
        self._background_tasks: list[asyncio.Task[Any]] = []
        self._started = False
        self._last_cycle_summary: dict[str, Any] = {}

    async def start(self, background_services: bool = True) -> dict[str, Any]:
        await self._ensure_database()
        hardening = await self.hardening_checker.run_checks()
        modules_health = await self.health_monitor.check_all_modules()
        await self.blackbox.log(
            "SOMBRA_STARTUP",
            "SOMBRA_CORE",
            {
                "hardening_status": hardening["overall_status"],
                "modules": {name: row["status"] for name, row in modules_health.items()},
            },
            order_origin="SOMBRA_CORE",
        )
        if background_services and not self._started:
            self._background_tasks.append(asyncio.create_task(self.collector_scheduler.start()))
            self._background_tasks.append(asyncio.create_task(self.watchdog.run_forever(interval_seconds=30)))
            self._started = True
        elif not background_services:
            await self.collector_scheduler._log_cycle("scheduler_start", "Collector scheduler ready for manual cycle")
            await self.watchdog.run_once()
        await self.blackbox.log(
            "SOMBRA_FULLY_OPERATIONAL",
            "SOMBRA_CORE",
            {"status": "OPERATIONAL", "classification": "CLASSIFIED"},
            order_origin="SOMBRA_CORE",
        )
        await self.cerebro_connector.send_heartbeat(**await self._heartbeat_context())
        await asyncio.to_thread(self._append_core_log, "SOMBRA FULLY OPERATIONAL")
        print(SYSTEM_BANNER, flush=True)
        return {"hardening": hardening, "modules_health": modules_health, "status": "OPERATIONAL"}

    async def process_intel_cycle(self) -> dict[str, Any]:
        await self._ensure_database()
        collected = await self._collect_from_agents_once()
        cycle_summary = {
            "collected_by_agent": {agent_id: len(packages) for agent_id, packages in collected.items()},
            "processed": 0,
            "processing_limit_per_agent": MAX_PACKAGES_PER_AGENT,
            "alerts_generated": 0,
            "proactive_alerts": 0,
            "transmissions": 0,
            "errors": [],
        }
        for agent_id, packages in collected.items():
            for package in packages[:MAX_PACKAGES_PER_AGENT]:
                try:
                    analysis = self.analysis_pipeline.analyze(package)
                    memory_id = await self.global_memory.store_intel(
                        analysis.classified,
                        analysis.score,
                        analysis.prediction,
                    )
                    proactive = await self.proactive_protocol.evaluate(analysis.classified, analysis.score)
                    alert = None
                    if self._should_generate_alert(analysis, proactive):
                        alert = await self.alert_generator.generate_alert(
                            analysis.classified,
                            analysis.score,
                            analysis.prediction,
                        )
                        cycle_summary["alerts_generated"] += 1
                        if proactive:
                            cycle_summary["proactive_alerts"] += 1
                        await self._handle_ceo_personal_asset_alert(alert)
                    cycle_summary["transmissions"] += await self._transmit_cycle_result(memory_id, analysis, alert)
                    cycle_summary["processed"] += 1
                    await self.metrics.record("intel_processed", 1)
                    await self.blackbox.log(
                        "INTEL_CYCLE_PROCESSED",
                        str(getattr(package, "intel_id", memory_id)),
                        {
                            "agent_id": agent_id,
                            "memory_id": memory_id,
                            "alert_id": getattr(alert, "alert_id", None),
                            "score": analysis.score.final,
                            "threat_type": analysis.classified.threat_type,
                        },
                        order_origin="SOMBRA_CORE",
                    )
                except Exception as error:
                    cycle_summary["errors"].append({"agent_id": agent_id, "error": repr(error)})
                    await self.blackbox.log(
                        "INTEL_CYCLE_ERROR",
                        agent_id,
                        {"error": repr(error)},
                        order_origin="SOMBRA_CORE",
                    )
        cycle_summary["timestamp_utc"] = self._now()
        self._last_cycle_summary = cycle_summary
        await asyncio.to_thread(self._append_core_log, f"INTEL_CYCLE {json.dumps(cycle_summary, sort_keys=True)}")
        return cycle_summary

    async def _collect_from_agents_once(self) -> dict[str, list[Any]]:
        results: dict[str, list[Any]] = {}
        for agent in sorted(self.collector_scheduler.agents, key=lambda item: item.priority):
            await self.collector_scheduler._log_cycle(agent.agent_id, "cycle_start")
            try:
                packages = await asyncio.wait_for(agent.collect(), timeout=COLLECTOR_TIMEOUT_SECONDS)
                results[agent.agent_id] = packages
                await self.collector_scheduler._log_cycle(agent.agent_id, f"cycle_complete packages={len(packages)}")
            except TimeoutError as error:
                results[agent.agent_id] = []
                await agent.report_failure(error)
                await self.collector_scheduler._log_cycle(
                    agent.agent_id,
                    f"cycle_timeout seconds={COLLECTOR_TIMEOUT_SECONDS}",
                )
                await self.blackbox.log(
                    "INTEL_COLLECTION_TIMEOUT",
                    agent.agent_id,
                    {"timeout_seconds": COLLECTOR_TIMEOUT_SECONDS},
                    order_origin="SOMBRA_CORE",
                )
            except Exception as error:
                results[agent.agent_id] = []
                await agent.report_failure(error)
                await self.collector_scheduler._log_cycle(agent.agent_id, f"cycle_failed error={error!r}")
                await self.blackbox.log(
                    "INTEL_COLLECTION_ERROR",
                    agent.agent_id,
                    {"error": repr(error)},
                    order_origin="SOMBRA_CORE",
                )
        return results

    async def receive_order(self, raw_order: dict[str, Any]) -> dict[str, Any]:
        await self._ensure_database()
        processed = await self.cerebro_order_handler.handle_order(raw_order)
        if processed.get("accepted") and int(raw_order.get("force_lockdown", 0) or 0) >= 3:
            lockdown_event = await self.lockdown_protocol.activate(int(raw_order["force_lockdown"]), "CEO ordered resistance lockdown test")
            return {**processed, "execution": "lockdown_activated", "lockdown": lockdown_event}
        if processed.get("accepted") and processed.get("is_ceo_order"):
            await self.blackbox.log(
                "CEO_ORDER_EXECUTED",
                str(processed.get("order_id")),
                {"target": processed.get("target"), "order_type": processed.get("order_type")},
                order_origin="CEO",
            )
            return {**processed, "execution": "executed_immediately"}
        return {**processed, "execution": "queued_or_recorded"}

    async def get_status(self) -> dict[str, Any]:
        await self._ensure_database()
        modules_health = await self.health_monitor.check_all_modules()
        daily_summary = await self.metrics.get_daily_summary()
        active_identities = await self.identity_manager.get_all_active()
        heartbeat = self._read_last_heartbeat()
        return {
            "operational_status": self._overall_status_from_health(modules_health),
            "modules_health": modules_health,
            "alerts_today": daily_summary["alerts_generated_today"],
            "intel_processed_today": daily_summary["intel_processed_today"],
            "identities_active": len(active_identities),
            "lockdown_level": self.lockdown_protocol.get_current_level(),
            "last_heartbeat": heartbeat,
            "last_cycle_summary": self._last_cycle_summary,
            "database_backend": self.database.backend,
            "current_ai_cost_today_usd": await self.ai_cost_monitor.get_daily_cost(),
            "monthly_ai_projection_usd": await self.ai_cost_monitor.get_monthly_projection(),
            "budget_mode": self.model_router.mode,
            "ceo_risk_score": await self.ceo_protection_profile.get_ceo_risk_score(),
        }

    async def shutdown(self) -> None:
        await self._ensure_database()
        await self.blackbox.log(
            "SOMBRA_SHUTDOWN",
            "SOMBRA_CORE",
            {"pending_background_tasks": len(self._background_tasks)},
            order_origin="SOMBRA_CORE",
        )
        self.collector_scheduler.stop()
        for task in self._background_tasks:
            task.cancel()
        if self._background_tasks:
            await asyncio.gather(*self._background_tasks, return_exceptions=True)
        self._background_tasks.clear()
        self._started = False
        await self.database.disconnect()
        print("SOMBRA OFFLINE")

    async def _ensure_database(self) -> None:
        if self.database.connection is None:
            await self.database.connect()

    async def _transmit_cycle_result(self, memory_id: str, analysis: Any, alert: Any | None) -> int:
        transmissions = 0
        payload = {
            "memory_id": memory_id,
            "classified": analysis.classified.to_dict(),
            "score": analysis.score.to_dict(),
            "prediction": analysis.prediction.to_dict(),
            "alert": alert.to_dict() if alert is not None else None,
        }
        if alert is not None:
            await self.cerebro_connector.send_intel_report(alert)
            transmissions += 1
        else:
            await self.outbound_engine.transmit_to_cerebro(payload, analysis.classified.severity)
            transmissions += 1
        if alert is not None and "SENTINELA" in alert.route_to:
            await self.sentinela_connector.deliver_intel(alert)
            transmissions += 1
        if alert is not None and alert.forja_construction_needed:
            signal = self.forja_signal_builder.build_construction_signal(alert, alert.threat_type)
            await self.forja_connector.send_construction_signal(signal)
            transmissions += 1
        return transmissions

    async def _heartbeat_context(self) -> dict[str, Any]:
        return {
            "current_ai_cost_today_usd": await self.ai_cost_monitor.get_daily_cost(),
            "budget_mode": self.model_router.mode,
            "ceo_risk_score": await self.ceo_protection_profile.get_ceo_risk_score(),
        }

    async def _handle_ceo_personal_asset_alert(self, alert: Any) -> None:
        snapshot = await self.ceo_protection_profile.get_profile_snapshot()
        if snapshot["asset_counts"]["personal_emails"] == 0 and snapshot["asset_counts"]["domains_owned"] == 0:
            return
        profile = await self.ceo_protection_profile._load_profile()
        if not profile:
            return
        asset_terms = self.ceo_protection_profile._asset_terms(profile)
        alert_text = json.dumps(alert.to_dict(), ensure_ascii=True).lower()
        matched_assets = [asset for asset in asset_terms if asset.lower() in alert_text]
        if not matched_assets:
            return
        code = "A1-PARA-1" if getattr(alert, "severity", "") == "CRITICAL" else "A2-PARA-1"
        await self.ceo_alert_codes.send_ceo_alert(
            code,
            f"CEO protected asset affected by {getattr(alert, 'threat_type', 'UNKNOWN')}: {matched_assets[0]}",
            intel_reference=str(getattr(alert, "alert_id", "")),
        )

    @staticmethod
    def _should_generate_alert(analysis: Any, proactive: bool) -> bool:
        return proactive or analysis.score.final >= 50 or analysis.classified.severity in {"CRITICAL", "HIGH"}

    @staticmethod
    def _overall_status_from_health(modules_health: dict[str, dict[str, Any]]) -> str:
        statuses = [row["status"] for row in modules_health.values()]
        if "DOWN" in statuses:
            return "CRITICAL"
        if "DEGRADED" in statuses:
            return "DEGRADED"
        return "OPERATIONAL"

    @staticmethod
    def _read_last_heartbeat() -> dict[str, Any] | str:
        heartbeat_path = LOG_DIR / "heartbeat.log"
        if not heartbeat_path.exists():
            return ""
        try:
            return json.loads(heartbeat_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return heartbeat_path.read_text(encoding="utf-8", errors="replace")[-1000:]

    @staticmethod
    def _append_core_log(message: str) -> None:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        with Path(CORE_LOG).open("a", encoding="utf-8") as log_file:
            log_file.write(f"{SombraCore._now()} {message}\n")

    @staticmethod
    def _now() -> str:
        return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")

