from __future__ import annotations

import os
import sys
from typing import Any

from apps.sombra.memory import DatabaseConnection
from apps.sombra.memory.database import LOG_DIR


REQUIRED_ENV_VARS_DOCUMENTED = (
    "DATABASE_URL",
    "CEREBRO_WEBHOOK_URL",
    "SENTINELA_WEBHOOK_URL",
    "FORJA_WEBHOOK_URL",
    "CEO_EMERGENCY_WEBHOOK_URL",
    "SOMBRA_CLIENT_DOMAINS",
)
SENSITIVE_NAME_PARTS = ("PASSWORD", "SECRET", "TOKEN", "API_KEY", "PRIVATE_KEY")
DEFAULT_SECRET_VALUES = {"password", "admin", "changeme", "change_me", "default", "123456", "test", "example"}


class HardeningChecker:
    def __init__(self, database: DatabaseConnection | None = None) -> None:
        self.database = database if database is not None else DatabaseConnection()
        self._owns_connection = database is None

    async def disconnect(self) -> None:
        if self._owns_connection:
            await self.database.disconnect()

    async def run_checks(self) -> dict[str, Any]:
        checks_passed: list[str] = []
        checks_failed: list[str] = []
        recommendations: list[str] = []
        self._check_python_version(checks_passed, checks_failed, recommendations)
        self._check_environment_defaults(checks_passed, checks_failed, recommendations)
        self._check_log_directory(checks_passed, checks_failed, recommendations)
        await self._check_database_access(checks_passed, checks_failed, recommendations)
        self._check_required_env_vars_documented(checks_passed, checks_failed, recommendations)
        overall_status = self._overall_status(checks_failed, recommendations)
        return {
            "checks_passed": checks_passed,
            "checks_failed": checks_failed,
            "recommendations": recommendations,
            "overall_status": overall_status,
        }

    @staticmethod
    def _check_python_version(checks_passed: list[str], checks_failed: list[str], recommendations: list[str]) -> None:
        if sys.version_info >= (3, 11):
            checks_passed.append("python_version_3_11_or_newer")
        else:
            checks_failed.append("python_version_too_old")
            recommendations.append("Upgrade Python runtime to 3.11 or newer.")

    @staticmethod
    def _check_environment_defaults(checks_passed: list[str], checks_failed: list[str], recommendations: list[str]) -> None:
        weak_names: list[str] = []
        for name, value in os.environ.items():
            if not any(part in name.upper() for part in SENSITIVE_NAME_PARTS):
                continue
            normalized = value.strip().lower()
            if normalized in DEFAULT_SECRET_VALUES or normalized.startswith("changeme"):
                weak_names.append(name)
        if weak_names:
            checks_failed.append("default_secret_like_environment_values_detected")
            recommendations.append(f"Rotate weak environment values for: {', '.join(sorted(weak_names))}.")
        else:
            checks_passed.append("no_default_secret_like_environment_values_detected")

    @staticmethod
    def _check_log_directory(checks_passed: list[str], checks_failed: list[str], recommendations: list[str]) -> None:
        try:
            LOG_DIR.mkdir(parents=True, exist_ok=True)
            test_file = LOG_DIR / ".hardening_write_test"
            test_file.write_text("ok", encoding="utf-8")
            test_file.unlink(missing_ok=True)
        except OSError as error:
            checks_failed.append("log_directory_not_writable")
            recommendations.append(f"Repair log directory permissions: {error}.")
            return
        checks_passed.append("log_directory_exists_and_writable")

    async def _check_database_access(
        self,
        checks_passed: list[str],
        checks_failed: list[str],
        recommendations: list[str],
    ) -> None:
        try:
            if self.database.connection is None:
                await self.database.connect()
            await self.database.fetchrow("SELECT 1 AS ok")
        except Exception as error:
            checks_failed.append("database_not_accessible")
            recommendations.append(f"Repair SOMBRA database access: {error}.")
            return
        checks_passed.append(f"database_accessible_{self.database.backend}")

    @staticmethod
    def _check_required_env_vars_documented(
        checks_passed: list[str],
        checks_failed: list[str],
        recommendations: list[str],
    ) -> None:
        if REQUIRED_ENV_VARS_DOCUMENTED:
            checks_passed.append("required_environment_variables_documented_in_code")
        else:
            checks_failed.append("required_environment_variables_not_documented")
            recommendations.append("Document required runtime environment variables inside hardening checker.")

    @staticmethod
    def _overall_status(checks_failed: list[str], recommendations: list[str]) -> str:
        if checks_failed:
            return "FAIL"
        if recommendations:
            return "WARN"
        return "PASS"
