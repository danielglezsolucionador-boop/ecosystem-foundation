from __future__ import annotations

import asyncio
from collections import Counter
from datetime import UTC, datetime
from html import escape
import json
import os
from pathlib import Path
import re
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from apps.sombra.collector.agents import SombraLeakRadarAgent
from apps.sombra.memory import BlackBoxAuditCore, DatabaseConnection, GlobalMemoryLayer, MemoryQueryEngine
from apps.sombra.memory.database import SOMBRA_ROOT


REPORT_DIR = SOMBRA_ROOT / "reports"
REPORT_SCAN_DIR = REPORT_DIR / "scans"
HIBP_BREACHES_URL = "https://haveibeenpwned.com/api/v3/breaches"
REPORT_FOOTER_TEMPLATE = (
    "Este reporte es confidencial y fue generado exclusivamente para {company}. "
    "Centinela — Protegemos lo que importa. Fecha: {date}"
)
CLIENT_ENGINE_NAME = "Motor de Inteligencia Centinela"
CLIENT_MONITORING_NAME = "Monitoreo Avanzado de Amenazas"
PDF_FONT_NAME = "CentinelaSans"
PDF_BOLD_FONT_NAME = "CentinelaSansBold"

RISK_DESCRIPTIONS = {
    "BAJO": "Tu empresa tiene exposición mínima detectada. Mantén las medidas actuales y monitorea continuamente.",
    "MEDIO": "Se detectaron exposiciones moderadas. Acción recomendada en los próximos 30 días para reducir el riesgo.",
    "ALTO": "Exposición significativa detectada. Se requiere acción urgente en los próximos 7 días.",
    "CRÍTICO": "Exposición crítica activa detectada. Acción inmediata requerida. Contacta a Centinela ahora.",
}

RISK_BADGES = {
    "BAJO": "(✓ Sin acción urgente)",
    "MEDIO": "(⚠ Revisar en 30 días)",
    "ALTO": "(⚠ Acción en 7 días)",
    "CRÍTICO": "(🚨 Acción inmediata)",
}

THREAT_TYPE_LABELS = {
    "VULNERABILITY_PUBLISHED": "Vulnerabilidad publicada",
    "RANSOMWARE_CAMPAIGN": "Campaña de ransomware",
    "CREDENTIAL_EXPOSURE": "Exposición de credenciales",
    "ACTIVE_ATTACK_CAMPAIGN": "Campaña de ataque activa",
    "ZERO_DAY_EXPLOIT": "Explotación de día cero",
    "INTELLIGENCE_TREND": "Tendencia de inteligencia",
    "GENERAL_CREDENTIAL_EXPOSURE": "Exposición general de credenciales",
}

SECTOR_LABELS = {
    "financial_services": "servicios financieros",
    "healthcare": "salud",
    "technology": "tecnología",
    "retail": "comercio",
    "education": "educación",
    "legal": "legal",
    "general_business": "empresa general",
}

DATA_CLASS_LABELS = {
    "Passwords": "Contraseñas",
    "Email addresses": "Correos electrónicos",
    "Usernames": "Nombres de usuario",
    "IP addresses": "Direcciones IP",
    "Phone numbers": "Teléfonos",
    "Physical addresses": "Direcciones físicas",
    "Credit cards": "Tarjetas de crédito",
    "Bank account numbers": "Cuentas bancarias",
    "Social security numbers": "Documentos de identidad",
    "Dates of birth": "Fechas de nacimiento",
    "Security questions and answers": "Preguntas y respuestas de seguridad",
    "Private messages": "Mensajes privados",
}

DATA_CLASS_WEIGHTS = {
    "passwords": 24,
    "email addresses": 8,
    "usernames": 6,
    "ip addresses": 5,
    "phone numbers": 6,
    "physical addresses": 8,
    "credit cards": 20,
    "bank account numbers": 22,
    "social security numbers": 24,
    "dates of birth": 10,
    "security questions and answers": 20,
    "private messages": 12,
}

SECTOR_KEYWORDS = {
    "financial_services": ("bank", "fintech", "pay", "capital", "finance", "credit", "insurance"),
    "healthcare": ("health", "clinic", "medical", "pharma", "care", "hospital"),
    "technology": ("tech", "software", "cloud", "ai", "data", "cyber", "systems"),
    "retail": ("shop", "store", "retail", "market", "commerce"),
    "education": ("school", "university", "academy", "education"),
    "legal": ("law", "legal", "attorney"),
}


class DarkWebScanProduct:
    def __init__(
        self,
        database: DatabaseConnection | None = None,
        blackbox: BlackBoxAuditCore | None = None,
    ) -> None:
        self.database = database if database is not None else DatabaseConnection()
        self.blackbox = blackbox if blackbox is not None else BlackBoxAuditCore(self.database)
        self.global_memory = GlobalMemoryLayer(self.database)
        self.query_engine = MemoryQueryEngine(self.database)
        self.leakradar = SombraLeakRadarAgent()
        self._owns_database = database is None

    async def generate_scan(self, company_name: str, domain: str, email_patterns: list[Any]) -> dict[str, Any]:
        clean_company = self._clean_required(company_name, "company_name")
        clean_domain = self._clean_domain(domain)
        clean_patterns = self._clean_email_patterns(email_patterns)
        await self._ensure_database()

        leakradar_result = await self._check_leakradar(clean_domain)
        hibp_result = await self._check_hibp(clean_domain)
        credential_matches = await self._search_credential_exposure(clean_company, clean_domain, clean_patterns)
        threat_landscape = await self._check_threat_landscape(clean_company, clean_domain)

        score_inputs = {
            "leakradar_hits": int(leakradar_result.get("hits") or 0),
            "breaches": hibp_result["breaches"],
            "credential_matches": credential_matches,
            "sector_threat_level": threat_landscape["sector_threat_level"],
        }
        risk_score = self._calculate_risk_score(**score_inputs)
        risk_level = self._risk_level(risk_score)
        exposures_found = self._build_exposures(leakradar_result, hibp_result, credential_matches, clean_domain)
        sector_threats = self._build_sector_threats(threat_landscape)
        executive_summary = self._write_executive_summary(clean_company, clean_domain, risk_score, risk_level, exposures_found, sector_threats)
        recommendations = self._build_recommendations(risk_level, exposures_found, sector_threats)
        scan_date = self._today()

        report = {
            "company": clean_company,
            "domain": clean_domain,
            "scan_date": scan_date,
            "risk_score": risk_score,
            "risk_level": risk_level,
            "risk_level_description": RISK_DESCRIPTIONS[risk_level],
            "executive_summary": executive_summary,
            "exposures_found": exposures_found,
            "sector_threats": sector_threats,
            "recommendations": recommendations,
            "footer": self._footer(clean_company, scan_date),
            "metadata": {
                "product": "Análisis de Exposición Digital",
                "leakradar_status": leakradar_result.get("status", "unknown"),
                "leakradar_hits": int(leakradar_result.get("hits") or 0),
                "leakradar_source_reliability": leakradar_result.get("source_reliability", 0.85),
                "hibp_mode": hibp_result["mode"],
                "hibp_note": hibp_result["note"],
                "email_patterns_checked": clean_patterns,
                "credential_matches_count": len(credential_matches),
                "breaches_found_count": len(hibp_result["breaches"]),
                "sector": self._spanish_sector(threat_landscape["sector"]),
                "sector_threat_level": threat_landscape["sector_threat_level"],
            },
        }

        json_path = self._report_path(clean_domain, "json")
        pdf_path = self._scan_pdf_path(clean_domain)
        report = self._sanitize_client_output(report)
        await asyncio.to_thread(self._save_json_report, report, json_path)
        await asyncio.to_thread(self._save_pdf_report, report, pdf_path)

        await self.blackbox.log(
            "DARK_WEB_SCAN_COMPLETED",
            clean_domain,
            {
                "company_name": clean_company,
                "domain": clean_domain,
                "risk_score": risk_score,
                "risk_level": risk_level,
                "leakradar_hits": int(leakradar_result.get("hits") or 0),
                "breaches_found": len(hibp_result["breaches"]),
                "credential_matches": len(credential_matches),
                "json_report_path": str(json_path),
                "pdf_report_path": str(pdf_path),
            },
            order_origin="SOMBRA_PRODUCT",
        )
        return report

    async def close(self) -> None:
        if self._owns_database:
            await self.database.disconnect()

    async def _ensure_database(self) -> None:
        if self.database.connection is None:
            await self.database.connect()

    async def _check_leakradar(self, domain: str) -> dict[str, Any]:
        result = await self.leakradar.search_domain(domain)
        result.setdefault("source", "LeakRadar")
        result.setdefault("source_reliability", 0.85)
        result.setdefault("source_category", "CREDENTIAL")
        result.setdefault("hits", 0)
        result.setdefault("results", [])
        return result

    async def _check_hibp(self, domain: str) -> dict[str, Any]:
        api_key = os.getenv("HIBP_API_KEY")
        mode = "autenticado" if api_key else "demostración pública"
        note = "Clave HIBP configurada; el catálogo de brechas fue filtrado para el dominio analizado."
        if not api_key:
            note = "Clave HIBP no configurada; se usó el catálogo público solo como señal indicativa."
        try:
            breaches = await asyncio.to_thread(self._fetch_hibp_breaches, api_key)
        except Exception:
            return {
                "mode": mode,
                "note": f"{note} La consulta HIBP no estuvo disponible durante este análisis.",
                "breaches": [],
            }
        filtered = [self._normalize_breach(breach) for breach in breaches if self._breach_matches_domain(breach, domain)]
        return {"mode": mode, "note": note, "breaches": filtered}

    @staticmethod
    def _fetch_hibp_breaches(api_key: str | None) -> list[dict[str, Any]]:
        headers = {
            "Accept": "application/json",
            "User-Agent": os.getenv("HIBP_USER_AGENT", "Centinela-DarkWebScan/1.0"),
        }
        if api_key:
            headers["hibp-api-key"] = api_key
        request = Request(HIBP_BREACHES_URL, headers=headers, method="GET")
        try:
            with urlopen(request, timeout=20) as response:
                payload = response.read().decode("utf-8")
        except HTTPError as error:
            raise RuntimeError(f"HIBP HTTP {error.code}") from error
        except URLError as error:
            raise RuntimeError(f"HIBP network error: {error.reason}") from error
        parsed = json.loads(payload)
        if not isinstance(parsed, list):
            return []
        return [item for item in parsed if isinstance(item, dict)]

    async def _search_credential_exposure(
        self,
        company_name: str,
        domain: str,
        email_patterns: list[str],
    ) -> list[dict[str, Any]]:
        terms = [domain, company_name, *email_patterns]
        seen: set[str] = set()
        matches: list[dict[str, Any]] = []
        for term in terms:
            if not term:
                continue
            for row in await self._search_intel_text(term):
                record_id = str(row.get("id", ""))
                if record_id in seen:
                    continue
                seen.add(record_id)
                matches.append(self._intel_summary(row, term))
        return sorted(matches, key=lambda row: int(row.get("threat_score") or 0), reverse=True)[:25]

    async def _search_intel_text(self, term: str) -> list[dict[str, Any]]:
        pattern = f"%{term.strip()}%"
        rows = await self.database.fetch(
            """
            SELECT * FROM sombra_intel_global
            WHERE LOWER(findings) LIKE LOWER($1)
               OR LOWER(threat_type) LIKE LOWER($1)
               OR LOWER(severity) LIKE LOWER($1)
               OR LOWER(CAST(indicators AS TEXT)) LIKE LOWER($1)
               OR LOWER(CAST(prediction AS TEXT)) LIKE LOWER($1)
            ORDER BY threat_score DESC, timestamp_utc DESC
            LIMIT 50
            """,
            pattern,
        )
        return [self.query_engine._decode_intel(row) for row in rows]

    async def _check_threat_landscape(self, company_name: str, domain: str) -> dict[str, Any]:
        sector = self._infer_sector(company_name, domain)
        recent = await self.global_memory.get_recent_threats(hours=24 * 30)
        sector_matches = await self.query_engine.search_by_keyword(sector.replace("_", " "))
        ranked = sorted(recent + sector_matches, key=lambda row: int(row.get("threat_score") or 0), reverse=True)
        unique: list[dict[str, Any]] = []
        seen: set[str] = set()
        for row in ranked:
            record_id = str(row.get("id", ""))
            if record_id in seen:
                continue
            seen.add(record_id)
            unique.append(row)
        type_counter = Counter(str(row.get("threat_type", "UNKNOWN")) for row in unique[:100])
        severity_counter = Counter(str(row.get("severity", "UNKNOWN")) for row in unique[:100])
        max_score = max((int(row.get("threat_score") or 0) for row in unique), default=0)
        critical_or_high = sum(1 for row in unique if str(row.get("severity", "")).upper() in {"CRITICAL", "HIGH"})
        sector_threat_level = min(100, max_score + min(25, critical_or_high * 3))
        return {
            "sector": sector,
            "top_threat_types": type_counter.most_common(5),
            "severity_mix": dict(severity_counter),
            "recent_similar_records": [self._intel_summary(row, "sector_landscape") for row in unique[:5]],
            "active_campaigns_nearby": [
                self._intel_summary(row, "active_campaign")
                for row in unique
                if str(row.get("severity", "")).upper() in {"CRITICAL", "HIGH"}
            ][:5],
            "sector_threat_level": sector_threat_level,
        }

    @staticmethod
    def _calculate_risk_score(
        leakradar_hits: int,
        breaches: list[dict[str, Any]],
        credential_matches: list[dict[str, Any]],
        sector_threat_level: int,
    ) -> int:
        leakradar_points = min(30, max(0, leakradar_hits) * 10)
        breach_points = min(35, len(breaches) * 12)
        credential_points = min(30, len(credential_matches) * 7)
        data_class_points = min(20, max((DarkWebScanProduct._data_class_weight(breach.get("data_classes", [])) for breach in breaches), default=0))
        recency_points = DarkWebScanProduct._breach_recency_points(breaches)
        sector_points = min(20, round(sector_threat_level * 0.2))
        return min(100, int(leakradar_points + breach_points + credential_points + data_class_points + recency_points + sector_points))

    @staticmethod
    def _data_class_weight(data_classes: Any) -> int:
        if not isinstance(data_classes, list):
            return 0
        return max((DATA_CLASS_WEIGHTS.get(str(item).lower(), 3) for item in data_classes), default=0)

    @staticmethod
    def _breach_recency_points(breaches: list[dict[str, Any]]) -> int:
        dates = [DarkWebScanProduct._parse_date(breach.get("breach_date")) for breach in breaches]
        dates = [date for date in dates if date is not None]
        if not dates:
            return 0
        days_old = (datetime.now(UTC).date() - max(dates).date()).days
        if days_old <= 365:
            return 15
        if days_old <= 365 * 3:
            return 10
        if days_old <= 365 * 5:
            return 5
        return 2

    @staticmethod
    def _risk_level(score: int) -> str:
        if score >= 76:
            return "CRÍTICO"
        if score >= 51:
            return "ALTO"
        if score >= 26:
            return "MEDIO"
        return "BAJO"

    @staticmethod
    def _build_exposures(
        leakradar_result: dict[str, Any],
        hibp_result: dict[str, Any],
        credential_matches: list[dict[str, Any]],
        domain: str,
    ) -> list[dict[str, Any]]:
        exposures: list[dict[str, Any]] = []
        leakradar_hits = int(leakradar_result.get("hits") or 0)
        if leakradar_hits > 0:
            exposures.append(
                {
                    "source": "LeakRadar",
                    "type": "exposición de credenciales",
                    "domain": domain,
                    "title": (
                        f"LeakRadar detectó {leakradar_hits} señales externas asociadas al dominio {domain}. "
                        "Esto puede indicar credenciales o datos corporativos circulando fuera del control de la empresa."
                    ),
                    "note": "Prioridad alta: validar cuentas afectadas, rotar contraseñas sensibles y activar monitoreo continuo.",
                    "source_reliability": leakradar_result.get("source_reliability", 0.85),
                }
            )
        for breach in hibp_result["breaches"]:
            exposures.append(
                {
                    "source": "HIBP",
                    "type": "brecha",
                    "title": breach["title"],
                    "domain": breach["domain"],
                    "breach_date": breach["breach_date"],
                    "pwn_count": breach["pwn_count"],
                    "data_classes": [DarkWebScanProduct._spanish_data_class(item) for item in breach["data_classes"]],
                    "verified": "sí" if breach["is_verified"] else "no",
                    "note": hibp_result["note"],
                }
            )
        for match in credential_matches:
            exposures.append(
                {
                    "source": CLIENT_ENGINE_NAME,
                    "type": "referencia de credenciales o datos",
                    **match,
                }
            )
        if exposures:
            return exposures
        return [
            {
                "source": CLIENT_MONITORING_NAME,
                "type": "sin exposición directa confirmada",
                "domain": domain,
                "title": "No se confirmó exposición directa de credenciales durante este análisis.",
                "note": hibp_result["note"],
            }
        ]

    @staticmethod
    def _build_sector_threats(threat_landscape: dict[str, Any]) -> list[dict[str, Any]]:
        threats: list[dict[str, Any]] = []
        for threat_type, count in threat_landscape["top_threat_types"]:
            threat_name = DarkWebScanProduct._spanish_threat_type(threat_type)
            threat_level = DarkWebScanProduct._risk_level(int(threat_landscape["sector_threat_level"]))
            threats.append(
                {
                    "threat_type": threat_name,
                    "threat_name": threat_name,
                    "observed_records": count,
                    "sector": DarkWebScanProduct._spanish_sector(threat_landscape["sector"]),
                    "threat_level": threat_level,
                    "executive_explanation": DarkWebScanProduct._threat_explanation(
                        str(threat_type),
                        int(count),
                        threat_level,
                    ),
                }
            )
        if threats:
            return threats
        return [
            {
                "threat_type": DarkWebScanProduct._spanish_threat_type("GENERAL_CREDENTIAL_EXPOSURE"),
                "threat_name": DarkWebScanProduct._spanish_threat_type("GENERAL_CREDENTIAL_EXPOSURE"),
                "observed_records": 0,
                "sector": DarkWebScanProduct._spanish_sector(threat_landscape["sector"]),
                "threat_level": DarkWebScanProduct._risk_level(int(threat_landscape["sector_threat_level"])),
                "executive_explanation": "No se observaron amenazas directas relevantes, pero conviene mantener monitoreo continuo sobre credenciales y accesos críticos.",
            }
        ]

    @staticmethod
    def _write_executive_summary(
        company_name: str,
        domain: str,
        risk_score: int,
        risk_level: str,
        exposures_found: list[dict[str, Any]],
        sector_threats: list[dict[str, Any]],
    ) -> str:
        confirmed = [item for item in exposures_found if item.get("type") != "sin exposición directa confirmada"]
        primary_threat = str((sector_threats[0] if sector_threats else {}).get("threat_name", "exposición de credenciales")).lower()
        exposure_sentence = (
            f"Se detectaron {len(confirmed)} señales directas de exposición asociadas a {company_name}."
            if confirmed
            else f"No se confirmó exposición directa de credenciales para {company_name} durante este análisis."
        )
        return (
            f"{company_name} presenta un nivel de riesgo {risk_level} con una puntuación de {risk_score}/100. "
            f"{exposure_sentence} "
            f"La amenaza principal observada en su entorno es {primary_threat}; revisa accesos y contraseñas esta semana."
        )

    @staticmethod
    def _build_recommendations(
        risk_level: str,
        exposures_found: list[dict[str, Any]],
        sector_threats: list[dict[str, Any]],
    ) -> list[str]:
        has_confirmed_exposure = any(item.get("type") != "sin exposición directa confirmada" for item in exposures_found)
        recommendations = [
            "Cambia de inmediato las contraseñas de las cuentas relacionadas con el dominio analizado." if has_confirmed_exposure else "Revisa cuentas ejecutivas, financieras y administrativas para descartar credenciales expuestas.",
            "Activa autenticación multifactor en todos los accesos externos y cuentas privilegiadas.",
            "Configura alertas para el dominio, nombres ejecutivos y patrones de correo de alto riesgo.",
            "Revisa campañas recientes del sector y corrige los sistemas vinculados a las amenazas principales.",
            "Agenda un nuevo análisis en 30 días y comparte el avance de mitigación con la dirección.",
        ]
        if risk_level in {"CRÍTICO", "ALTO"}:
            recommendations[0] = "Rota credenciales expuestas y cierra sesiones activas de usuarios afectados hoy mismo."
        if sector_threats and sector_threats[0].get("threat_name") == "Campaña de ransomware":
            recommendations[3] = "Valida respaldos aislados, accesos privilegiados y procedimientos de recuperación ante ransomware."
        return recommendations

    @staticmethod
    def _threat_explanation(threat_type: str, count: int, risk_level: str) -> str:
        if threat_type == "VULNERABILITY_PUBLISHED":
            return (
                f"Se detectaron {count} vulnerabilidades publicadas que afectan sistemas similares al tuyo. "
                f"Nivel de riesgo: {risk_level}. Acción recomendada: revisar y aplicar parches de seguridad esta semana."
            )
        if threat_type == "RANSOMWARE_CAMPAIGN":
            return (
                f"Se observaron {count} señales de campañas de ransomware contra organizaciones comparables. "
                f"Nivel de riesgo: {risk_level}. Acción recomendada: validar respaldos, accesos críticos y plan de respuesta esta semana."
            )
        if threat_type == "CREDENTIAL_EXPOSURE":
            return (
                f"Se encontraron {count} señales relacionadas con posible exposición de credenciales en el mercado criminal. "
                f"Nivel de riesgo: {risk_level}. Acción recomendada: revisar cuentas sensibles y activar autenticación multifactor."
            )
        if threat_type == "ACTIVE_ATTACK_CAMPAIGN":
            return (
                f"Se identificaron {count} señales de ataques activos contra empresas con perfiles similares. "
                f"Nivel de riesgo: {risk_level}. Acción recomendada: reforzar monitoreo y validar accesos externos de inmediato."
            )
        if threat_type == "ZERO_DAY_EXPLOIT":
            return (
                f"Se detectaron {count} señales de explotación reciente sin corrección ampliamente disponible. "
                f"Nivel de riesgo: {risk_level}. Acción recomendada: revisar exposición pública y aplicar mitigaciones temporales."
            )
        return (
            f"Se observaron {count} señales de riesgo digital relevantes para empresas similares. "
            f"Nivel de riesgo: {risk_level}. Acción recomendada: revisar controles de acceso y monitoreo esta semana."
        )

    @staticmethod
    def _normalize_breach(breach: dict[str, Any]) -> dict[str, Any]:
        return {
            "name": str(breach.get("Name", "")),
            "title": str(breach.get("Title", breach.get("Name", ""))),
            "domain": str(breach.get("Domain", "")),
            "breach_date": str(breach.get("BreachDate", "")),
            "added_date": str(breach.get("AddedDate", "")),
            "pwn_count": int(breach.get("PwnCount") or 0),
            "data_classes": list(breach.get("DataClasses") or []),
            "is_verified": bool(breach.get("IsVerified")),
            "is_sensitive": bool(breach.get("IsSensitive")),
            "is_spam_list": bool(breach.get("IsSpamList")),
        }

    @staticmethod
    def _breach_matches_domain(breach: dict[str, Any], domain: str) -> bool:
        requested = domain.lower()
        breach_domain = str(breach.get("Domain", "")).lower()
        name = str(breach.get("Name", "")).lower()
        title = str(breach.get("Title", "")).lower()
        return breach_domain == requested or breach_domain.endswith(f".{requested}") or requested in {name, title}

    @staticmethod
    def _intel_summary(row: dict[str, Any], matched_on: str) -> dict[str, Any]:
        threat_type = str(row.get("threat_type", "UNKNOWN"))
        severity = str(row.get("severity", "UNKNOWN"))
        return {
            "id": row.get("id"),
            "matched_on": DarkWebScanProduct._spanish_match_label(matched_on),
            "timestamp_utc": row.get("timestamp_utc"),
            "threat_type": DarkWebScanProduct._spanish_threat_type(threat_type),
            "severity": DarkWebScanProduct._spanish_severity(severity),
            "threat_score": int(row.get("threat_score") or 0),
            "source_category": "inteligencia interna",
            "findings_excerpt": f"Registro relacionado con {DarkWebScanProduct._spanish_threat_type(threat_type).lower()} y severidad {DarkWebScanProduct._spanish_severity(severity).lower()}.",
            "indicators": ["Indicadores revisados internamente"],
        }

    @staticmethod
    def _infer_sector(company_name: str, domain: str) -> str:
        value = f"{company_name} {domain}".lower()
        for sector, keywords in SECTOR_KEYWORDS.items():
            if any(keyword in value for keyword in keywords):
                return sector
        return "general_business"

    @staticmethod
    def _clean_required(value: str, field_name: str) -> str:
        clean = str(value or "").strip()
        if not clean:
            raise ValueError(f"{field_name} is required")
        return clean

    @staticmethod
    def _clean_domain(domain: str) -> str:
        clean = str(domain or "").strip().lower()
        clean = re.sub(r"^https?://", "", clean).split("/")[0].strip(".")
        if not clean or "." not in clean:
            raise ValueError("domain must be a valid DNS domain")
        return clean

    @staticmethod
    def _clean_email_patterns(email_patterns: list[Any]) -> list[str]:
        if not isinstance(email_patterns, list):
            raise ValueError("email_patterns must be a list")
        clean = [str(item).strip().lower() for item in email_patterns if str(item).strip()]
        return list(dict.fromkeys(clean))

    @staticmethod
    def _report_path(domain: str, extension: str) -> Path:
        safe_domain = re.sub(r"[^a-zA-Z0-9.-]+", "_", domain).strip("._")
        return REPORT_DIR / f"scan_{safe_domain}_{DarkWebScanProduct._today()}.{extension}"

    @staticmethod
    def _scan_pdf_path(domain: str) -> Path:
        safe_domain = re.sub(r"[^a-zA-Z0-9.-]+", "_", domain).strip("._")
        return REPORT_SCAN_DIR / f"scan_{safe_domain}_{DarkWebScanProduct._today()}.pdf"

    @staticmethod
    def _save_json_report(report: dict[str, Any], path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True, default=str), encoding="utf-8")

    @staticmethod
    def _save_pdf_report(report: dict[str, Any], path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        font_name, bold_font_name = DarkWebScanProduct._register_pdf_fonts()
        styles = DarkWebScanProduct._pdf_styles(font_name, bold_font_name)
        document = SimpleDocTemplate(
            str(path),
            pagesize=LETTER,
            rightMargin=0.65 * inch,
            leftMargin=0.65 * inch,
            topMargin=0.62 * inch,
            bottomMargin=0.62 * inch,
            title=f"Centinela - {report['company']}",
            author="Centinela",
        )
        story: list[Any] = []

        story.append(Paragraph("[CENTINELA]", styles["brand"]))
        story.append(Paragraph("Análisis de Exposición Digital", styles["title"]))
        story.append(Paragraph("Confidencial — Solo para uso interno", styles["subtitle"]))
        story.append(Spacer(1, 18))

        risk_text = f"{report['risk_level']} {DarkWebScanProduct._risk_badge(report['risk_level'])}"
        risk_table = Table(
            [
                [
                    Paragraph("Nivel de Riesgo", styles["risk_label"]),
                    Paragraph(risk_text, styles["risk_value"]),
                    Paragraph(f"{report['risk_score']}/100", styles["risk_score"]),
                ],
                [Paragraph(report["risk_level_description"], styles["risk_description"]), "", ""],
            ],
            colWidths=[1.65 * inch, 3.9 * inch, 1.45 * inch],
        )
        risk_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), DarkWebScanProduct._risk_color(report["risk_level"])),
                    ("TEXTCOLOR", (0, 0), (-1, -1), colors.white),
                    ("BOX", (0, 0), (-1, -1), 0.75, colors.HexColor("#17324D")),
                    ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.Color(1, 1, 1, alpha=0.3)),
                    ("SPAN", (0, 1), (-1, 1)),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 12),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 12),
                    ("TOPPADDING", (0, 0), (-1, -1), 10),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
                ]
            )
        )
        story.append(risk_table)
        story.append(Spacer(1, 16))

        story.append(Paragraph(f"<b>Empresa:</b> {escape(str(report['company']))}", styles["body"]))
        story.append(Paragraph(f"<b>Dominio:</b> {escape(str(report['domain']))}", styles["body"]))
        story.append(Paragraph(f"<b>Fecha de Análisis:</b> {escape(str(report['scan_date']))}", styles["body"]))
        story.append(Spacer(1, 16))

        DarkWebScanProduct._add_section(story, styles, "Resumen Ejecutivo", [str(report["executive_summary"])])
        DarkWebScanProduct._add_section(
            story,
            styles,
            "Exposiciones Detectadas",
            [DarkWebScanProduct._exposure_text(item) for item in report["exposures_found"]],
        )
        DarkWebScanProduct._add_section(
            story,
            styles,
            "Amenazas en tu Sector",
            [str(item.get("executive_explanation", item.get("threat_name", ""))) for item in report["sector_threats"]],
        )
        DarkWebScanProduct._add_section(story, styles, "Lo que debes hacer ahora", list(report["recommendations"]), numbered=True)
        story.append(Spacer(1, 18))
        story.append(Paragraph(str(report["footer"]), styles["footer"]))
        document.build(story)

    @staticmethod
    def _register_pdf_fonts() -> tuple[str, str]:
        regular_candidates = [
            "/usr/share/fonts/truetype/ancient-scripts/Symbola_hint.ttf",
            "/usr/share/fonts/truetype/noto/NotoSansSymbols2-Regular.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
            "C:/Windows/Fonts/seguisym.ttf",
            "C:/Windows/Fonts/segoeui.ttf",
            "C:/Windows/Fonts/arial.ttf",
        ]
        bold_candidates = [
            "/usr/share/fonts/truetype/ancient-scripts/Symbola_hint.ttf",
            "/usr/share/fonts/truetype/noto/NotoSansSymbols2-Regular.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf",
            "C:/Windows/Fonts/seguisym.ttf",
            "C:/Windows/Fonts/segoeuib.ttf",
            "C:/Windows/Fonts/arialbd.ttf",
        ]
        regular_path = next((Path(item) for item in regular_candidates if Path(item).exists()), None)
        bold_path = next((Path(item) for item in bold_candidates if Path(item).exists()), None)
        if regular_path is None:
            return "Helvetica", "Helvetica-Bold"
        registered = set(pdfmetrics.getRegisteredFontNames())
        if PDF_FONT_NAME not in registered:
            pdfmetrics.registerFont(TTFont(PDF_FONT_NAME, str(regular_path)))
        if bold_path is not None and PDF_BOLD_FONT_NAME not in registered:
            pdfmetrics.registerFont(TTFont(PDF_BOLD_FONT_NAME, str(bold_path)))
        return PDF_FONT_NAME, PDF_BOLD_FONT_NAME if bold_path is not None else PDF_FONT_NAME

    @staticmethod
    def _pdf_styles(font_name: str, bold_font_name: str) -> dict[str, ParagraphStyle]:
        return {
            "brand": ParagraphStyle("brand", fontName=bold_font_name, fontSize=14, leading=17, alignment=TA_CENTER, textColor=colors.HexColor("#17324D"), spaceAfter=4),
            "title": ParagraphStyle("title", fontName=bold_font_name, fontSize=20, leading=24, alignment=TA_CENTER, textColor=colors.HexColor("#111827"), spaceAfter=4),
            "subtitle": ParagraphStyle("subtitle", fontName=font_name, fontSize=10, leading=13, alignment=TA_CENTER, textColor=colors.HexColor("#4B5563")),
            "section": ParagraphStyle("section", fontName=bold_font_name, fontSize=13, leading=16, textColor=colors.HexColor("#17324D"), spaceBefore=12, spaceAfter=7),
            "body": ParagraphStyle("body", fontName=font_name, fontSize=10.5, leading=15, alignment=TA_LEFT, textColor=colors.HexColor("#1F2937"), spaceAfter=5),
            "bullet": ParagraphStyle("bullet", fontName=font_name, fontSize=10.3, leading=15, leftIndent=14, firstLineIndent=-8, textColor=colors.HexColor("#1F2937"), spaceAfter=6),
            "footer": ParagraphStyle("footer", fontName=font_name, fontSize=8.5, leading=11, alignment=TA_CENTER, textColor=colors.HexColor("#6B7280")),
            "risk_label": ParagraphStyle("risk_label", fontName=bold_font_name, fontSize=9.5, leading=12, textColor=colors.white),
            "risk_value": ParagraphStyle("risk_value", fontName=bold_font_name, fontSize=15, leading=18, textColor=colors.white),
            "risk_score": ParagraphStyle("risk_score", fontName=bold_font_name, fontSize=18, leading=21, alignment=TA_CENTER, textColor=colors.white),
            "risk_description": ParagraphStyle("risk_description", fontName=font_name, fontSize=10.2, leading=14, textColor=colors.white),
        }

    @staticmethod
    def _add_section(
        story: list[Any],
        styles: dict[str, ParagraphStyle],
        title: str,
        paragraphs: list[str],
        numbered: bool = False,
    ) -> None:
        story.append(Paragraph(escape(title), styles["section"]))
        for index, paragraph in enumerate(paragraphs, start=1):
            prefix = f"{index}. " if numbered else "• "
            story.append(Paragraph(f"{escape(prefix)}{escape(str(paragraph))}", styles["bullet"]))
        story.append(Spacer(1, 7))

    @staticmethod
    def _exposure_text(item: dict[str, Any]) -> str:
        title = str(item.get("title") or "No se detectaron exposiciones directas.")
        if item.get("type") == "brecha":
            data_classes = ", ".join(str(value) for value in item.get("data_classes", [])[:5])
            return f"{title}. Se trata de una brecha registrada para el dominio analizado. Datos expuestos: {data_classes or 'no especificados'}."
        return title

    @staticmethod
    def _risk_badge(risk_level: str) -> str:
        return RISK_BADGES.get(risk_level, "")

    @staticmethod
    def _risk_color(risk_level: str) -> colors.Color:
        return {
            "BAJO": colors.HexColor("#166534"),
            "MEDIO": colors.HexColor("#A16207"),
            "ALTO": colors.HexColor("#B45309"),
            "CRÍTICO": colors.HexColor("#991B1B"),
        }.get(risk_level, colors.HexColor("#17324D"))

    @staticmethod
    def _sanitize_client_output(value: Any) -> Any:
        if isinstance(value, dict):
            return {key: DarkWebScanProduct._sanitize_client_output(item) for key, item in value.items()}
        if isinstance(value, list):
            return [DarkWebScanProduct._sanitize_client_output(item) for item in value]
        if isinstance(value, str):
            return re.sub(r"sombra", CLIENT_ENGINE_NAME, value, flags=re.IGNORECASE)
        return value

    @staticmethod
    def _spanish_threat_type(value: Any) -> str:
        normalized = str(value or "UNKNOWN").upper()
        return THREAT_TYPE_LABELS.get(normalized, normalized.replace("_", " ").capitalize())

    @staticmethod
    def _spanish_sector(value: Any) -> str:
        normalized = str(value or "general_business")
        return SECTOR_LABELS.get(normalized, normalized.replace("_", " "))

    @staticmethod
    def _spanish_severity(value: Any) -> str:
        normalized = str(value or "").upper()
        return {
            "LOW": "baja",
            "MEDIUM": "media",
            "HIGH": "alta",
            "CRITICAL": "crítica",
        }.get(normalized, normalized.lower() or "sin clasificar")

    @staticmethod
    def _spanish_data_class(value: Any) -> str:
        text = str(value or "")
        return DATA_CLASS_LABELS.get(text, text)

    @staticmethod
    def _spanish_match_label(value: Any) -> str:
        text = str(value or "")
        return {
            "sector_landscape": "panorama del sector",
            "active_campaign": "campaña activa",
        }.get(text, text)

    @staticmethod
    def _footer(company: str, scan_date: str) -> str:
        return REPORT_FOOTER_TEMPLATE.format(company=company, date=scan_date)

    @staticmethod
    def _parse_date(value: Any) -> datetime | None:
        text = str(value or "").strip()
        if not text:
            return None
        try:
            parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
            if parsed.tzinfo is None:
                return parsed.replace(tzinfo=UTC)
            return parsed.astimezone(UTC)
        except ValueError:
            return None

    @staticmethod
    def _today() -> str:
        return datetime.now(UTC).date().isoformat()
