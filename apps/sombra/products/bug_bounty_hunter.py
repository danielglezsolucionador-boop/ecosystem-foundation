from __future__ import annotations

import argparse
import base64
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime, timedelta
from html import unescape
import json
import os
from pathlib import Path
import re
import socket
import sqlite3
import ssl
import time
from typing import Any
import uuid
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


def _load_local_env() -> None:
    env_path = Path.cwd() / ".env"
    if not env_path.exists():
        return

    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        if key.startswith("export "):
            key = key.removeprefix("export ").strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


_load_local_env()


HACKERONE_PUBLIC_PROGRAMS_URL = "https://hackerone.com/programs.json"
HACKERONE_HACKER_PROGRAMS_URL = "https://api.hackerone.com/v1/hackers/programs"
BUGCROWD_PUBLIC_PROGRAMS_URL = "https://bugcrowd.com/programs.json"
BUGCROWD_ENGAGEMENTS_URL = "https://bugcrowd.com/engagements.json"
BUGCROWD_BASE_URL = "https://bugcrowd.com"
CEREBRO_INBOX_URL = os.getenv(
    "SOMBRA_CEREBRO_INBOX_URL",
    "https://ecosystem-foundation.vercel.app/api/v1/cerebro/inbox/sombra",
)
CEREBRO_TOKEN = os.getenv(
    "SOMBRA_CEREBRO_TOKEN",
    "kmbIwNC6lSVsXRhFdPtacfODGuW8YQH1JUgAn05zTi4EyvMjeZ3qLx79pKB2or",
)
CEREBRO_REPORT_TYPE = os.getenv("SOMBRA_CEREBRO_REPORT_TYPE", "scan_report")
CEREBRO_SOURCE = os.getenv("SOMBRA_CEREBRO_SOURCE", "sombra")
CEREBRO_SEVERITY = os.getenv("SOMBRA_CEREBRO_SEVERITY", "medium")
CEREBRO_AUDIENCE = [
    item.strip()
    for item in os.getenv("SOMBRA_CEREBRO_AUDIENCE", "centinela").split(",")
    if item.strip()
]

DEFAULT_CENTINELA_ROOT = Path(os.getenv("CENTINELA_ROOT", r"C:\Users\admin\Documents\CENTINELA"))
DEFAULT_OUTPUT_DIR = DEFAULT_CENTINELA_ROOT / "reportes" / "bugbounty"
DEFAULT_STATE_PATH = DEFAULT_CENTINELA_ROOT / "operaciones" / "bug_bounty_hunter_state.json"

USER_AGENT = os.getenv("SOMBRA_BUGBOUNTY_USER_AGENT", "Centinela-BugBountyHunter/1.0")
MAX_BUGCROWD_PAGES = int(os.getenv("SOMBRA_BUGBOUNTY_MAX_BUGCROWD_PAGES", "20"))
MAX_DETAIL_PROGRAMS = int(os.getenv("SOMBRA_BUGBOUNTY_MAX_DETAIL_PROGRAMS", "30"))
DEFAULT_SCOPE_DOMAINS = tuple(
    item.strip().lower()
    for item in os.getenv(
        "SOMBRA_BUGBOUNTY_SCOPE_DOMAINS",
        "bitso.com,hostgator.com.mx,nubank.com.br,quintoandar.com",
    ).split(",")
    if item.strip()
)
MAX_PASSIVE_SUBDOMAINS = int(os.getenv("SOMBRA_BUGBOUNTY_MAX_PASSIVE_SUBDOMAINS", "50"))
MAX_PASSIVE_HTTP_CHECKS = int(os.getenv("SOMBRA_BUGBOUNTY_MAX_PASSIVE_HTTP_CHECKS", "8"))
PASSIVE_TIMEOUT_SECONDS = int(os.getenv("SOMBRA_BUGBOUNTY_PASSIVE_TIMEOUT_SECONDS", "6"))
CRT_SH_URL = "https://crt.sh/?q=%25.{domain}&output=json"

SECURITY_HEADERS = {
    "strict-transport-security": "HSTS",
    "content-security-policy": "CSP",
    "x-frame-options": "X-Frame-Options",
    "x-content-type-options": "X-Content-Type-Options",
    "referrer-policy": "Referrer-Policy",
    "permissions-policy": "Permissions-Policy",
}
SENSITIVE_SUBDOMAIN_TERMS = {
    "admin",
    "auth",
    "beta",
    "dev",
    "grafana",
    "internal",
    "jira",
    "jenkins",
    "login",
    "panel",
    "portal",
    "preprod",
    "staging",
    "test",
    "vpn",
}
POC_TERMS = {
    "proof of concept",
    "poc",
    "exploit-db",
    "metasploit",
    "nuclei",
    "reproduce",
    "reproduction",
    "curl ",
    "http request",
}

LATAM_PATTERN = re.compile(
    r"\b("
    r"latam|latin america|latin american|america latina|peru|peruvian|colombia|colombian|"
    r"brazil|brasil|brazilian|mexico|chile|argentina|uruguay|paraguay|"
    r"bolivia|ecuador|panama|costa rica|dominican|guatemala|honduras|venezuela|"
    r"nubank|bitso|quintoandar|hostgator latam"
    r")\b|"
    r"\.(com\.)?(pe|co|br|mx|cl|ar|uy|py|bo|ec|pa|cr|gt|hn|ve)\b",
    re.IGNORECASE,
)
DOMAIN_PATTERN = re.compile(
    r"(?<!@)\b(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+"
    r"(?:com|net|org|io|ai|co|pe|br|mx|cl|ar|uy|py|bo|ec|pa|cr|gt|hn|ve|dev|app|cloud|finance)\b",
    re.IGNORECASE,
)
CVE_PATTERN = re.compile(r"\bCVE-\d{4}-\d{4,}\b", re.IGNORECASE)
PORT_PATTERN = re.compile(r"\b(?:port|tcp|udp)[:/\s-]*(\d{1,5})\b", re.IGNORECASE)

WEB_SCOPE_TERMS = {
    "web",
    "website",
    "web app",
    "web application",
    "api",
    "http",
    "https",
    "domain",
    "subdomain",
    "graphql",
    "oauth",
    "saml",
}


@dataclass
class FetchAttempt:
    source: str
    url: str
    status: str
    detail: str


@dataclass
class BugBountyProgram:
    platform: str
    name: str
    program_url: str
    handle: str = ""
    reward_summary: str = ""
    min_payout: int | None = None
    max_payout: int | None = None
    domains: list[str] = field(default_factory=list)
    web_scope: bool = False
    latam_presence: bool = False
    scope_summary: str = ""
    submission_url: str = ""
    deadline: str | None = None
    source_url: str = ""
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass
class VulnerabilitySignal:
    source: str
    signal_type: str
    title: str
    severity: str
    domain: str | None = None
    indicators: list[str] = field(default_factory=list)
    cve_id: str | None = None
    component_terms: list[str] = field(default_factory=list)
    published_at: str | None = None
    reference: str | None = None
    evidence: str = ""
    confidence: float = 0.5


@dataclass
class ProgramMatch:
    program: BugBountyProgram
    signal: VulnerabilitySignal
    confidence: float
    reasons: list[str]


@dataclass
class ReportableFinding:
    company_name: str
    program_url: str
    platform: str
    vulnerability_found: str
    severity: str
    estimated_payout_range: str
    how_to_report: str
    deadline: str
    in_scope: bool
    already_reported_status: str
    public_disclosures_checked: list[str]
    match_confidence: float
    report_draft: str


class BugBountyHunter:
    """Passive bug bounty opportunity matcher for Sombra/CENTINELA data.

    The class does not probe targets. It fetches public program metadata and
    compares it with locally stored Sombra/CENTINELA signals.
    """

    def __init__(
        self,
        centinela_root: Path | str = DEFAULT_CENTINELA_ROOT,
        output_dir: Path | str | None = None,
        state_path: Path | str | None = None,
        sombra_db_paths: list[Path | str] | None = None,
        timeout_seconds: int = 30,
        max_bugcrowd_pages: int = MAX_BUGCROWD_PAGES,
        max_detail_programs: int = MAX_DETAIL_PROGRAMS,
        scope_domains: list[str] | tuple[str, ...] | None = None,
        max_passive_subdomains: int = MAX_PASSIVE_SUBDOMAINS,
        max_passive_http_checks: int = MAX_PASSIVE_HTTP_CHECKS,
    ) -> None:
        self.centinela_root = Path(centinela_root)
        self.output_dir = Path(output_dir) if output_dir else self.centinela_root / "reportes" / "bugbounty"
        self.state_path = Path(state_path) if state_path else self.centinela_root / "operaciones" / "bug_bounty_hunter_state.json"
        self.sombra_db_paths = [Path(item) for item in sombra_db_paths or []]
        self.timeout_seconds = timeout_seconds
        self.max_bugcrowd_pages = max_bugcrowd_pages
        self.max_detail_programs = max_detail_programs
        self.scope_domains = [
            domain
            for domain in (self._clean_domain(item) for item in (scope_domains or DEFAULT_SCOPE_DOMAINS))
            if domain
        ]
        self.max_passive_subdomains = max_passive_subdomains
        self.max_passive_http_checks = max_passive_http_checks
        self.fetch_attempts: list[FetchAttempt] = []

    def run_once(self, today: datetime | None = None) -> dict[str, Any]:
        now = today or datetime.now(UTC)
        self.fetch_attempts = []
        programs = self.fetch_active_programs()
        local_signals = self.load_known_vulnerability_signals(now=now)
        scope_signal_matches = self.analyze_scope_signals(local_signals)
        passive_scope_signals = self.scan_scope_domains()
        signals = self._dedupe_signals([*local_signals, *passive_scope_signals])
        matches = self.match_with_known_vulnerabilities(programs, signals)
        findings = self.identify_reportable_findings(matches)
        pdf_path = self.generate_opportunity_report(
            programs,
            signals,
            matches,
            findings,
            passive_scope_signals=passive_scope_signals,
            scope_signal_matches=scope_signal_matches,
            now=now,
        )
        self._save_state(programs, signals, matches, findings, pdf_path, now)
        result = {
            "message_id": self._new_message_id(now),
            "generated_at": self._iso(now),
            "programs_fetched": len(programs),
            "signals_loaded": len(signals),
            "local_signals_loaded": len(local_signals),
            "scope_signal_matches": scope_signal_matches,
            "passive_scope_findings": [asdict(item) for item in passive_scope_signals],
            "matches_found": len(matches),
            "reportable_findings": len(findings),
            "immediate_opportunities": [asdict(item) for item in findings],
            "pdf_path": str(pdf_path),
            "fetch_attempts": [asdict(item) for item in self.fetch_attempts],
        }
        result["cerebro_delivery"] = self.send_result_to_cerebro(result)
        return result

    def send_result_to_cerebro(self, scan_result: dict[str, Any]) -> dict[str, Any]:
        payload = {
            "message_id": scan_result.get("message_id") or self._new_message_id(datetime.now(UTC)),
            "source": CEREBRO_SOURCE,
            "type": CEREBRO_REPORT_TYPE,
            "severity": CEREBRO_SEVERITY,
            "title": "Bug bounty hunter scan report",
            "created_at": scan_result.get("generated_at") or self._iso(datetime.now(UTC)),
            "audience": CEREBRO_AUDIENCE,
            "summary": self._cerebro_summary(scan_result),
        }
        request = Request(
            CEREBRO_INBOX_URL,
            data=json.dumps(payload, default=str).encode("utf-8"),
            headers={
                "Accept": "application/json",
                "Authorization": f"Bearer {CEREBRO_TOKEN}",
                "Content-Type": "application/json",
                "User-Agent": USER_AGENT,
            },
            method="POST",
        )
        try:
            with urlopen(request, timeout=self.timeout_seconds) as response:
                response_text = response.read().decode("utf-8", "replace")
                return {
                    "status": "sent",
                    "http_status": response.status,
                    "response": self._truncate(response_text, 500),
                }
        except HTTPError as error:
            detail = error.read().decode("utf-8", "replace") if error.fp else error.reason
            return {
                "status": "http_error",
                "http_status": error.code,
                "error": self._truncate(str(detail or error.reason), 500),
            }
        except URLError as error:
            return {
                "status": "network_error",
                "error": self._truncate(str(error.reason), 500),
            }
        except Exception as error:
            return {
                "status": "error",
                "error": self._truncate(repr(error), 500),
            }

    def fetch_active_programs(self) -> list[BugBountyProgram]:
        programs: list[BugBountyProgram] = []
        programs.extend(self._fetch_hackerone_programs())
        programs.extend(self._fetch_bugcrowd_programs())
        filtered = [program for program in programs if self._is_paid_web_latam_program(program)]
        return self._dedupe_programs(filtered)

    def match_with_known_vulnerabilities(
        self,
        programs: list[BugBountyProgram],
        signals: list[VulnerabilitySignal],
    ) -> list[ProgramMatch]:
        matches: list[ProgramMatch] = []
        for program in programs:
            program_domains = set(program.domains)
            program_text = self._program_text(program)
            for signal in signals:
                confidence, reasons = self._match_confidence(program, program_domains, program_text, signal)
                if confidence >= 0.62:
                    matches.append(ProgramMatch(program=program, signal=signal, confidence=confidence, reasons=reasons))
        return sorted(matches, key=lambda item: item.confidence, reverse=True)

    def identify_reportable_findings(self, matches: list[ProgramMatch]) -> list[ReportableFinding]:
        findings: list[ReportableFinding] = []
        for match in matches:
            in_scope, scope_reason = self._verify_in_scope(match)
            if not in_scope:
                continue
            report_status, checked_urls = self._check_public_disclosures(match)
            if report_status == "reported":
                continue
            findings.append(
                ReportableFinding(
                    company_name=match.program.name,
                    program_url=match.program.program_url,
                    platform=match.program.platform,
                    vulnerability_found=match.signal.title,
                    severity=self._normalize_severity(match.signal.severity),
                    estimated_payout_range=self._estimate_payout_range(match.program, match.signal.severity),
                    how_to_report=match.program.submission_url or match.program.program_url,
                    deadline=match.program.deadline or "None published",
                    in_scope=True,
                    already_reported_status=report_status,
                    public_disclosures_checked=checked_urls,
                    match_confidence=round(match.confidence, 2),
                    report_draft=self._build_report_draft(match, scope_reason, report_status),
                )
            )
        return findings

    def generate_opportunity_report(
        self,
        programs: list[BugBountyProgram],
        signals: list[VulnerabilitySignal],
        matches: list[ProgramMatch],
        findings: list[ReportableFinding],
        passive_scope_signals: list[VulnerabilitySignal] | None = None,
        scope_signal_matches: list[dict[str, Any]] | None = None,
        now: datetime | None = None,
    ) -> Path:
        passive_scope_signals = passive_scope_signals or []
        scope_signal_matches = scope_signal_matches or []
        report_date = (now or datetime.now(UTC)).date().isoformat()
        pdf_path = self.output_dir / f"opportunities_{report_date}.pdf"
        self.output_dir.mkdir(parents=True, exist_ok=True)

        styles = self._pdf_styles()
        doc = SimpleDocTemplate(
            str(pdf_path),
            pagesize=LETTER,
            rightMargin=0.62 * inch,
            leftMargin=0.62 * inch,
            topMargin=0.62 * inch,
            bottomMargin=0.62 * inch,
            title=f"Bug bounty opportunities - {report_date}",
            author="Centinela",
        )
        story: list[Any] = [
            Paragraph("CENTINELA", styles["brand"]),
            Paragraph("Bug Bounty Hunter Opportunity Report", styles["title"]),
            Paragraph(f"Generated: {report_date} UTC", styles["subtitle"]),
            Spacer(1, 16),
        ]

        summary_rows = [
            ["Paid LATAM web programs", str(len(programs))],
            ["Total vulnerability signals", str(len(signals))],
            ["Scoped local signal matches", str(len(scope_signal_matches))],
            ["Passive scoped findings", str(len(passive_scope_signals))],
            ["Potential matches", str(len(matches))],
            ["Immediate reportable opportunities", str(len(findings))],
        ]
        story.append(self._summary_table(summary_rows))
        story.append(Spacer(1, 14))

        if findings:
            story.append(Paragraph("Immediate Opportunities", styles["section"]))
            for finding in findings:
                rows = [
                    ["Company", finding.company_name],
                    ["Program URL", finding.program_url],
                    ["Vulnerability found", finding.vulnerability_found],
                    ["Severity", finding.severity],
                    ["Estimated payout", finding.estimated_payout_range],
                    ["How to report", finding.how_to_report],
                    ["Deadline", finding.deadline],
                    ["Already reported", finding.already_reported_status],
                ]
                story.append(self._detail_table(rows))
                story.append(Paragraph("Report draft", styles["subsection"]))
                story.append(Paragraph(self._escape(finding.report_draft), styles["body"]))
                story.append(Spacer(1, 10))
        else:
            story.append(Paragraph("Immediate Opportunities", styles["section"]))
            story.append(
                Paragraph(
                    "No confirmed reportable opportunities were found. The scan did not find a passive local signal that overlapped with an in-scope paid LATAM web bounty program.",
                    styles["body"],
                )
            )
            story.append(Spacer(1, 10))

        story.append(Paragraph("Scoped Domain Signal Analysis", styles["section"]))
        if scope_signal_matches:
            for item in scope_signal_matches[:12]:
                rows = [
                    ["Domains", ", ".join(item.get("scope_domains", []))],
                    ["Signal", str(item.get("title") or "")],
                    ["Severity", str(item.get("severity") or "")],
                    ["PoC status", str(item.get("poc_status") or "")],
                    ["Reportable", "yes" if item.get("reportable") else "no"],
                ]
                story.append(self._detail_table(rows))
                story.append(Spacer(1, 7))
        else:
            story.append(Paragraph("No recent local Sombra signal overlapped the configured scoped domains.", styles["body"]))
        story.append(Spacer(1, 8))

        story.append(Paragraph("Passive Scoped Surface Findings", styles["section"]))
        if passive_scope_signals:
            for signal in passive_scope_signals[:16]:
                rows = [
                    ["Domain", signal.domain or ""],
                    ["Finding", signal.title],
                    ["Severity", self._normalize_severity(signal.severity)],
                    ["Indicators", ", ".join(signal.indicators[:10])],
                    ["Evidence", signal.evidence],
                ]
                story.append(self._detail_table(rows))
                story.append(Spacer(1, 7))
        else:
            story.append(Paragraph("No passive scoped findings were produced in this run.", styles["body"]))
        story.append(Spacer(1, 8))

        story.append(Paragraph("Active LATAM Paid Web Programs", styles["section"]))
        if programs:
            for program in programs:
                rows = [
                    ["Company", program.name],
                    ["Program URL", program.program_url],
                    ["Payout range", program.reward_summary or self._format_payout(program)],
                    ["Domains observed", ", ".join(program.domains[:8]) or "Not published in public metadata"],
                    ["Deadline", program.deadline or "None published"],
                    ["Report channel", program.submission_url or program.program_url],
                ]
                story.append(self._detail_table(rows))
                story.append(Spacer(1, 7))
        else:
            story.append(Paragraph("No programs passed all filters in this run.", styles["body"]))

        story.append(Paragraph("Program Fetch Diagnostics", styles["section"]))
        for attempt in self.fetch_attempts:
            story.append(
                Paragraph(
                    self._escape(f"{attempt.source}: {attempt.status} - {attempt.url} - {attempt.detail}"),
                    styles["small"],
                )
            )

        doc.build(story)
        return pdf_path

    def run_daily_forever(self, hour_utc: int = 9, minute_utc: int = 0) -> None:
        while True:
            now = datetime.now(UTC)
            next_run = now.replace(hour=hour_utc, minute=minute_utc, second=0, microsecond=0)
            if next_run <= now:
                next_run += timedelta(days=1)
            time.sleep(max(1, int((next_run - now).total_seconds())))
            self.run_once()

    def load_known_vulnerability_signals(self, now: datetime | None = None, days: int = 30) -> list[VulnerabilitySignal]:
        now = now or datetime.now(UTC)
        cutoff = now - timedelta(days=days)
        signals: list[VulnerabilitySignal] = []
        for db_path in self._discover_sombra_db_paths():
            signals.extend(self._signals_from_sombra_db(db_path, cutoff))
        signals.extend(self._signals_from_local_reports(cutoff))
        return self._dedupe_signals(signals)

    def analyze_scope_signals(self, signals: list[VulnerabilitySignal]) -> list[dict[str, Any]]:
        matches: list[dict[str, Any]] = []
        for signal in signals:
            scope_domains = self._signal_scope_domains(signal)
            if not scope_domains:
                continue
            poc_status, has_valid_poc = self._assess_signal_poc(signal)
            severity = self._normalize_severity(signal.severity)
            matches.append(
                {
                    "scope_domains": scope_domains,
                    "title": signal.title,
                    "severity": severity,
                    "signal_type": signal.signal_type,
                    "source": signal.source,
                    "published_at": signal.published_at,
                    "domain": signal.domain,
                    "indicators": signal.indicators[:20],
                    "poc_status": poc_status,
                    "has_valid_poc": has_valid_poc,
                    "reportable": has_valid_poc and severity in {"HIGH", "CRITICAL"},
                    "evidence": signal.evidence,
                }
            )
        return sorted(matches, key=lambda item: (item["reportable"], item["severity"]), reverse=True)

    def scan_scope_domains(self) -> list[VulnerabilitySignal]:
        signals: list[VulnerabilitySignal] = []
        for domain in self.scope_domains:
            subdomains = self._fetch_ct_subdomains(domain)
            sensitive_subdomains = [host for host in subdomains if self._looks_sensitive_subdomain(host)]
            if sensitive_subdomains:
                signals.append(
                    VulnerabilitySignal(
                        source="Passive CT subdomain inventory",
                        signal_type="exposed_subdomain",
                        title=f"Potentially sensitive subdomains exposed for {domain}",
                        severity="LOW",
                        domain=domain,
                        indicators=sensitive_subdomains[:20],
                        evidence=(
                            f"Certificate transparency exposed {len(sensitive_subdomains)} sensitive-looking "
                            f"hostname(s): {', '.join(sensitive_subdomains[:12])}"
                        ),
                        confidence=0.55,
                    )
                )

            for host in self._select_passive_hosts(domain, subdomains):
                header_signal = self._security_header_signal(domain, host)
                if header_signal:
                    signals.append(header_signal)
                tls_signal = self._tls_certificate_signal(domain, host)
                if tls_signal:
                    signals.append(tls_signal)
        return self._dedupe_signals(signals)

    def _signal_scope_domains(self, signal: VulnerabilitySignal) -> list[str]:
        hits: list[str] = []
        signal_text = " ".join(
            [
                signal.title,
                signal.evidence,
                signal.domain or "",
                " ".join(signal.indicators),
                " ".join(signal.component_terms),
            ]
        ).lower()
        for domain in self.scope_domains:
            candidates = {domain}
            if signal.domain and self._domain_matches_any(signal.domain, candidates):
                hits.append(domain)
                continue
            indicator_hit = False
            for indicator in signal.indicators:
                clean = self._clean_domain(str(indicator))
                if clean and self._domain_matches_any(clean, candidates):
                    hits.append(domain)
                    indicator_hit = True
                    break
            if indicator_hit:
                continue
            if domain in signal_text:
                hits.append(domain)
        return hits

    def _assess_signal_poc(self, signal: VulnerabilitySignal) -> tuple[str, bool]:
        evidence_text = " ".join(
            [
                signal.title,
                signal.evidence,
                signal.reference or "",
                " ".join(signal.indicators),
            ]
        ).lower()
        if any(term in evidence_text for term in POC_TERMS):
            return "PoC indicator present in local evidence; manual reproduction required", True
        if signal.signal_type in {"exposed_service", "scan", "leakradar"} and signal.domain:
            return "domain-specific passive evidence present; validate manually before reporting", True
        return "No valid PoC or reproducible evidence in local signal", False

    def _fetch_ct_subdomains(self, domain: str) -> list[str]:
        url = CRT_SH_URL.format(domain=domain)
        payload = self._fetch_json(
            url,
            source=f"Certificate transparency {domain}",
            timeout_seconds=min(self.timeout_seconds, PASSIVE_TIMEOUT_SECONDS),
        )
        if not isinstance(payload, list):
            return []
        hosts: list[str] = []
        for item in payload[: self.max_passive_subdomains * 8]:
            if not isinstance(item, dict):
                continue
            name_value = str(item.get("name_value") or item.get("common_name") or "")
            for raw_host in name_value.splitlines():
                clean = self._clean_domain(raw_host.replace("*.", ""))
                if clean and self._domain_matches_any(clean, {domain}):
                    hosts.append(clean)
        return list(dict.fromkeys(hosts))[: self.max_passive_subdomains]

    def _select_passive_hosts(self, domain: str, subdomains: list[str]) -> list[str]:
        preferred = [
            domain,
            f"www.{domain}",
            f"api.{domain}",
            f"app.{domain}",
            f"auth.{domain}",
            f"login.{domain}",
            f"portal.{domain}",
            f"admin.{domain}",
        ]
        candidates = list(dict.fromkeys([*preferred, *subdomains]))

        def score(host: str) -> tuple[int, int, str]:
            if host == domain:
                return (0, len(host), host)
            label = host.removesuffix(f".{domain}").split(".")[0]
            if label in {"www", "api", "app", "auth", "login", "portal"}:
                return (1, len(host), host)
            if self._looks_sensitive_subdomain(host):
                return (2, len(host), host)
            return (3, len(host), host)

        scoped = [host for host in candidates if self._domain_matches_any(host, {domain})]
        return sorted(scoped, key=score)[: self.max_passive_http_checks]

    def _looks_sensitive_subdomain(self, host: str) -> bool:
        labels = set(re.split(r"[-.]", host.lower()))
        return bool(labels & SENSITIVE_SUBDOMAIN_TERMS)

    def _security_header_signal(self, scope_domain: str, host: str) -> VulnerabilitySignal | None:
        headers, status, final_url = self._fetch_response_headers(host)
        if not headers:
            return None
        final_host = self._clean_domain(urlparse(final_url).netloc or host)
        if final_host and not self._domain_matches_any(final_host, {scope_domain}):
            return None
        issues = self._header_issues(headers)
        if not issues:
            return None
        severity = "MEDIUM" if any(issue.startswith("missing HSTS") or issue.startswith("weak HSTS") for issue in issues) else "LOW"
        if len(issues) >= 4:
            severity = "MEDIUM"
        return VulnerabilitySignal(
            source="Passive HTTP security header check",
            signal_type="security_header",
            title=f"Security header hardening gaps on {host}",
            severity=severity,
            domain=host,
            indicators=[host, *issues[:8]],
            evidence=f"HTTP {status} at {final_url}; observed issues: {', '.join(issues)}",
            confidence=0.64 if severity == "MEDIUM" else 0.5,
        )

    def _fetch_response_headers(self, host: str) -> tuple[dict[str, str], int | None, str]:
        url = f"https://{host}/"
        for method in ("HEAD", "GET"):
            headers = {
                "Accept": "text/html,application/xhtml+xml,application/json;q=0.9,*/*;q=0.8",
                "User-Agent": USER_AGENT,
            }
            if method == "GET":
                headers["Range"] = "bytes=0-0"
            request = Request(url, headers=headers, method=method)
            try:
                with urlopen(request, timeout=min(self.timeout_seconds, PASSIVE_TIMEOUT_SECONDS)) as response:
                    response_headers = {key.lower(): str(value) for key, value in response.headers.items()}
                    final_url = response.geturl()
                    self.fetch_attempts.append(
                        FetchAttempt(
                            f"Security headers {host}",
                            url,
                            f"ok:{response.status}",
                            f"{len(response_headers)} headers; final={final_url}",
                        )
                    )
                    return response_headers, response.status, final_url
            except HTTPError as error:
                response_headers = {key.lower(): str(value) for key, value in (error.headers or {}).items()}
                self.fetch_attempts.append(
                    FetchAttempt(
                        f"Security headers {host}",
                        url,
                        f"http:{error.code}",
                        error.reason or f"{len(response_headers)} headers",
                    )
                )
                if error.code == 405 and method == "HEAD":
                    continue
                if response_headers:
                    return response_headers, error.code, url
                return {}, error.code, url
            except URLError as error:
                self.fetch_attempts.append(FetchAttempt(f"Security headers {host}", url, "network_error", str(error.reason)))
                return {}, None, url
            except Exception as error:
                self.fetch_attempts.append(FetchAttempt(f"Security headers {host}", url, "error", repr(error)))
                return {}, None, url
        return {}, None, url

    def _header_issues(self, headers: dict[str, str]) -> list[str]:
        issues: list[str] = []
        hsts = headers.get("strict-transport-security", "")
        if not hsts:
            issues.append("missing HSTS")
        else:
            max_age = re.search(r"max-age=(\d+)", hsts, re.IGNORECASE)
            if not max_age or int(max_age.group(1)) < 15552000:
                issues.append("weak HSTS max-age")
            if "includesubdomains" not in hsts.lower():
                issues.append("HSTS missing includeSubDomains")

        csp = headers.get("content-security-policy", "")
        if not csp:
            issues.append("missing CSP")
        elif "'unsafe-inline'" in csp.lower() or "*" in csp:
            issues.append("broad CSP directives")

        frame = headers.get("x-frame-options", "")
        if not frame and "frame-ancestors" not in csp.lower():
            issues.append("missing clickjacking protection")

        content_type = headers.get("x-content-type-options", "")
        if content_type.lower() != "nosniff":
            issues.append("missing X-Content-Type-Options nosniff")

        referrer = headers.get("referrer-policy", "")
        if not referrer or referrer.lower() in {"unsafe-url", "no-referrer-when-downgrade"}:
            issues.append("weak or missing Referrer-Policy")

        if not headers.get("permissions-policy"):
            issues.append("missing Permissions-Policy")
        return issues

    def _tls_certificate_signal(self, scope_domain: str, host: str) -> VulnerabilitySignal | None:
        try:
            context = ssl.create_default_context()
            with socket.create_connection(
                (host, 443),
                timeout=min(self.timeout_seconds, PASSIVE_TIMEOUT_SECONDS),
            ) as sock:
                with context.wrap_socket(sock, server_hostname=host) as tls:
                    cert = tls.getpeercert()
                    version = tls.version() or "unknown"
            self.fetch_attempts.append(FetchAttempt(f"TLS certificate {host}", host, "ok", f"TLS {version}"))
        except ssl.SSLCertVerificationError as error:
            self.fetch_attempts.append(FetchAttempt(f"TLS certificate {host}", host, "ssl_verify_error", str(error)))
            return VulnerabilitySignal(
                source="Passive TLS certificate check",
                signal_type="tls_certificate",
                title=f"TLS certificate validation failed on {host}",
                severity="HIGH",
                domain=host,
                indicators=[host],
                evidence=f"TLS certificate validation failed for {host}: {error}",
                confidence=0.82,
            )
        except (TimeoutError, OSError, ssl.SSLError) as error:
            self.fetch_attempts.append(FetchAttempt(f"TLS certificate {host}", host, "network_error", repr(error)))
            return None

        not_after = cert.get("notAfter") if isinstance(cert, dict) else None
        if not not_after:
            return None
        expires_at = datetime.fromtimestamp(ssl.cert_time_to_seconds(not_after), tz=UTC)
        days_remaining = (expires_at - datetime.now(UTC)).days
        if days_remaining < 0:
            severity = "HIGH"
            title = f"Expired TLS certificate on {host}"
        elif days_remaining <= 14:
            severity = "HIGH"
            title = f"TLS certificate expires soon on {host}"
        elif days_remaining <= 30:
            severity = "MEDIUM"
            title = f"TLS certificate nearing expiry on {host}"
        else:
            return None
        return VulnerabilitySignal(
            source="Passive TLS certificate check",
            signal_type="tls_certificate",
            title=title,
            severity=severity,
            domain=host,
            indicators=[host, expires_at.date().isoformat()],
            evidence=f"Certificate for {host} expires at {expires_at.date().isoformat()} UTC ({days_remaining} day(s) remaining).",
            confidence=0.82,
        )

    def _fetch_hackerone_programs(self) -> list[BugBountyProgram]:
        programs: list[BugBountyProgram] = []
        username = os.getenv("HACKERONE_USERNAME") or os.getenv("H1_USERNAME")
        token = os.getenv("HACKERONE_API_TOKEN") or os.getenv("H1_API_TOKEN")
        if not username or not token:
            payload = self._fetch_json(HACKERONE_PUBLIC_PROGRAMS_URL, source="HackerOne public list")
            if payload:
                programs.extend(self._parse_hackerone_payload(payload, HACKERONE_PUBLIC_PROGRAMS_URL))
            self.fetch_attempts.append(
                FetchAttempt(
                    "HackerOne Hacker API",
                    HACKERONE_HACKER_PROGRAMS_URL,
                    "skipped",
                    "Set HACKERONE_USERNAME and HACKERONE_API_TOKEN to enable authenticated program fetches.",
                )
            )
            return programs

        auth = base64.b64encode(f"{username}:{token}".encode("utf-8")).decode("ascii")
        page = 1
        while page <= 10:
            url = f"{HACKERONE_HACKER_PROGRAMS_URL}?page[number]={page}&page[size]=100"
            payload = self._fetch_json(url, source="HackerOne Hacker API", headers={"Authorization": f"Basic {auth}"})
            if not payload:
                break
            parsed = self._parse_hackerone_payload(payload, url)
            programs.extend(parsed)
            if not parsed or not self._has_next_page(payload):
                break
            page += 1
        return programs

    def _fetch_bugcrowd_programs(self) -> list[BugBountyProgram]:
        programs: list[BugBountyProgram] = []
        if os.getenv("SOMBRA_BUGBOUNTY_FETCH_BUGCROWD_LEGACY", "").lower() in {"1", "true", "yes"}:
            requested_payload = self._fetch_json(BUGCROWD_PUBLIC_PROGRAMS_URL, source="Bugcrowd requested list")
            if requested_payload:
                programs.extend(self._parse_bugcrowd_payload(requested_payload, BUGCROWD_PUBLIC_PROGRAMS_URL))

        seen_handles = {program.handle for program in programs if program.handle}
        for page in range(1, self.max_bugcrowd_pages + 1):
            url = (
                f"{BUGCROWD_ENGAGEMENTS_URL}?page={page}"
                "&target_categories=website&sort_by=promoted&sort_direction=desc"
            )
            payload = self._fetch_json(url, source="Bugcrowd public engagements")
            if not payload:
                break
            page_programs = self._parse_bugcrowd_payload(payload, url)
            for program in page_programs:
                if program.handle not in seen_handles:
                    programs.append(program)
                    seen_handles.add(program.handle)
            total = int((payload.get("paginationMeta") or {}).get("totalCount") or 0) if isinstance(payload, dict) else 0
            if len(seen_handles) >= total > 0:
                break

        candidates = [program for program in programs if self._program_has_latam_hint(program) and self._program_pays_money(program)]
        for program in candidates[: self.max_detail_programs]:
            self._enrich_bugcrowd_program(program)
        return programs

    def _parse_hackerone_payload(self, payload: Any, source_url: str) -> list[BugBountyProgram]:
        items = payload.get("data", payload) if isinstance(payload, dict) else payload
        if not isinstance(items, list):
            return []
        programs: list[BugBountyProgram] = []
        for item in items:
            if not isinstance(item, dict):
                continue
            attrs = item.get("attributes") or item
            name = str(attrs.get("name") or attrs.get("team_name") or attrs.get("handle") or "").strip()
            handle = str(attrs.get("handle") or item.get("id") or "").strip()
            if not name:
                continue
            program_url = attrs.get("url") or attrs.get("profile_picture") or f"https://hackerone.com/{handle}"
            scopes = attrs.get("structured_scopes") or attrs.get("structured_scope") or attrs.get("scopes") or []
            scope_text = json.dumps(scopes, default=str)
            reward_summary = str(attrs.get("bounty_summary") or attrs.get("currency") or "")
            domains = self._extract_domains(scope_text)
            min_payout, max_payout = self._parse_reward_range(reward_summary)
            offers_bounties = bool(attrs.get("offers_bounties") or attrs.get("bounty_table") or max_payout)
            programs.append(
                BugBountyProgram(
                    platform="HackerOne",
                    name=name,
                    handle=handle,
                    program_url=str(program_url),
                    reward_summary=reward_summary or ("Bounty enabled" if offers_bounties else ""),
                    min_payout=min_payout,
                    max_payout=max_payout,
                    domains=domains,
                    web_scope=self._has_web_scope(scope_text),
                    latam_presence=bool(LATAM_PATTERN.search(f"{name} {scope_text}")),
                    scope_summary=self._truncate(self._strip_tags(scope_text), 500),
                    submission_url=f"https://hackerone.com/{handle}/reports/new" if handle else str(program_url),
                    source_url=source_url,
                    raw=attrs,
                )
            )
        return programs

    def _parse_bugcrowd_payload(self, payload: Any, source_url: str) -> list[BugBountyProgram]:
        items = payload.get("engagements", payload.get("data", payload)) if isinstance(payload, dict) else payload
        if not isinstance(items, list):
            return []
        programs: list[BugBountyProgram] = []
        for item in items:
            if not isinstance(item, dict):
                continue
            attrs = item.get("attributes") or item
            name = str(attrs.get("name") or attrs.get("title") or "").strip()
            if not name:
                continue
            brief_url = str(attrs.get("briefUrl") or attrs.get("brief_url") or attrs.get("url") or "")
            program_url = urljoin(BUGCROWD_BASE_URL, brief_url) if brief_url else BUGCROWD_BASE_URL
            handle = self._handle_from_url(program_url)
            reward = attrs.get("rewardSummary") or attrs.get("reward_summary") or {}
            reward_summary = self._reward_summary_text(reward)
            min_payout, max_payout = self._parse_reward_range(reward_summary)
            product_type = attrs.get("productEngagementType") or attrs.get("product_engagement_type") or {}
            product_label = str(product_type.get("label") or product_type.get("productLabel") or "")
            raw_text = " ".join(
                str(value)
                for value in [
                    name,
                    attrs.get("tagline", ""),
                    attrs.get("industryName", ""),
                    product_label,
                    brief_url,
                    reward_summary,
                ]
            )
            programs.append(
                BugBountyProgram(
                    platform="Bugcrowd",
                    name=name,
                    handle=handle,
                    program_url=program_url,
                    reward_summary=reward_summary,
                    min_payout=min_payout,
                    max_payout=max_payout,
                    domains=self._extract_domains(raw_text),
                    web_scope=True,
                    latam_presence=bool(LATAM_PATTERN.search(raw_text)),
                    scope_summary=self._truncate(str(attrs.get("tagline") or ""), 500),
                    submission_url=program_url,
                    deadline=str(attrs.get("endsAt") or "") or None,
                    source_url=source_url,
                    raw=attrs,
                )
            )
        return programs

    def _enrich_bugcrowd_program(self, program: BugBountyProgram) -> None:
        if program.platform != "Bugcrowd" or not program.program_url:
            return
        html_text = self._fetch_text(program.program_url, source=f"Bugcrowd brief {program.handle}", accept="text/html")
        if not html_text:
            return
        props = self._extract_bugcrowd_data_props(html_text)
        description_html = ""
        if props:
            early_props = props.get("earlyFetchProps") or {}
            header = early_props.get("headerProps") or {}
            description_html = str(early_props.get("description") or "")
            program.deadline = program.deadline or (str(header.get("endsAt") or "") or None)
            program.scope_summary = self._truncate(self._strip_tags(description_html), 1200) or program.scope_summary
        text = self._strip_tags(description_html or html_text)
        domains = list(dict.fromkeys([*program.domains, *self._extract_domains(text)]))
        program.domains = domains
        program.latam_presence = program.latam_presence or bool(LATAM_PATTERN.search(f"{program.name} {text} {' '.join(domains)}"))
        program.web_scope = program.web_scope or self._has_web_scope(text)
        program.deadline = program.deadline or self._extract_deadline(text)
        if description_html:
            program.raw = {**program.raw, "public_brief_excerpt": self._truncate(text, 2000)}

    def _signals_from_sombra_db(self, db_path: Path, cutoff: datetime) -> list[VulnerabilitySignal]:
        if not db_path.exists():
            return []
        signals: list[VulnerabilitySignal] = []
        try:
            connection = sqlite3.connect(db_path)
            connection.row_factory = sqlite3.Row
            rows = connection.execute(
                """
                SELECT id, timestamp_utc, threat_type, severity, findings, indicators,
                       source_category, source_reliability, threat_score, prediction
                FROM sombra_intel_global
                WHERE timestamp_utc >= ?
                ORDER BY threat_score DESC, timestamp_utc DESC
                """,
                (self._iso(cutoff),),
            ).fetchall()
        except sqlite3.Error as error:
            self.fetch_attempts.append(FetchAttempt("Sombra memory", str(db_path), "error", str(error)))
            return []
        finally:
            try:
                connection.close()
            except Exception:
                pass

        for row in rows:
            record = dict(row)
            timestamp = self._parse_datetime(record.get("timestamp_utc"))
            if timestamp and timestamp < cutoff:
                continue
            indicators = self._json_list(record.get("indicators"))
            prediction = self._json_obj(record.get("prediction"))
            haystack = " ".join(
                [str(record.get("findings") or ""), json.dumps(indicators, default=str), json.dumps(prediction, default=str)]
            )
            threat_type = str(record.get("threat_type") or "").upper()
            severity = str(record.get("severity") or "UNKNOWN")
            if threat_type == "VULNERABILITY_PUBLISHED":
                cve_id = self._first_cve(haystack)
                component_terms = self._component_terms(indicators, haystack)
                title = cve_id or self._component_title(component_terms) or "Recent published vulnerability"
                signals.append(
                    VulnerabilitySignal(
                        source=f"Sombra memory ({db_path.name})",
                        signal_type="cve",
                        title=title,
                        severity=severity,
                        indicators=indicators,
                        cve_id=cve_id,
                        component_terms=component_terms,
                        published_at=str(record.get("timestamp_utc") or ""),
                        evidence=self._truncate(str(record.get("findings") or ""), 700),
                        confidence=min(0.95, 0.5 + (int(record.get("threat_score") or 0) / 200)),
                    )
                )
            elif threat_type in {"CREDENTIAL_EXPOSURE", "ZERO_DAY_EXPLOIT", "ACTIVE_ATTACK_CAMPAIGN"}:
                for domain in self._extract_domains(haystack):
                    signals.append(
                        VulnerabilitySignal(
                            source=f"Sombra memory ({db_path.name})",
                            signal_type=threat_type.lower(),
                            title=self._title_from_threat(threat_type, domain),
                            severity=severity,
                            domain=domain,
                            indicators=indicators,
                            published_at=str(record.get("timestamp_utc") or ""),
                            evidence=self._truncate(str(record.get("findings") or ""), 700),
                            confidence=0.75,
                        )
                    )
        self.fetch_attempts.append(FetchAttempt("Sombra memory", str(db_path), "ok", f"{len(signals)} recent signals parsed"))
        return signals

    def _signals_from_local_reports(self, cutoff: datetime) -> list[VulnerabilitySignal]:
        signals: list[VulnerabilitySignal] = []
        report_roots = [self.centinela_root / "reportes"]
        for db_path in self._discover_sombra_db_paths():
            report_roots.append(db_path.parents[1] / "reports")
        for root in report_roots:
            if not root.exists():
                continue
            for path in root.rglob("*.json"):
                try:
                    if self._mtime_datetime(path) < cutoff:
                        continue
                    payload = json.loads(path.read_text(encoding="utf-8"))
                except Exception:
                    continue
                signals.extend(self._signals_from_report_payload(path, payload))
        return signals

    def _signals_from_report_payload(self, path: Path, payload: Any) -> list[VulnerabilitySignal]:
        signals: list[VulnerabilitySignal] = []
        if isinstance(payload, list):
            for item in payload:
                signals.extend(self._signals_from_report_payload(path, item))
            return signals
        if not isinstance(payload, dict):
            return signals

        domain = self._clean_domain(str(payload.get("domain") or "")) if payload.get("domain") else None
        company = str(payload.get("company") or payload.get("client_name") or "")
        risk_level = str(payload.get("risk_level") or payload.get("severity") or "MEDIUM")
        exposures = payload.get("exposures_found")
        external_signals = self._safe_int(payload.get("external_signals"))

        if domain and external_signals > 0:
            signals.append(
                VulnerabilitySignal(
                    source=f"CENTINELA report ({path.name})",
                    signal_type="leakradar",
                    title=f"LeakRadar-style external exposure signals for {domain}",
                    severity=risk_level,
                    domain=domain,
                    indicators=[domain, company],
                    evidence=f"{external_signals} external signal(s) recorded in local report.",
                    confidence=0.72,
                )
            )

        if isinstance(exposures, list):
            for exposure in exposures:
                if not isinstance(exposure, dict):
                    continue
                exposure_domain = self._clean_domain(str(exposure.get("domain") or domain or "")) if (exposure.get("domain") or domain) else None
                if not exposure_domain:
                    continue
                exposure_type = str(exposure.get("type") or "").lower()
                if "sin expos" in exposure_type or "no " in str(exposure.get("title", "")).lower()[:12]:
                    continue
                signals.append(
                    VulnerabilitySignal(
                        source=f"CENTINELA report ({path.name})",
                        signal_type="scan",
                        title=str(exposure.get("title") or f"Exposure finding for {exposure_domain}"),
                        severity=risk_level,
                        domain=exposure_domain,
                        indicators=[exposure_domain],
                        evidence=self._truncate(json.dumps(exposure, ensure_ascii=True, default=str), 700),
                        confidence=0.78,
                    )
                )

        for service in self._iter_service_findings(payload):
            service_domain = service.get("domain") or domain
            if not service_domain:
                continue
            signals.append(
                VulnerabilitySignal(
                    source=f"Scan data ({path.name})",
                    signal_type="exposed_service",
                    title=service.get("title") or f"Exposed service on {service_domain}",
                    severity=service.get("severity") or risk_level,
                    domain=service_domain,
                    indicators=service.get("indicators") or [service_domain],
                    evidence=service.get("evidence") or "",
                    confidence=0.8,
                )
            )
        return signals

    def _iter_service_findings(self, payload: Any) -> list[dict[str, Any]]:
        findings: list[dict[str, Any]] = []
        if isinstance(payload, dict):
            for key, value in payload.items():
                key_lower = str(key).lower()
                if key_lower in {"open_ports", "exposed_services", "services", "ports"} and isinstance(value, list):
                    for item in value:
                        findings.append(self._normalize_service_finding(item))
                else:
                    findings.extend(self._iter_service_findings(value))
        elif isinstance(payload, list):
            for item in payload:
                findings.extend(self._iter_service_findings(item))
        return [item for item in findings if item]

    def _normalize_service_finding(self, item: Any) -> dict[str, Any]:
        if isinstance(item, dict):
            text = json.dumps(item, default=str)
            domains = self._extract_domains(text)
            port = item.get("port") or item.get("number")
            title = str(item.get("title") or item.get("service") or item.get("name") or "")
            if port:
                title = f"{title or 'Service'} exposed on port {port}"
            return {
                "domain": domains[0] if domains else self._clean_domain(str(item.get("domain") or item.get("host") or "")) or None,
                "title": title,
                "severity": str(item.get("severity") or item.get("risk") or "MEDIUM"),
                "indicators": domains + ([str(port)] if port else []),
                "evidence": self._truncate(text, 700),
            }
        text = str(item)
        domains = self._extract_domains(text)
        ports = PORT_PATTERN.findall(text)
        if not domains and not ports:
            return {}
        return {
            "domain": domains[0] if domains else None,
            "title": f"Exposed service {ports[0]}" if ports else "Exposed service",
            "severity": "MEDIUM",
            "indicators": domains + ports,
            "evidence": self._truncate(text, 700),
        }

    def _match_confidence(
        self,
        program: BugBountyProgram,
        program_domains: set[str],
        program_text: str,
        signal: VulnerabilitySignal,
    ) -> tuple[float, list[str]]:
        confidence = 0.0
        reasons: list[str] = []
        if signal.domain and self._domain_matches_any(signal.domain, program_domains):
            confidence += 0.75
            reasons.append(f"signal domain {signal.domain} overlaps program scope")
        for indicator in signal.indicators:
            clean = self._clean_domain(str(indicator))
            if clean and self._domain_matches_any(clean, program_domains):
                confidence += 0.65
                reasons.append(f"indicator {clean} overlaps program scope")
                break
        signal_text = " ".join(
            [
                signal.title,
                signal.evidence,
                signal.domain or "",
                " ".join(signal.indicators),
                " ".join(signal.component_terms),
            ]
        ).lower()
        for domain in program_domains:
            if domain and domain in signal_text:
                confidence += 0.4
                reasons.append(f"program domain {domain} appears in signal text")
                break
        component_hits = [term for term in signal.component_terms if len(term) >= 4 and term.lower() in program_text]
        if component_hits:
            confidence += 0.35
            reasons.append(f"affected component appears in public scope text: {', '.join(component_hits[:3])}")
        name_tokens = self._name_tokens(program.name)
        if name_tokens and any(token in signal_text for token in name_tokens):
            confidence += 0.25
            reasons.append("program name appears in signal text")
        if signal.signal_type in {"scan", "leakradar", "exposed_service"} and signal.domain:
            confidence += 0.08
            reasons.append("signal came from local exposure/scan data")
        return min(confidence, 0.98), reasons

    def _verify_in_scope(self, match: ProgramMatch) -> tuple[bool, str]:
        program_domains = set(match.program.domains)
        if match.signal.domain and self._domain_matches_any(match.signal.domain, program_domains):
            return True, f"{match.signal.domain} appears in public program scope/domain metadata."
        for indicator in match.signal.indicators:
            clean = self._clean_domain(str(indicator))
            if clean and self._domain_matches_any(clean, program_domains):
                return True, f"{clean} appears in public program scope/domain metadata."
        if match.signal.signal_type == "cve" and match.signal.component_terms:
            program_text = self._program_text(match.program)
            if any(term.lower() in program_text for term in match.signal.component_terms):
                return True, "Affected component appears in public program brief; manual target validation required before submission."
        return False, "No public in-scope overlap was found."

    def _check_public_disclosures(self, match: ProgramMatch) -> tuple[str, list[str]]:
        checked_urls: list[str] = []
        terms = [match.signal.cve_id or "", match.signal.domain or "", *match.signal.component_terms[:3]]
        terms = [term.lower() for term in terms if term]
        if match.program.platform == "Bugcrowd" and match.program.handle:
            known_url = f"{BUGCROWD_BASE_URL}/engagements/{match.program.handle}/engagement_known_issues.json"
            checked_urls.append(known_url)
            payload = self._fetch_json(known_url, source=f"Bugcrowd known issues {match.program.handle}")
            if payload:
                haystack = json.dumps(payload, default=str).lower()
                if any(term in haystack for term in terms):
                    return "reported", checked_urls
                return "not found in accessible known-issues feed", checked_urls
        return "unknown - public known-issues feed unavailable or unauthenticated", checked_urls

    def _build_report_draft(self, match: ProgramMatch, scope_reason: str, report_status: str) -> str:
        signal = match.signal
        program = match.program
        evidence = signal.evidence or "Passive local signal matched program metadata."
        cve_text = f" ({signal.cve_id})" if signal.cve_id else ""
        return (
            f"Title: Potential {self._normalize_severity(signal.severity)} issue for {program.name}{cve_text}\n\n"
            f"Summary: Sombra matched a passive local signal to the public {program.platform} program for {program.name}. "
            f"The signal is: {signal.title}.\n\n"
            f"Scope validation: {scope_reason}\n\n"
            f"Evidence source: {signal.source}. Evidence excerpt: {evidence}\n\n"
            f"Duplicate check: {report_status}.\n\n"
            "Recommended next step: manually validate the affected asset under the program rules of engagement before submitting. "
            "Do not run intrusive testing unless the program brief explicitly authorizes it."
        )

    def _discover_sombra_db_paths(self) -> list[Path]:
        paths: list[Path] = [Path(item) for item in self.sombra_db_paths if Path(item).exists()]
        env_path = os.getenv("SOMBRA_BUGBOUNTY_DB") or os.getenv("SOMBRA_DB_PATH")
        if env_path and Path(env_path).exists():
            paths.append(Path(env_path))
        current = Path.cwd() / "apps" / "sombra" / "data" / "sombra.db"
        if current.exists():
            paths.append(current)
        docs = Path.home() / "Documents" / "Codex"
        if docs.exists():
            try:
                paths.extend(docs.rglob("apps/sombra/data/sombra.db"))
            except Exception:
                pass
        deduped: dict[str, Path] = {}
        for path in paths:
            try:
                deduped[str(path.resolve())] = path
            except Exception:
                deduped[str(path)] = path
        return sorted(deduped.values(), key=lambda item: item.stat().st_mtime if item.exists() else 0, reverse=True)[:5]

    def _fetch_json(
        self,
        url: str,
        source: str,
        headers: dict[str, str] | None = None,
        timeout_seconds: int | None = None,
    ) -> Any | None:
        text = self._fetch_text(url, source=source, accept="application/json", headers=headers, timeout_seconds=timeout_seconds)
        if not text:
            return None
        try:
            return json.loads(text)
        except json.JSONDecodeError as error:
            self.fetch_attempts.append(FetchAttempt(source, url, "parse_error", str(error)))
            return None

    def _fetch_text(
        self,
        url: str,
        source: str,
        accept: str = "application/json",
        headers: dict[str, str] | None = None,
        timeout_seconds: int | None = None,
    ) -> str | None:
        request_headers = {
            "Accept": accept,
            "User-Agent": USER_AGENT,
            **(headers or {}),
        }
        request = Request(url, headers=request_headers, method="GET")
        try:
            with urlopen(request, timeout=timeout_seconds or self.timeout_seconds) as response:
                text = response.read().decode("utf-8", "replace")
                self.fetch_attempts.append(FetchAttempt(source, url, f"ok:{response.status}", f"{len(text)} bytes"))
                return text
        except HTTPError as error:
            self.fetch_attempts.append(FetchAttempt(source, url, f"http:{error.code}", error.reason or "HTTP error"))
        except URLError as error:
            self.fetch_attempts.append(FetchAttempt(source, url, "network_error", str(error.reason)))
        except Exception as error:
            self.fetch_attempts.append(FetchAttempt(source, url, "error", repr(error)))
        return None

    def _is_paid_web_latam_program(self, program: BugBountyProgram) -> bool:
        return self._program_pays_money(program) and program.web_scope and self._program_has_latam_hint(program)

    def _program_pays_money(self, program: BugBountyProgram) -> bool:
        text = f"{program.reward_summary} {program.min_payout or ''} {program.max_payout or ''}"
        return "$" in text or (program.max_payout or 0) > 0

    def _program_has_latam_hint(self, program: BugBountyProgram) -> bool:
        text = self._program_text(program)
        return program.latam_presence or bool(LATAM_PATTERN.search(text))

    def _program_text(self, program: BugBountyProgram) -> str:
        return " ".join(
            [
                program.name,
                program.handle,
                program.program_url,
                program.reward_summary,
                " ".join(program.domains),
                program.scope_summary,
                json.dumps(program.raw, default=str)[:3000],
            ]
        ).lower()

    def _has_web_scope(self, text: str) -> bool:
        lower = text.lower()
        return any(term in lower for term in WEB_SCOPE_TERMS)

    def _extract_bugcrowd_data_props(self, html_text: str) -> dict[str, Any]:
        match = re.search(r'data-props="([^"]+)"', html_text)
        if not match:
            return {}
        try:
            return json.loads(unescape(match.group(1)))
        except json.JSONDecodeError:
            return {}

    def _extract_domains(self, text: str) -> list[str]:
        domains: list[str] = []
        for match in DOMAIN_PATTERN.findall(text.replace("\\/", "/")):
            value = match if isinstance(match, str) else match[0]
            clean = self._clean_domain(value)
            if clean and not self._domain_is_noise(clean):
                domains.append(clean)
        return list(dict.fromkeys(domains))

    def _clean_domain(self, value: str) -> str | None:
        clean = str(value or "").strip().lower()
        clean = re.sub(r"^https?://", "", clean).split("/")[0].split(":")[0].strip(".*_-. ")
        if "." not in clean or "@" in clean:
            return None
        if not re.fullmatch(r"[a-z0-9.-]+\.[a-z]{2,}", clean):
            return None
        return clean

    def _domain_is_noise(self, domain: str) -> bool:
        noisy_suffixes = {
            "bugcrowd.com",
            "bugcrowdusercontent.com",
            "w3.org",
            "schema.org",
            "example.com",
            "github.com",
            "linkedin.com",
            "facebook.com",
            "twitter.com",
            "x.com",
            "youtube.com",
        }
        return any(domain == suffix or domain.endswith(f".{suffix}") for suffix in noisy_suffixes)

    def _domain_matches_any(self, domain: str, candidates: set[str]) -> bool:
        clean = self._clean_domain(domain)
        if not clean:
            return False
        for candidate in candidates:
            candidate_clean = self._clean_domain(candidate)
            if not candidate_clean:
                continue
            if clean == candidate_clean or clean.endswith(f".{candidate_clean}") or candidate_clean.endswith(f".{clean}"):
                return True
        return False

    def _component_terms(self, indicators: list[str], haystack: str) -> list[str]:
        terms: list[str] = []
        for indicator in indicators:
            if str(indicator).startswith("cpe:"):
                parts = str(indicator).split(":")
                if len(parts) > 5:
                    terms.extend([parts[3].replace("_", " "), parts[4].replace("_", " ")])
        for cve in CVE_PATTERN.findall(haystack):
            terms.append(cve.upper())
        return [term for term in dict.fromkeys(term.strip(" *:-_").lower() for term in terms) if len(term) >= 3]

    def _component_title(self, terms: list[str]) -> str:
        if not terms:
            return ""
        return "Recent published vulnerability affecting " + ", ".join(terms[:3])

    def _first_cve(self, text: str) -> str | None:
        match = CVE_PATTERN.search(text)
        return match.group(0).upper() if match else None

    def _title_from_threat(self, threat_type: str, domain: str) -> str:
        labels = {
            "CREDENTIAL_EXPOSURE": "Credential exposure signal",
            "ZERO_DAY_EXPLOIT": "Zero-day exploitation signal",
            "ACTIVE_ATTACK_CAMPAIGN": "Active attack campaign signal",
        }
        return f"{labels.get(threat_type, threat_type.replace('_', ' ').title())} for {domain}"

    def _check_hall_of_fame_only(self, text: str) -> bool:
        lower = text.lower()
        return "hall of fame" in lower and "$" not in lower and "bounty" not in lower

    def _parse_reward_range(self, text: str) -> tuple[int | None, int | None]:
        amounts = []
        for match in re.findall(r"\$\s*([0-9][0-9,]*)", str(text)):
            try:
                amounts.append(int(match.replace(",", "")))
            except ValueError:
                continue
        if not amounts:
            return None, None
        return min(amounts), max(amounts)

    def _reward_summary_text(self, reward: Any) -> str:
        if isinstance(reward, dict):
            summary = reward.get("summary")
            if summary:
                return str(summary)
            values = [
                reward.get("minReward"),
                reward.get("maxReward"),
                reward.get("compensationSummary"),
                reward.get("compensationHint"),
            ]
            return " - ".join(str(value) for value in values if value)
        return str(reward or "")

    def _estimate_payout_range(self, program: BugBountyProgram, severity: str) -> str:
        low = program.min_payout or 0
        high = program.max_payout or low
        if high <= 0:
            return program.reward_summary or "Published payout unavailable"
        normalized = self._normalize_severity(severity)
        if normalized == "CRITICAL":
            return f"${max(low, int(high * 0.65)):,} - ${high:,}"
        if normalized == "HIGH":
            return f"${max(low, int(high * 0.35)):,} - ${max(low, int(high * 0.75)):,}"
        if normalized == "MEDIUM":
            return f"${low:,} - ${max(low, int(high * 0.4)):,}"
        return f"${low:,} - ${max(low, int(high * 0.2)):,}"

    def _format_payout(self, program: BugBountyProgram) -> str:
        if program.min_payout is None and program.max_payout is None:
            return "Published payout unavailable"
        if program.min_payout == program.max_payout:
            return f"${program.max_payout:,}"
        return f"${program.min_payout or 0:,} - ${program.max_payout or 0:,}"

    def _extract_deadline(self, text: str) -> str | None:
        patterns = [
            r"(?:through|until|ends?|deadline)[:\s]+([A-Z][a-z]+ \d{1,2}, \d{4})",
            r"([A-Z][a-z]+ \d{1,2}, \d{4})\s*(?:-|to|through)\s*([A-Z][a-z]+ \d{1,2}, \d{4})",
        ]
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(match.lastindex or 1)
        return None

    def _has_next_page(self, payload: Any) -> bool:
        if not isinstance(payload, dict):
            return False
        links = payload.get("links") or {}
        return bool(links.get("next"))

    def _handle_from_url(self, url: str) -> str:
        return str(url).rstrip("/").split("/")[-1]

    def _dedupe_programs(self, programs: list[BugBountyProgram]) -> list[BugBountyProgram]:
        deduped: dict[tuple[str, str], BugBountyProgram] = {}
        for program in programs:
            if self._check_hall_of_fame_only(program.reward_summary):
                continue
            key = (program.platform, program.handle or program.program_url or program.name)
            existing = deduped.get(key)
            if not existing:
                deduped[key] = program
                continue
            existing.domains = list(dict.fromkeys([*existing.domains, *program.domains]))
            existing.scope_summary = existing.scope_summary or program.scope_summary
            existing.deadline = existing.deadline or program.deadline
        return sorted(deduped.values(), key=lambda item: (item.platform, item.name.lower()))

    def _dedupe_signals(self, signals: list[VulnerabilitySignal]) -> list[VulnerabilitySignal]:
        deduped: dict[tuple[str, str, str], VulnerabilitySignal] = {}
        for signal in signals:
            key = (signal.signal_type, signal.domain or "", signal.title.lower())
            existing = deduped.get(key)
            if not existing or signal.confidence > existing.confidence:
                deduped[key] = signal
        return sorted(deduped.values(), key=lambda item: item.confidence, reverse=True)

    def _save_state(
        self,
        programs: list[BugBountyProgram],
        signals: list[VulnerabilitySignal],
        matches: list[ProgramMatch],
        findings: list[ReportableFinding],
        pdf_path: Path,
        now: datetime,
    ) -> None:
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        previous = self._load_json_file(self.state_path) or {}
        previous_program_keys = set(previous.get("program_keys", []))
        current_program_keys = [f"{program.platform}:{program.handle or program.program_url}" for program in programs]
        state = {
            "generated_at": self._iso(now),
            "program_keys": current_program_keys,
            "new_programs": [key for key in current_program_keys if key not in previous_program_keys],
            "program_count": len(programs),
            "signal_count": len(signals),
            "match_count": len(matches),
            "reportable_findings_count": len(findings),
            "pdf_path": str(pdf_path),
        }
        self.state_path.write_text(json.dumps(state, indent=2, sort_keys=True), encoding="utf-8")

    def _load_json_file(self, path: Path) -> Any | None:
        if not path.exists():
            return None
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return None

    def _json_list(self, value: Any) -> list[str]:
        if isinstance(value, list):
            return [str(item) for item in value]
        if isinstance(value, str):
            try:
                parsed = json.loads(value)
                if isinstance(parsed, list):
                    return [str(item) for item in parsed]
            except json.JSONDecodeError:
                return [value]
        return []

    def _json_obj(self, value: Any) -> dict[str, Any]:
        if isinstance(value, dict):
            return value
        if isinstance(value, str):
            try:
                parsed = json.loads(value)
                return parsed if isinstance(parsed, dict) else {}
            except json.JSONDecodeError:
                return {}
        return {}

    def _safe_int(self, value: Any) -> int:
        try:
            return int(value or 0)
        except (TypeError, ValueError):
            return 0

    def _name_tokens(self, name: str) -> list[str]:
        stop = {"managed", "bug", "bounty", "program", "engagement", "public", "latam", "brasil"}
        return [token for token in re.findall(r"[a-z0-9]{4,}", name.lower()) if token not in stop]

    def _normalize_severity(self, severity: str) -> str:
        text = str(severity or "").upper()
        if "CRIT" in text:
            return "CRITICAL"
        if "HIGH" in text or "ALTO" in text:
            return "HIGH"
        if "MED" in text:
            return "MEDIUM"
        if "LOW" in text or "BAJO" in text:
            return "LOW"
        return "MEDIUM"

    def _strip_tags(self, value: str) -> str:
        text = re.sub(r"<br\s*/?>", "\n", value, flags=re.IGNORECASE)
        text = re.sub(r"<[^>]+>", " ", text)
        return re.sub(r"\s+", " ", unescape(text)).strip()

    def _truncate(self, value: str, limit: int) -> str:
        clean = re.sub(r"\s+", " ", str(value or "")).strip()
        if len(clean) <= limit:
            return clean
        return clean[: limit - 3].rstrip() + "..."

    def _escape(self, value: str) -> str:
        return (
            str(value or "")
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace("\n", "<br/>")
        )

    def _parse_datetime(self, value: Any) -> datetime | None:
        text = str(value or "").strip()
        if not text:
            return None
        try:
            parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
        except ValueError:
            return None
        if parsed.tzinfo is None:
            return parsed.replace(tzinfo=UTC)
        return parsed.astimezone(UTC)

    def _mtime_datetime(self, path: Path) -> datetime:
        return datetime.fromtimestamp(path.stat().st_mtime, tz=UTC)

    def _iso(self, value: datetime) -> str:
        return value.astimezone(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")

    def _new_message_id(self, now: datetime) -> str:
        stamp = now.astimezone(UTC).strftime("%Y%m%dT%H%M%SZ")
        return f"bug-bounty-hunter-{stamp}-{uuid.uuid4().hex[:12]}"

    def _cerebro_summary(self, scan_result: dict[str, Any]) -> str:
        return (
            f"Bug bounty hunter scan generated_at={scan_result.get('generated_at')} "
            f"programs={scan_result.get('programs_fetched')} "
            f"signals={scan_result.get('signals_loaded')} "
            f"scope_matches={len(scan_result.get('scope_signal_matches') or [])} "
            f"passive_findings={len(scan_result.get('passive_scope_findings') or [])} "
            f"matches={scan_result.get('matches_found')} "
            f"reportable={scan_result.get('reportable_findings')} "
            f"pdf={scan_result.get('pdf_path', '')}"
        )

    def _pdf_styles(self) -> dict[str, ParagraphStyle]:
        return {
            "brand": ParagraphStyle("brand", fontName="Helvetica-Bold", fontSize=13, leading=16, alignment=TA_CENTER, textColor=colors.HexColor("#17324D"), spaceAfter=5),
            "title": ParagraphStyle("title", fontName="Helvetica-Bold", fontSize=18, leading=22, alignment=TA_CENTER, textColor=colors.HexColor("#111827"), spaceAfter=4),
            "subtitle": ParagraphStyle("subtitle", fontName="Helvetica", fontSize=9, leading=12, alignment=TA_CENTER, textColor=colors.HexColor("#4B5563")),
            "section": ParagraphStyle("section", fontName="Helvetica-Bold", fontSize=12.5, leading=15, textColor=colors.HexColor("#17324D"), spaceBefore=10, spaceAfter=7),
            "subsection": ParagraphStyle("subsection", fontName="Helvetica-Bold", fontSize=10.5, leading=13, textColor=colors.HexColor("#374151"), spaceBefore=6, spaceAfter=4),
            "body": ParagraphStyle("body", fontName="Helvetica", fontSize=9.5, leading=13.5, alignment=TA_LEFT, textColor=colors.HexColor("#1F2937"), spaceAfter=5),
            "small": ParagraphStyle("small", fontName="Helvetica", fontSize=8.2, leading=11, textColor=colors.HexColor("#4B5563"), spaceAfter=3),
        }

    def _summary_table(self, rows: list[list[str]]) -> Table:
        table = Table(rows, colWidths=[4.7 * inch, 1.5 * inch])
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F3F4F6")),
                    ("BOX", (0, 0), (-1, -1), 0.4, colors.HexColor("#D1D5DB")),
                    ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#E5E7EB")),
                    ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                    ("FONTNAME", (1, 0), (1, -1), "Helvetica"),
                    ("FONTSIZE", (0, 0), (-1, -1), 9.5),
                    ("LEFTPADDING", (0, 0), (-1, -1), 8),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                    ("TOPPADDING", (0, 0), (-1, -1), 6),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ]
            )
        )
        return table

    def _detail_table(self, rows: list[list[str]]) -> Table:
        style = self._pdf_styles()
        rendered = [[Paragraph(self._escape(left), style["small"]), Paragraph(self._escape(right), style["small"])] for left, right in rows]
        table = Table(rendered, colWidths=[1.45 * inch, 5.25 * inch])
        table.setStyle(
            TableStyle(
                [
                    ("BOX", (0, 0), (-1, -1), 0.35, colors.HexColor("#D1D5DB")),
                    ("INNERGRID", (0, 0), (-1, -1), 0.2, colors.HexColor("#E5E7EB")),
                    ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#F9FAFB")),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 6),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                    ("TOPPADDING", (0, 0), (-1, -1), 5),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ]
            )
        )
        return table


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the Sombra BugBountyHunter passive opportunity scan.")
    parser.add_argument("--once", action="store_true", help="Run one scan and exit.")
    parser.add_argument("--daily", action="store_true", help="Run forever, once per day at 09:00 UTC.")
    parser.add_argument("--centinela-root", default=str(DEFAULT_CENTINELA_ROOT), help="CENTINELA root directory.")
    parser.add_argument("--output-dir", default=None, help="PDF output directory.")
    parser.add_argument("--db", action="append", default=[], help="Optional Sombra SQLite database path. Can be repeated.")
    parser.add_argument("--max-detail-programs", type=int, default=MAX_DETAIL_PROGRAMS, help="Maximum public briefs to enrich per run.")
    parser.add_argument("--scope-domain", action="append", default=[], help="Domain to include in scoped passive analysis. Can be repeated.")
    parser.add_argument("--max-passive-subdomains", type=int, default=MAX_PASSIVE_SUBDOMAINS, help="Maximum CT subdomains retained per scoped domain.")
    parser.add_argument("--max-passive-http-checks", type=int, default=MAX_PASSIVE_HTTP_CHECKS, help="Maximum passive HTTP/TLS checks per scoped domain.")
    return parser


def main() -> None:
    parser = build_arg_parser()
    args = parser.parse_args()
    hunter = BugBountyHunter(
        centinela_root=args.centinela_root,
        output_dir=args.output_dir,
        sombra_db_paths=args.db,
        max_detail_programs=args.max_detail_programs,
        scope_domains=args.scope_domain or None,
        max_passive_subdomains=args.max_passive_subdomains,
        max_passive_http_checks=args.max_passive_http_checks,
    )
    if args.daily:
        hunter.run_daily_forever()
        return
    result = hunter.run_once()
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
