"""Local-only evidence rehearsal and deterministic operational playbooks."""
from datetime import UTC, datetime
from uuid import uuid4
import re

KINDS = {"stock", "cost", "logistics", "sample", "checkout", "legal"}
PROVIDERS = {"Dropi", "Aliclik", "Easydrop"}
PLAYBOOKS = {
    "availability": ("customer_service", "operator", "Confirmar disponibilidad y plazo antes de ofrecer el producto."),
    "order_confirmation": ("sales", "operator", "Revisar el pedido y confirmar condiciones antes de enviarlo."),
    "delivery_delay": ("logistics", "operator", "Consultar el estado con el proveedor; no prometer una fecha sin evidencia."),
    "return_request": ("after_sales", "CEO", "Revisar la solicitud y las condiciones aplicables; no aprobar ni rechazar automáticamente."),
    "settlement_difference": ("finance", "CEO", "Conciliar la diferencia con los comprobantes antes de registrar un ajuste."),
    "ad_campaign": ("marketing", "CEO", "Preparar creatividades y presupuesto para revisión; no publicar ni gastar."),
}


def playbook(intent):
    if intent not in PLAYBOOKS:
        raise ValueError("Unknown intent")
    agent, owner, draft = PLAYBOOKS[intent]
    return {"mode": "simulation", "agent": agent, "reviewer": owner, "draft": draft,
            "sent": False, "live_enabled": False, "llm_called": False}


class EvidenceStore:
    def __init__(self, connection, placeholder="?"):
        self.db = connection
        self.p = placeholder

    def initialize(self):
        self.db.execute("""CREATE TABLE IF NOT EXISTS pe_demo_evidence (
            id TEXT PRIMARY KEY, candidate TEXT NOT NULL, provider TEXT NOT NULL,
            kind TEXT NOT NULL, reference TEXT NOT NULL, actor TEXT NOT NULL,
            created_at TEXT NOT NULL, UNIQUE(candidate, provider, kind, reference))""")
        self.db.execute("""CREATE TABLE IF NOT EXISTS pe_demo_evidence_review (
            evidence_id TEXT PRIMARY KEY REFERENCES pe_demo_evidence(id),
            decision TEXT NOT NULL, actor TEXT NOT NULL, created_at TEXT NOT NULL)""")

    def submit(self, candidate, provider, kind, reference, actor, role):
        if role not in {"CEO", "ADMIN", "OPERATOR"}:
            raise PermissionError("Submission not allowed")
        if (not re.fullmatch(r"PE-(00[1-9]|01[0-9]|02[0-9]|030)", candidate)
                or provider not in PROVIDERS or kind not in KINDS
                or not re.fullmatch(r"DEMO-[0-9]{1,8}", reference)):
            raise ValueError("Invalid demo evidence")
        eid = uuid4().hex
        p = self.p
        cur = self.db.execute(f"""INSERT INTO pe_demo_evidence
            (id,candidate,provider,kind,reference,actor,created_at)
            VALUES ({','.join([p]*7)}) ON CONFLICT(candidate,provider,kind,reference) DO NOTHING""",
            (eid,candidate,provider,kind,reference,actor,datetime.now(UTC).isoformat()))
        if cur.rowcount != 1:
            raise ValueError("Duplicate evidence")
        return eid

    def review(self, eid, decision, actor, role):
        if role != "CEO":
            raise PermissionError("CEO review required")
        if decision not in {"accepted_demo", "rejected_demo"}:
            raise ValueError("Invalid review")
        p = self.p
        if self.db.execute(f"SELECT id FROM pe_demo_evidence WHERE id={p}", (eid,)).fetchone() is None:
            raise ValueError("Unknown evidence")
        cur = self.db.execute(f"""INSERT INTO pe_demo_evidence_review
            (evidence_id,decision,actor,created_at) VALUES ({','.join([p]*4)})
            ON CONFLICT(evidence_id) DO NOTHING""", (eid,decision,actor,datetime.now(UTC).isoformat()))
        if cur.rowcount != 1:
            raise ValueError("Evidence already reviewed")

    def snapshot(self):
        rows = self.db.execute("""SELECT e.id,e.candidate,e.provider,e.kind,e.reference,
            e.actor AS submitted_by,e.created_at,r.decision,r.actor AS reviewed_by,
            r.created_at AS reviewed_at FROM pe_demo_evidence e
            LEFT JOIN pe_demo_evidence_review r ON e.id=r.evidence_id
            ORDER BY e.created_at DESC,e.id DESC LIMIT 100""").fetchall()
        return {"mode": "simulation", "items": [dict(row) for row in rows],
                "live_enabled": False, "real_evidence_verified": False,
                "approved_for_sale": False}
