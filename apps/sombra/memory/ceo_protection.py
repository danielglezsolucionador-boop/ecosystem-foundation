from __future__ import annotations

from copy import deepcopy
from datetime import UTC, datetime
import base64
import hashlib
import json
import os
from typing import Any

from cryptography.fernet import Fernet

from apps.sombra.communication.ceo_alert_codes import CEOAlertCodeSystem
from apps.sombra.memory.blackbox import BlackBoxAuditCore
from apps.sombra.memory.database import DatabaseConnection


CEO_PROFILE_SCHEMA = {
    "ceo_id": "1",
    "protection_level": "MAXIMUM",
    "digital_assets": {
        "personal_emails": [],
        "professional_emails": [],
        "domains_owned": [],
        "social_profiles": [],
        "ecosystem_apps": [
            "cerebro-app-eta.vercel.app",
            "centinela-alpha.vercel.app",
            "forja-frontend.onrender.com",
        ],
    },
    "exposure_history": [],
    "active_threats": [],
    "last_scan": None,
    "risk_score": 0,
}

CEO_PROFILE_TABLE_SCHEMA = """
CREATE TABLE IF NOT EXISTS sombra_ceo_profile (
  ceo_id TEXT PRIMARY KEY,
  encrypted_payload TEXT,
  payload_sha256 TEXT,
  updated_at TEXT
);
"""


class CEOProtectionProfile:
    def __init__(self, database: DatabaseConnection | None = None, blackbox: BlackBoxAuditCore | None = None) -> None:
        self.database = database if database is not None else DatabaseConnection()
        self.blackbox = blackbox if blackbox is not None else BlackBoxAuditCore(self.database)
        self.alert_codes = CEOAlertCodeSystem(self.database, self.blackbox)
        self._schema_ready = False
        self._owns_connection = database is None

    async def disconnect(self) -> None:
        if self._owns_connection:
            await self.database.disconnect()

    async def initialize_ceo_profile(
        self,
        personal_emails: list[str],
        domains: list[str],
        social_profiles: list[str],
    ) -> dict[str, Any]:
        await self._ensure_ready()
        profile = await self._load_profile() or deepcopy(CEO_PROFILE_SCHEMA)
        profile["ceo_id"] = "1"
        profile["protection_level"] = "MAXIMUM"
        assets = profile.setdefault("digital_assets", {})
        assets["personal_emails"] = self._unique_strings(personal_emails)
        assets["domains_owned"] = self._unique_strings(domains)
        assets["social_profiles"] = self._unique_strings(social_profiles)
        assets.setdefault("professional_emails", [])
        assets.setdefault("ecosystem_apps", deepcopy(CEO_PROFILE_SCHEMA["digital_assets"]["ecosystem_apps"]))
        profile["risk_score"] = self._calculate_risk_score(profile)
        await self._save_profile(profile)
        await self.blackbox.log(
            "CEO_PROFILE_INITIALIZED",
            "CEO-1",
            {
                "protection_level": profile["protection_level"],
                "personal_email_count": len(assets["personal_emails"]),
                "domain_count": len(assets["domains_owned"]),
                "social_profile_count": len(assets["social_profiles"]),
            },
            order_origin="CEO_PROTECTION_PROFILE",
        )
        return await self.scan_ceo_exposure()

    async def scan_ceo_exposure(self) -> dict[str, Any]:
        await self._ensure_ready()
        profile = await self._load_profile() or deepcopy(CEO_PROFILE_SCHEMA)
        assets = self._asset_terms(profile)
        matches = await self._scan_local_evidence(assets)
        profile["last_scan"] = self._now()
        profile["active_threats"] = matches
        profile["risk_score"] = self._calculate_risk_score(profile)
        await self._save_profile(profile)
        report = {
            "ceo_id": "1",
            "timestamp_utc": profile["last_scan"],
            "external_sources_contacted": False,
            "local_evidence_sources": ["sombra_intel_global", "sombra_alerts"],
            "assets_checked": {
                "personal_emails": len(profile["digital_assets"].get("personal_emails", [])),
                "domains_owned": len(profile["digital_assets"].get("domains_owned", [])),
                "social_profiles": len(profile["digital_assets"].get("social_profiles", [])),
                "ecosystem_apps": len(profile["digital_assets"].get("ecosystem_apps", [])),
            },
            "exposures_found": len(matches),
            "risk_score": profile["risk_score"],
            "status": "EXPOSURE_FOUND" if matches else "CLEAN_LOCAL_SCAN",
        }
        await self.blackbox.log(
            "CEO_EXPOSURE_SCAN_COMPLETED",
            "CEO-1",
            report,
            order_origin="CEO_PROTECTION_PROFILE",
        )
        if matches:
            highest = max(matches, key=lambda item: self._severity_rank(item.get("severity", "")))
            code = "A1-PARA-1" if highest.get("severity") == "CRITICAL" else "A2-PARA-1"
            await self.alert_codes.send_ceo_alert(
                code,
                f"CEO asset exposure detected in local intelligence memory: {highest.get('asset', 'unknown asset')}",
                intel_reference=str(highest.get("source_id") or ""),
            )
        return report

    async def get_ceo_risk_score(self) -> int:
        await self._ensure_ready()
        profile = await self._load_profile() or deepcopy(CEO_PROFILE_SCHEMA)
        score = self._calculate_risk_score(profile)
        if score != profile.get("risk_score"):
            profile["risk_score"] = score
            await self._save_profile(profile)
        return score

    async def add_exposure(self, exposure_data: dict[str, Any]) -> dict[str, Any]:
        await self._ensure_ready()
        profile = await self._load_profile() or deepcopy(CEO_PROFILE_SCHEMA)
        exposure = dict(exposure_data)
        exposure.setdefault("timestamp_utc", self._now())
        exposure.setdefault("severity", "HIGH")
        profile.setdefault("exposure_history", []).append(exposure)
        profile.setdefault("active_threats", []).append(exposure)
        profile["risk_score"] = self._calculate_risk_score(profile)
        await self._save_profile(profile)
        await self.blackbox.log(
            "CEO_EXPOSURE_ADDED",
            "CEO-1",
            {
                "severity": exposure.get("severity"),
                "asset": exposure.get("asset"),
                "risk_score": profile["risk_score"],
            },
            order_origin="CEO_PROTECTION_PROFILE",
        )
        code = "A1-PARA-1" if str(exposure.get("severity", "")).upper() == "CRITICAL" else "A2-PARA-1"
        await self.alert_codes.send_ceo_alert(
            code,
            f"CEO exposure registered: {exposure.get('summary', exposure.get('asset', 'protected asset'))}",
            intel_reference=str(exposure.get("source_id") or ""),
        )
        return {"risk_score": profile["risk_score"], "exposure": exposure}

    async def get_profile_snapshot(self) -> dict[str, Any]:
        await self._ensure_ready()
        profile = await self._load_profile() or deepcopy(CEO_PROFILE_SCHEMA)
        assets = profile.get("digital_assets", {})
        return {
            "ceo_id": "1",
            "protection_level": profile.get("protection_level", "MAXIMUM"),
            "asset_counts": {
                "personal_emails": len(assets.get("personal_emails", [])),
                "professional_emails": len(assets.get("professional_emails", [])),
                "domains_owned": len(assets.get("domains_owned", [])),
                "social_profiles": len(assets.get("social_profiles", [])),
                "ecosystem_apps": len(assets.get("ecosystem_apps", [])),
            },
            "active_threat_count": len(profile.get("active_threats", [])),
            "last_scan": profile.get("last_scan"),
            "risk_score": profile.get("risk_score", 0),
            "encrypted_at_rest": True,
        }

    async def _scan_local_evidence(self, assets: list[str]) -> list[dict[str, Any]]:
        if not assets:
            return []
        matches: list[dict[str, Any]] = []
        matches.extend(await self._scan_table("sombra_intel_global", "id", ["findings", "indicators", "prediction"], assets))
        matches.extend(
            await self._scan_table(
                "sombra_alerts",
                "alert_id",
                ["findings", "evidence_summary", "target_assets", "target_client"],
                assets,
            )
        )
        return matches

    async def _scan_table(
        self,
        table_name: str,
        id_column: str,
        text_columns: list[str],
        assets: list[str],
    ) -> list[dict[str, Any]]:
        try:
            rows = await self.database.fetch(f"SELECT * FROM {table_name} ORDER BY timestamp_utc DESC LIMIT 500")
        except Exception:
            return []
        results: list[dict[str, Any]] = []
        for row in rows:
            text = " ".join(str(row.get(column, "")) for column in text_columns).lower()
            for asset in assets:
                if asset and asset.lower() in text:
                    results.append(
                        {
                            "asset": asset,
                            "source_table": table_name,
                            "source_id": row.get(id_column),
                            "severity": str(row.get("severity", "HIGH")).upper(),
                            "timestamp_utc": row.get("timestamp_utc"),
                        }
                    )
        return results

    async def _load_profile(self) -> dict[str, Any] | None:
        row = await self.database.fetchrow(
            """
            SELECT encrypted_payload
            FROM sombra_ceo_profile
            WHERE ceo_id = $1
            """,
            "1",
        )
        if not row:
            return None
        return self._decrypt_payload(str(row["encrypted_payload"]))

    async def _save_profile(self, profile: dict[str, Any]) -> None:
        profile_json = json.dumps(profile, sort_keys=True, separators=(",", ":"))
        encrypted_payload = self._encrypt_payload(profile)
        payload_hash = hashlib.sha256(profile_json.encode("utf-8")).hexdigest()
        existing = await self.database.fetchrow("SELECT ceo_id FROM sombra_ceo_profile WHERE ceo_id = $1", "1")
        if existing:
            await self.database.execute(
                """
                UPDATE sombra_ceo_profile
                SET encrypted_payload = $1, payload_sha256 = $2, updated_at = $3
                WHERE ceo_id = $4
                """,
                encrypted_payload,
                payload_hash,
                self._now(),
                "1",
            )
            return
        await self.database.execute(
            """
            INSERT INTO sombra_ceo_profile (ceo_id, encrypted_payload, payload_sha256, updated_at)
            VALUES ($1, $2, $3, $4)
            """,
            "1",
            encrypted_payload,
            payload_hash,
            self._now(),
        )

    async def _ensure_ready(self) -> None:
        if self.database.connection is None:
            await self.database.connect()
        if self._schema_ready:
            return
        if self.database.backend == "sqlite":
            async with self.database._sqlite_lock:
                await self.database.connection.executescript(CEO_PROFILE_TABLE_SCHEMA)
                await self.database.connection.commit()
        else:
            statements = [statement.strip() for statement in CEO_PROFILE_TABLE_SCHEMA.split(";") if statement.strip()]
            for statement in statements:
                await self.database.execute(statement)
        self._schema_ready = True

    def _encrypt_payload(self, payload: dict[str, Any]) -> str:
        return Fernet(self._fernet_key()).encrypt(json.dumps(payload, sort_keys=True).encode("utf-8")).decode("utf-8")

    def _decrypt_payload(self, encrypted_payload: str) -> dict[str, Any]:
        raw = Fernet(self._fernet_key()).decrypt(encrypted_payload.encode("utf-8"))
        return json.loads(raw.decode("utf-8"))

    @staticmethod
    def _fernet_key() -> bytes:
        key_material = os.getenv("SOMBRA_CEO_PROFILE_KEY") or os.getenv("SOMBRA_API_KEY") or "local-ceo-profile-key"
        if len(key_material) == 44:
            try:
                base64.urlsafe_b64decode(key_material.encode("utf-8"))
                return key_material.encode("utf-8")
            except Exception:
                pass
        return base64.urlsafe_b64encode(hashlib.sha256(key_material.encode("utf-8")).digest())

    @staticmethod
    def _asset_terms(profile: dict[str, Any]) -> list[str]:
        assets = profile.get("digital_assets", {})
        terms: list[str] = []
        for key in ("personal_emails", "professional_emails", "domains_owned", "social_profiles", "ecosystem_apps"):
            terms.extend(str(item).strip() for item in assets.get(key, []) if str(item).strip())
        return sorted(set(terms))

    @staticmethod
    def _calculate_risk_score(profile: dict[str, Any]) -> int:
        active_threats = profile.get("active_threats", [])
        history = profile.get("exposure_history", [])
        score = len(active_threats) * 20 + len(history) * 5
        for exposure in active_threats:
            severity = str(exposure.get("severity", "")).upper()
            if severity == "CRITICAL":
                score += 50
            elif severity == "HIGH":
                score += 30
            elif severity == "MEDIUM":
                score += 15
        return max(0, min(100, int(score)))

    @staticmethod
    def _unique_strings(items: list[str]) -> list[str]:
        return sorted(set(str(item).strip() for item in items if str(item).strip()))

    @staticmethod
    def _severity_rank(severity: str) -> int:
        return {"CRITICAL": 4, "HIGH": 3, "MEDIUM": 2, "LOW": 1}.get(str(severity).upper(), 0)

    @staticmethod
    def _now() -> str:
        return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
