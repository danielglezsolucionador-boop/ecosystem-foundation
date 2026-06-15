from __future__ import annotations

from typing import Any


class CerebroIntelProtocol:
    ROUTING_RULES = {
        "LINKEDIN_WORTHY": {
            "trigger": [
                "new threat trend detected",
                "sector under attack",
                "new ransomware family",
                "zero day circulating",
            ],
            "cerebro_instruction": "Route to Marketing. Generate LinkedIn post.",
            "format": "public_bulletin",
        },
        "FORJA_ACTION": {
            "trigger": [
                "zero day exploit",
                "active attack campaign",
                "ransomware campaign",
                "new malware family",
            ],
            "cerebro_instruction": "Route to Forja. Build defensive tool.",
            "format": "construction_signal",
        },
        "CENTINELA_DEFENSE": {
            "trigger": [
                "client at risk",
                "credential exposure",
                "active attack on client",
            ],
            "cerebro_instruction": "Route to Centinela. Deploy defense.",
            "format": "defense_order",
        },
        "CEO_ONLY": {
            "trigger": [
                "A1-PARA-1",
                "A2-PARA-1",
                "legal risk",
                "ecosystem compromise",
            ],
            "cerebro_instruction": "Route to CEO immediately. Do not filter.",
            "format": "ceo_alert",
        },
    }

    def tag_intel(self, alert: Any) -> dict[str, Any]:
        alert_id = self._get(alert, "alert_id", "id", default="")
        severity = self._get(alert, "severity", "level", default="UNKNOWN")
        threat_type = self._get(alert, "threat_type", default="")
        findings = self._get(alert, "findings", "message", "executive_summary", default="")
        recommended_action = self._get(alert, "recommended_action", "action", default="")
        time_window = self._get(alert, "time_window", "response_window", default="")

        haystack = f"{findings} {threat_type}".lower()
        routes: list[str] = []
        instructions: list[str] = []
        formats: dict[str, str] = {}

        for route_name, config in self.ROUTING_RULES.items():
            for trigger in config["trigger"]:
                if trigger.lower() in haystack:
                    routes.append(route_name)
                    instructions.append(config["cerebro_instruction"])
                    formats[route_name] = config["format"]
                    break

        unique_routes = list(dict.fromkeys(routes))
        unique_instructions = list(dict.fromkeys(instructions))

        return {
            "alert_id": str(alert_id),
            "severity": str(severity),
            "routes": unique_routes,
            "cerebro_instructions": unique_instructions,
            "formats": formats,
            "auto_linkedin": "LINKEDIN_WORTHY" in unique_routes,
            "auto_forja": "FORJA_ACTION" in unique_routes,
            "auto_centinela": "CENTINELA_DEFENSE" in unique_routes,
            "ceo_required": "CEO_ONLY" in unique_routes,
            "payload": {
                "threat_type": str(threat_type),
                "findings": str(findings),
                "recommended_action": str(recommended_action),
                "time_window": str(time_window),
            },
        }

    @staticmethod
    def _get(alert: Any, *keys: str, default: Any = None) -> Any:
        if isinstance(alert, dict):
            for key in keys:
                if key in alert and alert[key] is not None:
                    return alert[key]
            return default
        for key in keys:
            value = getattr(alert, key, None)
            if value is not None:
                return value
        return default
