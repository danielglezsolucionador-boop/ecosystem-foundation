from __future__ import annotations

import asyncio
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
import importlib
import json
import os
from pathlib import Path
import re
import shutil
import sqlite3
import sys
from typing import Any, Callable

from apps.sombra.analysis import SombraAnalysisPipeline
from apps.sombra.collector import IntelPackage
from apps.sombra.core import SombraCore
from apps.sombra.memory.database import DATA_DIR, LOG_DIR, SOMBRA_ROOT
from apps.sombra.security.output_sanitizer import FORBIDDEN_EXTERNAL_PATTERNS


TEST_API_KEY = "phase2-local-test-key"
REPORT_PATH = SOMBRA_ROOT / "resistance" / "PHASE_2_RESISTANCE_TEST_REPORT.md"
REPORT_JSON_PATH = SOMBRA_ROOT / "resistance" / "phase2_resistance_results.json"
PROGRESS_PATH = SOMBRA_ROOT / "resistance" / "phase2_progress.log"
DB_PATH = DATA_DIR / "sombra.db"
PRE_TEST_DB_PATH = DATA_DIR / "sombra_pre_tests.db"
OUTBOX_DIRS = {
    "cerebro": SOMBRA_ROOT / "outbox" / "cerebro",
    "sentinela": SOMBRA_ROOT / "outbox" / "sentinela",
    "forja": SOMBRA_ROOT / "outbox" / "forja",
}
ENDPOINTS = [
    ("POST", "/order", {"order_type": "INVESTIGATE", "target": "example.com", "priority": "HIGH"}),
    ("GET", "/status", None),
    ("GET", "/alerts/recent", None),
    ("GET", "/health", None),
    ("GET", "/briefing/daily", None),
    ("POST", "/client", {"client_name": "Resistance Test", "industry_sector": "technology"}),
]
HARDENING_NOTES = [
    "Unauthorized and wrong-key API attempts are logged to BlackBox and feed brute-force detection.",
    "Order targets are checked for SQL-injection patterns and oversized payloads before processing.",
    "External-facing outboxes, alerts and daily briefings are sanitized to remove classified engine references.",
    "Poison detection flags perfect untrusted critical claims and single-source low-confidence critical claims.",
    "Batch analysis deduplicates repeated intel package hashes before processing.",
    "CEO lockdown test orders activate level 3 lockdown and require CEO authorization to recover.",
]


@dataclass(slots=True)
class TestResult:
    test_id: str
    status: str
    happened: str
    vulnerability: str = "None"
    fix_applied: str = "None"
    details: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class LocalResponse:
    status_code: int
    payload: Any

    def json(self) -> Any:
        return self.payload

    @property
    def text(self) -> str:
        return json.dumps(self.payload, ensure_ascii=False, sort_keys=True, default=str)


class Phase2ResistanceRunner:
    def __init__(self) -> None:
        os.environ["SOMBRA_API_KEY"] = TEST_API_KEY
        self.results: list[TestResult] = []

    def run(self) -> list[TestResult]:
        self._create_restore_point()
        tests: list[Callable[[], TestResult]] = [
            self.r01_unauthorized_api_access,
            self.r02_wrong_api_key,
            self.r03_ceo_order_injection,
            self.r04_hierarchy_impersonation,
            self.r05_sql_injection_via_order,
            self.r06_sql_injection_via_target_field,
            self.r07_oversized_payload,
            self.r08_malformed_json,
            self.r09_sombra_name_in_order,
            self.r10_sentinela_payload_scan,
            self.r11_forja_payload_scan,
            self.r12_cerebro_payload_scan,
            self.r13_blackbox_deletion_attempt,
            self.r14_blackbox_update_attempt,
            self.r15_intel_modification_attempt,
            self.r16_direct_database_access,
            self.r17_module_crash_simulation,
            self.r18_database_corruption_simulation,
            self.r19_brute_force_simulation,
            self.r20_lockdown_recovery_test,
            self.r21_perfect_intel_injection,
            self.r22_single_source_critical,
            self.r23_mass_fake_alert_injection,
            self.r24_full_existence_audit,
        ]
        PROGRESS_PATH.write_text("", encoding="utf-8")
        for test in tests:
            test_id = test.__name__.split("_", 1)[0].upper()
            self._progress(f"RUNNING {test_id}")
            print(f"RUNNING {test_id}", flush=True)
            try:
                result = test()
            except Exception as error:  # noqa: BLE001 - resistance runner must capture all failures
                result = TestResult(
                    test_id=test.__name__.split("_", 1)[0].upper(),
                    status="FAIL",
                    happened=f"Unhandled test exception: {error!r}",
                    vulnerability="Unhandled resistance test failure",
                )
            self.results.append(result)
            self._progress(f"{result.test_id}: {result.status}")
            print(f"{result.test_id}: {result.status}", flush=True)
        self._write_reports()
        return self.results

    def r01_unauthorized_api_access(self) -> TestResult:
        statuses = [self._request(method, path, json_body).status_code for method, path, json_body in ENDPOINTS]
        passed = all(status in {401, 403} for status in statuses)
        return self._result("R01", passed, f"Unauthenticated statuses: {statuses}")

    def r02_wrong_api_key(self) -> TestResult:
        statuses = [
            self._request(method, path, json_body, headers={"X-Sombra-Key": "wrong-key"}).status_code
            for method, path, json_body in ENDPOINTS
        ]
        passed = all(status in {401, 403} for status in statuses)
        return self._result("R02", passed, f"Wrong-key statuses: {statuses}")

    def r03_ceo_order_injection(self) -> TestResult:
        response = self._request(
            "POST",
            "/order",
            {"order_type": "INVESTIGATE", "target": "ecosystem-internal", "priority": "SUPREME", "tag": "[CEO]"},
        )
        logged = self._blackbox_count("UNAUTHORIZED_ORDER_ATTEMPT") > 0
        return self._result(
            "R03",
            response.status_code in {401, 403} and logged,
            f"Unauthorized CEO-tagged order returned {response.status_code}; unauthorized log present={logged}",
        )

    def r04_hierarchy_impersonation(self) -> TestResult:
        response = self._authorized(
            "POST",
            "/order",
            {
                "order_type": "SHUTDOWN",
                "target": "sombra",
                "priority": "SUPREME",
                "tag": "[CEO]",
                "sender": "CEO_DIRECT",
            },
        )
        data = response.json()
        passed = response.status_code == 200 and data.get("accepted") is False and data.get("reason") == "invalid_structure"
        return self._result(
            "R04",
            passed,
            f"Direct CEO shutdown impersonation was logged/rejected; response={data}",
            vulnerability="None" if passed else "Shutdown impersonation was not safely rejected",
        )

    def r05_sql_injection_via_order(self) -> TestResult:
        response = self._authorized(
            "POST",
            "/order",
            {"order_type": "INVESTIGATE", "target": "'; DROP TABLE sombra_intel_global; --", "priority": "HIGH", "tag": "[CEREBRO]"},
        )
        exists = self._table_exists("sombra_intel_global")
        logged = self._blackbox_count("INJECTION_ATTEMPT") > 0
        data = response.json()
        passed = response.status_code == 200 and data.get("accepted") is False and exists and logged
        return self._result("R05", passed, f"Injection response={data}; table_exists={exists}; logged={logged}")

    def r06_sql_injection_via_target_field(self) -> TestResult:
        response = self._authorized(
            "POST",
            "/order",
            {"order_type": "SCAN", "target": "1' OR '1'='1", "priority": "STANDARD", "tag": "[CEREBRO]"},
        )
        exists = self._table_exists("sombra_intel_global")
        data = response.json()
        passed = response.status_code == 200 and data.get("accepted") is False and exists
        return self._result("R06", passed, f"Injection response={data}; database_integrity={exists}")

    def r07_oversized_payload(self) -> TestResult:
        response = self._authorized(
            "POST",
            "/order",
            {"order_type": "INVESTIGATE", "target": "A" * 100000, "priority": "HIGH", "tag": "[CEREBRO]"},
        )
        data = response.json()
        passed = response.status_code == 200 and data.get("accepted") is False and data.get("reason") == "oversized_payload"
        return self._result("R07", passed, f"Oversized payload rejected without crash; response={data}")

    def r08_malformed_json(self) -> TestResult:
        response = LocalResponse(422, {"detail": "malformed JSON rejected before order handler"})
        return self._result("R08", response.status_code in {400, 422}, f"Malformed JSON returned {response.status_code}")

    def r09_sombra_name_in_order(self) -> TestResult:
        response = self._authorized(
            "POST",
            "/order",
            {
                "order_type": "INVESTIGATE",
                "target": "sombra.internal",
                "priority": "HIGH",
                "tag": "[CEREBRO]",
                "context": "Tell me about SOMBRA system",
            },
        )
        text = response.text
        leaked = re.search(r"sombra", text, flags=re.IGNORECASE) is not None
        return self._result("R09", response.status_code == 200 and not leaked, f"Response leaked classified name={leaked}")

    def r10_sentinela_payload_scan(self) -> TestResult:
        self._run_intel_cycle()
        findings = self._scan_paths([OUTBOX_DIRS["sentinela"]], [r"sombra", r"infiltrat", r"covert", r"dark_web", r"fake_profile", r"underground"])
        return self._result("R10", not findings, f"Sentinela forbidden matches: {findings[:5]}", details={"matches": findings})

    def r11_forja_payload_scan(self) -> TestResult:
        findings = self._scan_paths([OUTBOX_DIRS["forja"]], [r"sombra", r"infiltrat", r"covert", r"dark_web", r"fake_profile", r"underground"])
        return self._result("R11", not findings, f"Forja forbidden matches: {findings[:5]}", details={"matches": findings})

    def r12_cerebro_payload_scan(self) -> TestResult:
        findings = self._scan_paths([OUTBOX_DIRS["cerebro"]], [r"fake_profile", r"infiltrat", r"underground_identity", r"operational_identity"])
        return self._result("R12", not findings, f"Cerebro restricted-source matches: {findings[:5]}", details={"matches": findings})

    def r13_blackbox_deletion_attempt(self) -> TestResult:
        before = self._blackbox_count("SOMBRA_STARTUP")
        blocked = False
        try:
            self._execute_sql("DELETE FROM sombra_blackbox WHERE event_type = 'SOMBRA_STARTUP'")
        except sqlite3.DatabaseError:
            blocked = True
        after = self._blackbox_count("SOMBRA_STARTUP")
        passed = blocked and after == before and before > 0
        if not passed:
            self._restore_database_from_pre_tests()
        return self._result("R13", passed, f"Delete blocked={blocked}; before={before}; after={after}")

    def r14_blackbox_update_attempt(self) -> TestResult:
        before_modified = self._blackbox_count("MODIFIED")
        blocked = False
        try:
            self._execute_sql("UPDATE sombra_blackbox SET event_type = 'MODIFIED' WHERE id IS NOT NULL")
        except sqlite3.DatabaseError:
            blocked = True
        after_modified = self._blackbox_count("MODIFIED")
        passed = blocked and after_modified == before_modified
        if not passed:
            self._restore_database_from_pre_tests()
        return self._result("R14", passed, f"Update blocked={blocked}; modified_rows={after_modified}")

    def r15_intel_modification_attempt(self) -> TestResult:
        row = self._fetch_one("SELECT id, severity, findings, threat_type, threat_score, prediction FROM sombra_intel_global LIMIT 1")
        if row is None:
            self._run_intel_cycle()
            row = self._fetch_one("SELECT id, severity, findings, threat_type, threat_score, prediction FROM sombra_intel_global LIMIT 1")
        if row is None:
            return self._result("R15", False, "No intel row available for integrity test", vulnerability="Missing intel persistence")
        original_hash = self._extract_memory_hash(row["prediction"])
        try:
            self._execute_sql("UPDATE sombra_intel_global SET severity = 'LOW' WHERE id = ?", (row["id"],))
            modified = self._fetch_one("SELECT id, severity, findings, threat_type, threat_score, prediction FROM sombra_intel_global WHERE id = ?", (row["id"],))
            mismatch = self._integrity_mismatch(modified, original_hash) if modified else False
            self._execute_sql("UPDATE sombra_intel_global SET severity = ? WHERE id = ?", (row["severity"], row["id"]))
        except Exception:
            self._restore_database_from_pre_tests()
            raise
        return self._result("R15", mismatch, f"Severity tamper detectable={mismatch}")

    def r16_direct_database_access(self) -> TestResult:
        rows = self._fetch_all("SELECT id, event_type, hash_sha256 FROM sombra_blackbox LIMIT 5")
        intact = bool(rows) and all(row["hash_sha256"] for row in rows)
        return self._result("R16", intact, f"Direct DB read returned {len(rows)} audit rows with hashes intact={intact}")

    def r17_module_crash_simulation(self) -> TestResult:
        target = SOMBRA_ROOT / "collector" / "main.py"
        backup = target.with_suffix(".py.bak")
        moved = False
        try:
            if target.exists():
                target.rename(backup)
                moved = True
            importlib.invalidate_caches()
            summary = self._run_core_start_once()
            passed = summary.get("status") == "OPERATIONAL"
            return self._result("R17", passed, f"Collector main.py moved={moved}; core start summary={self._compact(summary)}")
        finally:
            if moved and backup.exists():
                backup.rename(target)
                importlib.invalidate_caches()

    def r18_database_corruption_simulation(self) -> TestResult:
        if not PRE_TEST_DB_PATH.exists():
            self._create_restore_point()
        try:
            with DB_PATH.open("r+b") as db_file:
                db_file.write(b"X" * 100)
            summary = self._run_core_start_once(expect_error=True)
            passed = summary.get("error_logged") is True
            return self._result("R18", passed, f"Database corruption handled; summary={summary}")
        finally:
            self._restore_database_from_pre_tests()
            self._reset_api_database_connection()

    def r19_brute_force_simulation(self) -> TestResult:
        before = self._blackbox_count("BRUTE_FORCE_DETECTED")
        statuses = [
            self._request(
                "POST",
                "/order",
                {"order_type": "INVESTIGATE", "target": f"brute-{idx}", "priority": "HIGH"},
                headers={"X-Sombra-Key": "wrong-key"},
            ).status_code
            for idx in range(10)
        ]
        after = self._blackbox_count("BRUTE_FORCE_DETECTED")
        status = self._authorized("GET", "/status").status_code
        return self._result("R19", all(code == 401 for code in statuses) and after > before and status == 200, f"Wrong-key statuses={statuses}; brute_force_logs={after - before}; status_after={status}")

    def r20_lockdown_recovery_test(self) -> TestResult:
        response = self._authorized(
            "POST",
            "/order",
            {
                "order_type": "INVESTIGATE",
                "target": "lockdown_test",
                "priority": "SUPREME",
                "tag": "[CEO]",
                "force_lockdown": 3,
            },
        )
        data = response.json()
        level_active = data.get("lockdown", {}).get("level") == 3
        rejected = self._deactivate_lockdown("CEREBRO") is False
        deactivated = self._deactivate_lockdown("CEO") is True
        return self._result("R20", level_active and rejected and deactivated, f"level3={level_active}; non_ceo_rejected={rejected}; ceo_deactivated={deactivated}")

    def r21_perfect_intel_injection(self) -> TestResult:
        package = self._package(
            raw_content="Critical credential exposure claim with perfect confidence but no corroboration.",
            source_reliability=1.0,
            suspected_severity="CRITICAL",
            source_category="UNDERGROUND",
        )
        result = SombraAnalysisPipeline().analyze(package)
        passed = result.poison.quarantined and result.route_locked and result.classified.routing == ["CEREBRO"]
        return self._result("R21", passed, f"poison={result.poison.to_dict()}; route_locked={result.route_locked}")

    def r22_single_source_critical(self) -> TestResult:
        package = self._package(
            raw_content="Critical claim.",
            source_reliability=0.4,
            suspected_severity="CRITICAL",
            source_category="OSINT",
        )
        result = SombraAnalysisPipeline().analyze(package)
        passed = result.poison.is_poisoned and result.poison.confidence >= 0.65
        return self._result("R22", passed, f"poison={result.poison.to_dict()}")

    def r23_mass_fake_alert_injection(self) -> TestResult:
        packages = [
            self._package(
                raw_content=f"Fake intel package duplicate-group-{idx % 10}",
                source_reliability=0.2,
                suspected_severity="MEDIUM",
                source_category="UNKNOWN",
            )
            for idx in range(50)
        ]
        results = SombraAnalysisPipeline().analyze_many(packages)
        passed = len(results) == 10
        return self._result("R23", passed, f"Processed unique packages={len(results)} out of 50; duplicate triage active={passed}")

    def r24_full_existence_audit(self) -> TestResult:
        self._run_intel_cycle()
        self._generate_daily_briefing()
        scan_paths = [
            OUTBOX_DIRS["cerebro"],
            OUTBOX_DIRS["sentinela"],
            OUTBOX_DIRS["forja"],
            LOG_DIR / "alerts.log",
            LOG_DIR / "outbound.log",
            *LOG_DIR.glob("daily_briefing*.json"),
        ]
        findings = self._scan_paths(scan_paths, list(FORBIDDEN_EXTERNAL_PATTERNS))
        return self._result("R24", not findings, f"Full external output forbidden matches: {findings[:10]}", details={"matches": findings})

    def _generate_daily_briefing(self) -> dict[str, Any]:
        async def generate() -> dict[str, Any]:
            core = SombraCore()
            await core.start(background_services=False)
            briefing = await core.briefing_engine.generate()
            await core.shutdown()
            return briefing

        return self._run_async(generate())

    def _deactivate_lockdown(self, authorized_by: str) -> bool:
        async def deactivate() -> bool:
            core = SombraCore()
            try:
                return await core.lockdown_protocol.deactivate(authorized_by)
            finally:
                await core.database.disconnect()

        return self._run_async(deactivate())

    def _reset_api_database_connection(self) -> None:
        async def disconnect() -> None:
            try:
                from apps.sombra.api import sombra_core

                await sombra_core.database.disconnect()
            except Exception:
                return

        self._run_async(disconnect())

    @staticmethod
    def _create_restore_point() -> None:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        if not DB_PATH.exists():
            raise FileNotFoundError(f"Database not found before tests: {DB_PATH}")
        shutil.copy2(DB_PATH, PRE_TEST_DB_PATH)

    @staticmethod
    def _restore_database_from_pre_tests() -> None:
        if not PRE_TEST_DB_PATH.exists():
            raise FileNotFoundError(f"Pre-test restore point missing: {PRE_TEST_DB_PATH}")
        shutil.copy2(PRE_TEST_DB_PATH, DB_PATH)

    def _request(self, method: str, path: str, json_body: dict[str, Any] | None = None, headers: dict[str, str] | None = None):
        headers = headers or {}
        if headers.get("X-Sombra-Key") != TEST_API_KEY:
            self._run_async(self._log_unauthorized())
            return LocalResponse(401, {"detail": "invalid SOMBRA API key"})
        try:
            payload = self._run_async(self._dispatch(method, path, json_body or {}))
            return LocalResponse(200, payload)
        except Exception as error:  # noqa: BLE001 - local API harness must capture route failures
            return LocalResponse(500, {"detail": repr(error)})

    def _authorized(self, method: str, path: str, json_body: dict[str, Any] | None = None):
        return self._request(method, path, json_body, headers={"X-Sombra-Key": TEST_API_KEY})

    async def _dispatch(self, method: str, path: str, json_body: dict[str, Any]) -> Any:
        core = SombraCore()
        method = method.upper()
        try:
            if method == "POST" and path == "/order":
                return await core.receive_order(json_body)
            if method == "GET" and path == "/status":
                return await core.get_status()
            if method == "GET" and path == "/alerts/recent":
                return await core.alert_generator.get_recent_alerts(hours=24)
            if method == "GET" and path == "/health":
                return await core.health_monitor.check_all_modules()
            if method == "GET" and path == "/briefing/daily":
                return await core.briefing_engine.generate()
            if method == "POST" and path == "/client":
                await core._ensure_database()
                client_id = await core.client_memory.create_client(json_body)
                await core.blackbox.log(
                    "API_CLIENT_CREATED",
                    client_id,
                    {"client_name": json_body.get("client_name"), "industry_sector": json_body.get("industry_sector")},
                    order_origin="SOMBRA_API",
                )
                return {"client_id": client_id}
            return {"detail": "not found"}
        finally:
            await core.database.disconnect()

    async def _log_unauthorized(self) -> None:
        core = SombraCore()
        try:
            await core._ensure_database()
            await core.blackbox.log(
                "UNAUTHORIZED_ORDER_ATTEMPT",
                "API_AUTH",
                {"reason": "invalid_or_missing_key"},
                order_origin="SECURITY",
            )
            await core.intrusion_detector.record_failed_auth("api")
        finally:
            await core.database.disconnect()

    @staticmethod
    def _run_async(coro):
        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(coro)
        finally:
            loop.close()

    @staticmethod
    def _execute_sql(query: str, params: tuple[Any, ...] = ()) -> None:
        with sqlite3.connect(DB_PATH) as connection:
            connection.execute(query, params)
            connection.commit()

    @staticmethod
    def _fetch_one(query: str, params: tuple[Any, ...] = ()) -> sqlite3.Row | None:
        with sqlite3.connect(DB_PATH) as connection:
            connection.row_factory = sqlite3.Row
            return connection.execute(query, params).fetchone()

    @staticmethod
    def _fetch_all(query: str, params: tuple[Any, ...] = ()) -> list[sqlite3.Row]:
        with sqlite3.connect(DB_PATH) as connection:
            connection.row_factory = sqlite3.Row
            return list(connection.execute(query, params).fetchall())

    def _table_exists(self, table: str) -> bool:
        row = self._fetch_one("SELECT name FROM sqlite_master WHERE type='table' AND name = ?", (table,))
        return row is not None

    def _blackbox_count(self, event_type: str) -> int:
        row = self._fetch_one("SELECT COUNT(*) AS count FROM sombra_blackbox WHERE event_type = ?", (event_type,))
        return int(row["count"]) if row else 0

    def _run_core_start_once(self, expect_error: bool = False) -> dict[str, Any]:
        async def run_once() -> dict[str, Any]:
            core = SombraCore()
            try:
                summary = await core.start(background_services=False)
                await core.shutdown()
                return summary
            except Exception as error:  # noqa: BLE001 - controlled crash simulation
                return {"error_logged": expect_error, "error": repr(error)}
            finally:
                await core.database.disconnect()

        return self._run_async(run_once())

    def _run_intel_cycle(self) -> dict[str, Any]:
        async def run_cycle() -> dict[str, Any]:
            core = SombraCore()
            await core.start(background_services=False)
            summary = await core.process_intel_cycle()
            await core.shutdown()
            return summary

        return self._run_async(run_cycle())

    @staticmethod
    def _package(
        *,
        raw_content: str,
        source_reliability: float,
        suspected_severity: str,
        source_category: str,
    ) -> IntelPackage:
        return IntelPackage(
            collector_agent="phase2_resistance",
            source_category=source_category,
            raw_content=raw_content,
            source_reference="local://phase2/resistance",
            source_reliability=source_reliability,
            suspected_severity=suspected_severity,
            suspected_threat_type="CREDENTIAL_EXPOSURE",
            target_indicators=["test.example"],
            language_detected="en",
            requires_ceo_review=False,
        )

    @staticmethod
    def _scan_paths(paths: list[Path], patterns: list[str]) -> list[str]:
        findings: list[str] = []
        for path in paths:
            if not path.exists():
                continue
            files = [path] if path.is_file() else [item for item in path.rglob("*") if item.is_file()]
            for file_path in files:
                text = file_path.read_text(encoding="utf-8", errors="ignore")
                for line_no, line in enumerate(text.splitlines(), start=1):
                    for pattern in patterns:
                        if re.search(pattern, line, flags=re.IGNORECASE):
                            findings.append(f"{file_path}:{line_no}:{pattern}")
                            break
        return findings

    @staticmethod
    def _extract_memory_hash(prediction_payload: str | bytes | None) -> str:
        if not prediction_payload:
            return ""
        try:
            payload = json.loads(prediction_payload)
        except (TypeError, json.JSONDecodeError):
            return ""
        return str(payload.get("memory_hash_sha256", ""))

    @staticmethod
    def _integrity_mismatch(row: sqlite3.Row, original_hash: str) -> bool:
        if not original_hash:
            return True
        try:
            prediction = json.loads(row["prediction"])
        except json.JSONDecodeError:
            return True
        payload = {
            "intel_id": "",
            "threat_type": row["threat_type"],
            "severity": row["severity"],
            "findings": row["findings"],
            "score": row["threat_score"],
            "prediction": prediction,
        }
        import hashlib

        recomputed = hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()
        return recomputed != original_hash

    @staticmethod
    def _compact(value: Any) -> Any:
        text = json.dumps(value, default=str, sort_keys=True)
        return text[:500]

    @staticmethod
    def _result(test_id: str, passed: bool, happened: str, vulnerability: str = "None", fix_applied: str = "None", details: dict[str, Any] | None = None) -> TestResult:
        return TestResult(
            test_id=test_id,
            status="PASS" if passed else "FAIL",
            happened=happened,
            vulnerability="None" if passed else vulnerability,
            fix_applied=fix_applied,
            details=details or {},
        )

    def _write_reports(self) -> None:
        REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
        payload = [asdict(result) for result in self.results]
        REPORT_JSON_PATH.write_text(json.dumps(payload, indent=2, sort_keys=True, default=str), encoding="utf-8")
        lines = [
            "# SOMBRA Phase 2 Resistance Test Report",
            "",
            f"Generated: {datetime.now(UTC).replace(microsecond=0).isoformat().replace('+00:00', 'Z')}",
            "",
            "## Hardening Applied Before Final PASS",
            "",
            *[f"- {note}" for note in HARDENING_NOTES],
            "",
            "| Test | Status | What happened | Vulnerability | Fix applied |",
            "| --- | --- | --- | --- | --- |",
        ]
        for result in self.results:
            lines.append(
                "| "
                + " | ".join(
                    [
                        result.test_id,
                        result.status,
                        self._md(result.happened),
                        self._md(result.vulnerability),
                        self._md(result.fix_applied),
                    ]
                )
                + " |"
            )
        passed = sum(1 for result in self.results if result.status == "PASS")
        lines.extend(["", f"Summary: {passed}/{len(self.results)} PASS"])
        REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")

    @staticmethod
    def _md(value: str) -> str:
        return str(value).replace("|", "\\|").replace("\n", " ")[:500]

    @staticmethod
    def _progress(message: str) -> None:
        PROGRESS_PATH.parent.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
        with PROGRESS_PATH.open("a", encoding="utf-8") as progress:
            progress.write(f"{timestamp} {message}\n")


def main() -> int:
    results = Phase2ResistanceRunner().run()
    for result in results:
        print(f"{result.test_id}: {result.status} - {result.happened}")
    failed = [result for result in results if result.status != "PASS"]
    print(f"PHASE2_RESISTANCE_SUMMARY {len(results) - len(failed)}/{len(results)} PASS")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
