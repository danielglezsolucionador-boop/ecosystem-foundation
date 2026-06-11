from __future__ import annotations

import importlib
from pathlib import Path
from typing import Any

from apps.sombra.memory.database import LOG_DIR, SOMBRA_ROOT


MODULES = {
    "collector": {
        "files": ["collector/base_agent.py", "collector/main.py", "collector/scheduler.py"],
        "logs": ["scheduler.log", "sombra_collector.log"],
    },
    "analysis": {
        "files": ["analysis/pipeline.py", "analysis/classifier.py", "analysis/scorer.py"],
        "logs": [],
    },
    "memory": {
        "files": ["memory/database.py", "memory/global_memory.py", "memory/query_engine.py"],
        "logs": ["memory_database.log"],
    },
    "identity": {
        "files": ["identity/manager.py", "identity/lifecycle.py", "identity/compartment_checker.py"],
        "logs": [],
    },
    "communication": {
        "files": ["communication/outbound.py", "communication/inbound.py", "communication/queue_manager.py"],
        "logs": ["outbound.log", "inbound.log", "CEO_EMERGENCY.log"],
    },
    "alerts": {
        "files": ["alerts/generator.py", "alerts/proactive.py", "alerts/briefing.py"],
        "logs": ["alerts.log", "proactive.log"],
    },
    "security": {
        "files": ["security/intrusion_detector.py", "security/lockdown.py", "security/hardening_checker.py"],
        "logs": ["security.log"],
    },
}


class SombraHealthMonitor:
    async def check_module_health(self, module_name: str) -> dict[str, Any]:
        normalized = module_name.lower()
        config = MODULES.get(normalized)
        if config is None:
            return {
                "module": module_name,
                "status": "DOWN",
                "last_log_entry": "",
                "details": "unknown module",
            }
        import_ok, import_error = self._can_import(normalized)
        missing_files = [file for file in config["files"] if not (SOMBRA_ROOT / file).exists()]
        last_log_entry = self._last_log_entry(config["logs"])
        if not import_ok or missing_files:
            return {
                "module": normalized,
                "status": "DOWN",
                "last_log_entry": last_log_entry,
                "details": f"import_ok={import_ok}; import_error={import_error}; missing_files={missing_files}",
            }
        if config["logs"] and not last_log_entry:
            return {
                "module": normalized,
                "status": "DEGRADED",
                "last_log_entry": "",
                "details": "key files present and importable; no recent log entries found",
            }
        if not config["logs"]:
            return {
                "module": normalized,
                "status": "HEALTHY",
                "last_log_entry": "",
                "details": "key files present and importable; module has no required log writer",
            }
        return {
            "module": normalized,
            "status": "HEALTHY",
            "last_log_entry": last_log_entry,
            "details": "key files present, importable, logs active",
        }

    async def check_all_modules(self) -> dict[str, dict[str, Any]]:
        matrix: dict[str, dict[str, Any]] = {}
        for module_name in MODULES:
            matrix[module_name] = await self.check_module_health(module_name)
        return matrix

    async def get_overall_status(self) -> str:
        matrix = await self.check_all_modules()
        statuses = [row["status"] for row in matrix.values()]
        if "DOWN" in statuses:
            return "CRITICAL"
        if "DEGRADED" in statuses:
            return "DEGRADED"
        return "FULLY_OPERATIONAL"

    @staticmethod
    def _can_import(module_name: str) -> tuple[bool, str]:
        try:
            importlib.import_module(f"apps.sombra.{module_name}")
        except Exception as error:
            return False, repr(error)
        return True, ""

    @staticmethod
    def _last_log_entry(log_names: list[str]) -> str:
        entries: list[tuple[float, str]] = []
        for log_name in log_names:
            path = LOG_DIR / log_name
            if not path.exists() or path.stat().st_size == 0:
                continue
            lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
            if lines:
                entries.append((path.stat().st_mtime, lines[-1]))
        if not entries:
            return ""
        return sorted(entries, key=lambda item: item[0], reverse=True)[0][1]
