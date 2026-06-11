from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta
import json
import os
from pathlib import Path
import sys
import tempfile
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from apps.sombra.alerts.briefing import DailyIntelligenceBriefing
from apps.sombra.communication.ceo_alert_codes import CEOAlertCodeSystem
from apps.sombra.integrations.cerebro_report_formatter import CerebroReportFormatter
from apps.sombra.memory.blackbox import BlackBoxAuditCore
from apps.sombra.memory.ceo_protection import CEOProtectionProfile
from apps.sombra.memory.database import DatabaseConnection
from apps.sombra.monitoring.ai_cost_monitor import AICostMonitor
from apps.sombra.monitoring.model_router import ModelRouter


async def run_tests() -> dict[str, Any]:
    previous_budget = os.environ.get("SOMBRA_AI_BUDGET_USD")
    os.environ["SOMBRA_AI_BUDGET_USD"] = "300"
    with tempfile.TemporaryDirectory(prefix="sombra_cost_ceo_") as temp_dir:
        database = DatabaseConnection(sqlite_path=Path(temp_dir) / "sombra_cost_ceo_tests.db")
        await database.connect()
        blackbox = BlackBoxAuditCore(database)
        model_router = ModelRouter(database, blackbox)
        cost_monitor = AICostMonitor(database, blackbox, model_router)
        ceo_alerts = CEOAlertCodeSystem(database, blackbox)
        ceo_profile = CEOProtectionProfile(database, blackbox)
        briefing = DailyIntelligenceBriefing(database, cost_monitor, model_router, ceo_profile)
        results: dict[str, Any] = {
            "tests": {},
            "samples": {},
            "database": str(database.sqlite_path),
        }
        try:
            usage_samples = [
                await cost_monitor.record_usage("claude-haiku-4-5", 1_000, 500, "bulk_classification"),
                await cost_monitor.record_usage("claude-sonnet-4-6", 2_000, 1_000, "standard_analysis"),
                await cost_monitor.record_usage("ollama_llama3", 100_000, 100_000, "offline_fallback"),
            ]
            daily_cost = await cost_monitor.get_daily_cost()
            monthly_total = await cost_monitor.get_monthly_total()
            heartbeat_payload = CerebroReportFormatter.format_heartbeat(
                status="OPERATIONAL",
                intel_processed_today=0,
                alerts_sent_today=0,
                lockdown_level=0,
                current_ai_cost_today_usd=daily_cost,
                budget_mode=model_router.mode,
                ceo_risk_score=0,
            )
            results["tests"]["TEST 1 - COST TRACKING"] = _pass(
                daily_cost > 0
                and monthly_total >= daily_cost
                and "current_ai_cost_today_usd" in heartbeat_payload
            )
            results["samples"]["cost_usage"] = usage_samples
            results["samples"]["heartbeat_cost_fields"] = {
                "current_ai_cost_today_usd": heartbeat_payload["current_ai_cost_today_usd"],
                "budget_mode": heartbeat_payload["budget_mode"],
                "ceo_risk_score": heartbeat_payload["ceo_risk_score"],
            }

            await model_router.set_mode_async("ECONOMY", reason="integration_test")
            economy_model = model_router.get_model("standard_analysis")
            await model_router.set_mode_async("NORMAL", reason="integration_test_reset")
            results["tests"]["TEST 2 - MODEL ROUTER"] = _pass(economy_model == "claude-haiku-4-5")
            results["samples"]["model_router"] = {"economy_standard_analysis": economy_model, "final_mode": model_router.mode}

            cost_monitor.monthly_budget_usd = 1.00
            await cost_monitor.record_usage("claude-haiku-4-5", 850_000, 0, "budget_warning_test")
            warning_rows = await database.fetch(
                """
                SELECT *
                FROM sombra_blackbox
                WHERE event_type = 'AI_BUDGET_WARNING'
                ORDER BY timestamp_utc DESC
                LIMIT 1
                """
            )
            results["tests"]["TEST 3 - BUDGET WARNING"] = _pass(bool(warning_rows) and model_router.mode == "ECONOMY")
            results["samples"]["budget_warning"] = {
                "router_mode": model_router.mode,
                "monthly_total_usd": await cost_monitor.get_monthly_total(),
                "budget_limit_usd": cost_monitor.monthly_budget_usd,
            }

            a1_alert = await ceo_alerts.send_ceo_alert(
                "A1-PARA-1",
                "TEST: CEO credentials scan completed clean",
                intel_reference="test-a1",
            )
            a1_queue = await _latest_outbound(database, "SUPREME")
            a1_blackbox = await _latest_blackbox(database, "CEO_ALERT_SENT")
            results["tests"]["TEST 4 - CEO ALERT A1"] = _pass(
                a1_alert.get("priority") == "SUPREME" and bool(a1_queue) and bool(a1_blackbox)
            )
            results["samples"]["a1_alert_package"] = a1_alert

            a2_alert = await ceo_alerts.send_ceo_alert(
                "A2-PARA-1",
                "TEST: Directed threat detected - monitoring elevated",
                intel_reference="test-a2",
            )
            a2_queue = await _latest_outbound(database, "CRITICAL")
            results["tests"]["TEST 5 - CEO ALERT A2"] = _pass(
                a2_alert.get("priority") == "CRITICAL" and a2_alert["sms_text"].startswith("A2-PARA-1:") and bool(a2_queue)
            )
            results["samples"]["a2_alert_sms_text"] = a2_alert["sms_text"]

            resend_alert = await ceo_alerts.send_ceo_alert(
                "A1-PARA-1",
                "TEST: Unacknowledged alert resend path",
                intel_reference="test-resend",
            )
            old_time = (datetime.now(UTC) - timedelta(minutes=11)).replace(microsecond=0).isoformat().replace("+00:00", "Z")
            await database.execute(
                """
                UPDATE sombra_ceo_alerts
                SET last_sent_at = $1
                WHERE alert_id = $2
                """,
                old_time,
                resend_alert["alert_id"],
            )
            resent = await ceo_alerts.check_unacknowledged()
            results["tests"]["TEST 6 - UNACKNOWLEDGED CHECK"] = _pass(
                any(item.get("alert_id") == resend_alert["alert_id"] for item in resent)
            )
            results["samples"]["resent_alerts_count"] = len(resent)

            profile_scan = await ceo_profile.initialize_ceo_profile(
                personal_emails=["test@test.com"],
                domains=["test-domain.com"],
                social_profiles=["linkedin/test"],
            )
            risk_score = await ceo_profile.get_ceo_risk_score()
            results["tests"]["TEST 7 - CEO PROFILE"] = _pass(
                profile_scan["status"] in {"CLEAN_LOCAL_SCAN", "EXPOSURE_FOUND"} and isinstance(risk_score, int)
            )
            results["samples"]["ceo_profile_scan"] = profile_scan

            daily_briefing = await briefing.generate()
            ai_status = daily_briefing["operational_status"]["ai_cost_control"]
            protection_status = daily_briefing["operational_status"]["ceo_protection"]
            results["tests"]["TEST 8 - DAILY BRIEFING WITH COSTS"] = _pass(
                "daily_ai_cost_usd" in ai_status
                and "monthly_projection_usd" in ai_status
                and "budget_mode" in ai_status
                and "ceo_risk_score" in protection_status
            )
            results["samples"]["daily_briefing_costs"] = {
                "ai_cost_control": ai_status,
                "ceo_protection": protection_status,
            }

            results["summary"] = {
                "passed": sum(1 for item in results["tests"].values() if item["status"] == "PASS"),
                "total": len(results["tests"]),
                "blackbox_entries": await _blackbox_count(database),
            }
        finally:
            await database.disconnect()
            if previous_budget is None:
                os.environ.pop("SOMBRA_AI_BUDGET_USD", None)
            else:
                os.environ["SOMBRA_AI_BUDGET_USD"] = previous_budget
        return results


def _pass(condition: bool) -> dict[str, str]:
    return {"status": "PASS" if condition else "FAIL"}


async def _latest_outbound(database: DatabaseConnection, priority: str) -> dict[str, Any] | None:
    return await database.fetchrow(
        """
        SELECT *
        FROM sombra_outbound_queue
        WHERE priority = $1
        ORDER BY timestamp_utc DESC
        LIMIT 1
        """,
        priority,
    )


async def _latest_blackbox(database: DatabaseConnection, event_type: str) -> dict[str, Any] | None:
    return await database.fetchrow(
        """
        SELECT *
        FROM sombra_blackbox
        WHERE event_type = $1
        ORDER BY timestamp_utc DESC
        LIMIT 1
        """,
        event_type,
    )


async def _blackbox_count(database: DatabaseConnection) -> int:
    row = await database.fetchrow("SELECT COUNT(*) AS count FROM sombra_blackbox")
    return int((row or {}).get("count") or 0)


if __name__ == "__main__":
    print(json.dumps(asyncio.run(run_tests()), indent=2, sort_keys=True, default=str))
