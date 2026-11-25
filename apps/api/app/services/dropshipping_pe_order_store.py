"""Local persistent order rehearsal. No real orders, payment or outbound calls."""
import hashlib
import hmac
import json
import re
import time
from datetime import UTC, datetime
from uuid import uuid4
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field
from app.api.dropshipping_storefront import Cart, quote
from app.services.dropshipping_pe_pipeline import Provider, CODES, TRANSITIONS

DemoRef = Annotated[str, Field(pattern=r"^DEMO-[0-9]{1,8}$")]
OrderId = Annotated[str, Field(pattern=r"^DEMO-[0-9a-f]{32}$")]
MAX_CLOCK_SKEW_SECONDS = 300


class DemoOrder(BaseModel):
    model_config = ConfigDict(extra="forbid")
    reference: DemoRef
    provider: Provider
    cart: Cart


class SignedDemoEvent(BaseModel):
    model_config = ConfigDict(extra="forbid")
    order_id: OrderId
    provider: Provider
    event_id: DemoRef
    code: str = Field(min_length=1, max_length=64)
    timestamp: Annotated[int, Field(strict=True, ge=0, le=4102444800)]


class Conflict(ValueError):
    pass


class Paused(ValueError):
    pass


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def verify_demo_signature(event, signature, secret, now=None):
    # Internal synthetic protocol, NOT an actual provider webhook specification.
    if not isinstance(secret, str) or len(secret.encode()) < 32:
        raise RuntimeError("Demo signature key not configured")
    if not isinstance(signature, str) or not re.fullmatch(r"[0-9a-f]{64}", signature):
        raise PermissionError("Invalid signature")
    expected = hmac.new(secret.encode(), canonical(event.model_dump(mode="json")).encode(),
                        hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, signature):
        raise PermissionError("Invalid signature")
    if abs((time.time() if now is None else now) - event.timestamp) > MAX_CLOCK_SKEW_SECONDS:
        raise PermissionError("Expired event")


def now_iso():
    return datetime.now(UTC).isoformat()


class OrderStore:
    """SQLite only; all writes serialized in transactions with BEGIN IMMEDIATE."""
    def __init__(self, db):
        self.db = db

    def initialize(self):
        with self.db:
            self.db.execute("CREATE TABLE IF NOT EXISTS pe_demo_control (id INTEGER PRIMARY KEY CHECK(id=1), paused INTEGER NOT NULL CHECK(paused IN (0,1)))")
            self.db.execute("INSERT INTO pe_demo_control(id,paused) VALUES(1,0) ON CONFLICT(id) DO NOTHING")
            self.db.execute("""CREATE TABLE IF NOT EXISTS pe_demo_orders (
                id TEXT PRIMARY KEY, reference TEXT NOT NULL UNIQUE, provider TEXT NOT NULL,
                request_hash TEXT NOT NULL, quote_json TEXT NOT NULL, state TEXT NOT NULL,
                actor TEXT NOT NULL, created_at TEXT NOT NULL)""")
            self.db.execute("""CREATE TABLE IF NOT EXISTS pe_demo_order_events (
                provider TEXT NOT NULL, event_id TEXT NOT NULL, order_id TEXT NOT NULL REFERENCES pe_demo_orders(id),
                code TEXT NOT NULL, state TEXT NOT NULL, actor TEXT NOT NULL, created_at TEXT NOT NULL,
                PRIMARY KEY(provider,event_id))""")
            self.db.execute("""CREATE TABLE IF NOT EXISTS pe_demo_order_audit (
                id INTEGER PRIMARY KEY, order_id TEXT, action TEXT NOT NULL,
                actor TEXT NOT NULL, created_at TEXT NOT NULL)""")

    def is_paused(self):
        return bool(self.db.execute("SELECT paused FROM pe_demo_control WHERE id=1").fetchone()[0])

    def _audit(self, order_id, action, actor):
        self.db.execute("INSERT INTO pe_demo_order_audit(order_id,action,actor,created_at) VALUES(?,?,?,?)",
                        (order_id, action, actor, now_iso()))

    def _write_role(self, role):
        if role not in {"CEO", "ADMIN", "OPERATOR"}:
            raise PermissionError("Write forbidden")

    def set_paused(self, paused, actor, role):
        if role != "CEO" or type(paused) is not bool:
            raise PermissionError("CEO pause control required")
        with self.db:
            self.db.execute("BEGIN IMMEDIATE")
            if self.is_paused() != paused:
                self.db.execute("UPDATE pe_demo_control SET paused=? WHERE id=1", (int(paused),))
                self._audit(None, "pause_demo" if paused else "resume_demo", actor)
        return self.status()

    def status(self):
        return {"mode":"simulation", "paused":self.is_paused(), "live_enabled":False,
                "real_order_created":False, "external_webhooks_enabled":False,
                "persistent_demo_idempotency":True}

    def create(self, request, actor, role):
        self._write_role(role)
        data = request.model_dump(mode="json")
        data["cart"]["lines"].sort(key=lambda line: (line["product_id"], line["pack"]))
        digest = hashlib.sha256(canonical(data).encode()).hexdigest()
        with self.db:
            self.db.execute("BEGIN IMMEDIATE")
            old = self.db.execute("SELECT id,request_hash FROM pe_demo_orders WHERE reference=?", (request.reference,)).fetchone()
            if old:
                if old["request_hash"] != digest:
                    raise Conflict("Reference already used with different payload")
                return {**self.get(old["id"]), "duplicate":True}
            if self.is_paused():
                raise Paused("Demo operations paused")
            order = quote(Cart.model_validate(data["cart"]))
            oid = "DEMO-" + uuid4().hex
            self.db.execute("""INSERT INTO pe_demo_orders
                (id,reference,provider,request_hash,quote_json,state,actor,created_at)
                VALUES(?,?,?,?,?,?,?,?)""",
                (oid,request.reference,request.provider.value,digest,canonical(order),"received",actor,now_iso()))
            self._audit(oid,"create_demo",actor)
            return {**self.get(oid), "duplicate":False}

    def receive(self, event, signature, secret, actor, role, now=None):
        self._write_role(role)
        verify_demo_signature(event, signature, secret, now)
        with self.db:
            self.db.execute("BEGIN IMMEDIATE")
            row = self.db.execute("SELECT provider,state FROM pe_demo_orders WHERE id=?", (event.order_id,)).fetchone()
            if not row or row["provider"] != event.provider.value:
                raise ValueError("Unknown order or provider mismatch")
            old = self.db.execute("SELECT order_id,code FROM pe_demo_order_events WHERE provider=? AND event_id=?",
                                  (event.provider.value,event.event_id)).fetchone()
            if old:
                if old["order_id"] != event.order_id or old["code"] != event.code:
                    raise Conflict("Event ID reused with different payload")
                return {**self.get(event.order_id), "duplicate":True}
            if self.is_paused():
                raise Paused("Demo operations paused")
            stage = CODES[event.provider].get(event.code)
            if stage is None or stage not in TRANSITIONS.get(row["state"], set()):
                raise Conflict("Invalid state transition")
            self.db.execute("""INSERT INTO pe_demo_order_events
                (provider,event_id,order_id,code,state,actor,created_at) VALUES(?,?,?,?,?,?,?)""",
                (event.provider.value,event.event_id,event.order_id,event.code,stage.value,actor,now_iso()))
            self.db.execute("UPDATE pe_demo_orders SET state=? WHERE id=?", (stage.value,event.order_id))
            self._audit(event.order_id,"event_"+stage.value,actor)
            return {**self.get(event.order_id), "duplicate":False}

    def get(self, oid):
        row = self.db.execute("SELECT id,reference,provider,state,quote_json,created_at FROM pe_demo_orders WHERE id=?", (oid,)).fetchone()
        if row is None:
            raise ValueError("Unknown order")
        events = self.db.execute("SELECT event_id,code,state,created_at FROM pe_demo_order_events WHERE order_id=? ORDER BY rowid", (oid,)).fetchall()
        return {"id":row["id"],"reference":row["reference"],"provider":row["provider"],
                "state":row["state"],"quote":json.loads(row["quote_json"]),"created_at":row["created_at"],
                "events":[dict(e) for e in events],"mode":"simulation","live_enabled":False,
                "real_order_created":False,"payment_processed":False,"supplier_contacted":False}

    def snapshot(self):
        rows = self.db.execute("SELECT id,reference,provider,state,created_at FROM pe_demo_orders ORDER BY rowid DESC LIMIT 100").fetchall()
        audit = self.db.execute("SELECT order_id,action,actor,created_at FROM pe_demo_order_audit ORDER BY id DESC LIMIT 100").fetchall()
        return {**self.status(),"items":[dict(r) for r in rows],"audit":[dict(r) for r in audit]}
