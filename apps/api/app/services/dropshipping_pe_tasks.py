"""Persistent, local-only task rehearsal. Each tick executes one internal draft."""
from typing import Annotated, Literal
from uuid import uuid4
import time

from pydantic import BaseModel, ConfigDict, Field

from app.services.dropshipping_pe_order_store import DemoRef, OrderId, OrderStore, Conflict, Paused, now_iso
from app.services.dropshipping_pe_evidence import playbook

Intent = Literal["order_confirmation", "delivery_delay", "return_request", "settlement_difference"]
MAX_ATTEMPTS = 3


class DemoTask(BaseModel):
    model_config = ConfigDict(extra="forbid")
    reference: DemoRef
    order_id: OrderId
    intent: Intent
    simulated_failures: Annotated[int, Field(strict=True, ge=0, le=3)] = 0


class TaskStore:
    def __init__(self, db):
        self.db = db
        self.orders = OrderStore(db)

    def initialize(self):
        self.orders.initialize()
        with self.db:
            self.db.execute("""CREATE TABLE IF NOT EXISTS pe_demo_tasks (
                id TEXT PRIMARY KEY, reference TEXT NOT NULL UNIQUE,
                order_id TEXT NOT NULL REFERENCES pe_demo_orders(id), intent TEXT NOT NULL,
                simulated_failures INTEGER NOT NULL, attempts INTEGER NOT NULL,
                state TEXT NOT NULL, due_at INTEGER NOT NULL, result TEXT,
                actor TEXT NOT NULL, created_at TEXT NOT NULL,
                UNIQUE(order_id,intent))""")
            self.db.execute("""CREATE TABLE IF NOT EXISTS pe_demo_task_audit (
                id INTEGER PRIMARY KEY, task_id TEXT NOT NULL REFERENCES pe_demo_tasks(id),
                action TEXT NOT NULL, actor TEXT NOT NULL, created_at TEXT NOT NULL)""")

    def _audit(self, task_id, action, actor):
        self.db.execute("INSERT INTO pe_demo_task_audit(task_id,action,actor,created_at) VALUES(?,?,?,?)",
                        (task_id,action,actor,now_iso()))

    def _role(self, role):
        if role not in {"CEO","ADMIN","OPERATOR"}:
            raise PermissionError("Task write forbidden")

    def _get(self, task_id):
        row = self.db.execute("SELECT * FROM pe_demo_tasks WHERE id=?", (task_id,)).fetchone()
        if row is None:
            raise ValueError("Unknown task")
        return {**dict(row), "mode":"simulation","live_enabled":False,
                "external_action_executed":False,"llm_called":False}

    def enqueue(self, task, actor, role, now=None):
        self._role(role)
        now = int(time.time() if now is None else now)
        with self.db:
            self.db.execute("BEGIN IMMEDIATE")
            old = self.db.execute("SELECT * FROM pe_demo_tasks WHERE reference=?", (task.reference,)).fetchone()
            if old:
                if (old["order_id"],old["intent"],old["simulated_failures"]) != (task.order_id,task.intent,task.simulated_failures):
                    raise Conflict("Task reference reused with different payload")
                return {**self._get(old["id"]), "duplicate":True}
            if self.orders.is_paused():
                raise Paused("Demo operations paused")
            self.orders.get(task.order_id)
            if self.db.execute("SELECT id FROM pe_demo_tasks WHERE order_id=? AND intent=?",(task.order_id,task.intent)).fetchone():
                raise Conflict("Order already has this task intent")
            tid = "TASK-" + uuid4().hex
            self.db.execute("""INSERT INTO pe_demo_tasks
                (id,reference,order_id,intent,simulated_failures,attempts,state,due_at,result,actor,created_at)
                VALUES(?,?,?,?,?,0,'queued',?,NULL,?,?)""",
                (tid,task.reference,task.order_id,task.intent,task.simulated_failures,now,actor,now_iso()))
            self._audit(tid,"queued",actor)
            return {**self._get(tid),"duplicate":False}

    def tick(self, actor, role, now=None):
        self._role(role)
        now = int(time.time() if now is None else now)
        with self.db:
            self.db.execute("BEGIN IMMEDIATE")
            if self.orders.is_paused():
                raise Paused("Demo operations paused")
            row = self.db.execute("""SELECT * FROM pe_demo_tasks
                WHERE state IN ('queued','retry_wait') AND due_at<=?
                ORDER BY due_at,rowid LIMIT 1""",(now,)).fetchone()
            if row is None:
                return {"task":None,"mode":"simulation","live_enabled":False,"external_action_executed":False}
            attempts = row["attempts"] + 1
            if attempts <= row["simulated_failures"]:
                state = "escalated" if attempts >= MAX_ATTEMPTS else "retry_wait"
                due = now + 30 * (2 ** (attempts-1)) if state == "retry_wait" else now
                result = "Simulated transient failure; CEO review required" if state == "escalated" else "Simulated transient failure"
            else:
                plan = playbook(row["intent"])
                state = "awaiting_ceo" if plan["reviewer"] == "CEO" else "draft_ready"
                due = now
                result = plan["draft"]
            self.db.execute("UPDATE pe_demo_tasks SET attempts=?,state=?,due_at=?,result=? WHERE id=?",
                            (attempts,state,due,result,row["id"]))
            self._audit(row["id"],state,actor)
            return {"task":self._get(row["id"]),"mode":"simulation","live_enabled":False,"external_action_executed":False}

    def acknowledge(self, task_id, actor, role):
        if role != "CEO":
            raise PermissionError("CEO review required")
        with self.db:
            self.db.execute("BEGIN IMMEDIATE")
            row = self._get(task_id)
            if row["state"] == "reviewed_demo":
                return {**row,"duplicate":True}
            if row["state"] not in {"escalated","awaiting_ceo"}:
                raise Conflict("Task is not awaiting CEO review")
            self.db.execute("UPDATE pe_demo_tasks SET state='reviewed_demo' WHERE id=?",(task_id,))
            self._audit(task_id,"reviewed_demo",actor)
            return {**self._get(task_id),"duplicate":False}

    def snapshot(self):
        items = self.db.execute("SELECT id FROM pe_demo_tasks ORDER BY rowid DESC LIMIT 100").fetchall()
        audit = self.db.execute("SELECT task_id,action,actor,created_at FROM pe_demo_task_audit ORDER BY id DESC LIMIT 100").fetchall()
        return {"mode":"simulation","live_enabled":False,"external_action_executed":False,
                "worker_running":False,"paused":self.orders.is_paused(),
                "items":[self._get(row["id"]) for row in items],"audit":[dict(row) for row in audit]}
