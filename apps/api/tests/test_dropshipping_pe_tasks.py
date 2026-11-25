import sqlite3
from concurrent.futures import ThreadPoolExecutor
import pytest
from app.services.dropshipping_pe_order_store import DemoOrder, Conflict, Paused
from app.services.dropshipping_pe_tasks import DemoTask, TaskStore


def connect(path):
    db = sqlite3.connect(path)
    db.row_factory = sqlite3.Row
    return db


@pytest.fixture
def setup(tmp_path):
    path=tmp_path/"queue.db"
    db=connect(path)
    store=TaskStore(db)
    store.initialize()
    order=store.orders.create(DemoOrder(reference="DEMO-1",provider="Dropi",cart={"lines":[{"product_id":"PE-019","pack":1,"quantity":1}],"region":"lima"}),"op","OPERATOR")
    yield store,order["id"],path
    db.close()


def task(oid,ref="DEMO-10",intent="order_confirmation",failures=0):
    return DemoTask(reference=ref,order_id=oid,intent=intent,simulated_failures=failures)


def test_retry_schedule_and_success(setup):
    s,oid,_=setup
    s.enqueue(task(oid,failures=2),"op","OPERATOR",now=100)
    first=s.tick("op","OPERATOR",now=100)["task"]
    assert first["state"]=="retry_wait" and first["due_at"]==130
    assert s.tick("op","OPERATOR",now=129)["task"] is None
    second=s.tick("op","OPERATOR",now=130)["task"]
    assert second["due_at"]==190 and second["attempts"]==2
    third=s.tick("op","OPERATOR",now=190)["task"]
    assert third["state"]=="draft_ready" and third["attempts"]==3
    assert not third["external_action_executed"]
    assert s.tick("op","OPERATOR",now=1000)["task"] is None


def test_escalation_and_review(setup):
    s,oid,_=setup
    t=s.enqueue(task(oid,failures=3),"op","OPERATOR",now=100)
    for now in (100,130,190):
        result=s.tick("op","OPERATOR",now=now)["task"]
    assert result["state"]=="escalated"
    with pytest.raises(PermissionError): s.acknowledge(t["id"],"op","OPERATOR")
    assert s.acknowledge(t["id"],"ceo","CEO")["state"]=="reviewed_demo"
    assert s.acknowledge(t["id"],"ceo","CEO")["duplicate"]
    assert s.tick("op","OPERATOR",now=1000)["task"] is None


def test_finance_requires_ceo(setup):
    s,oid,_=setup
    t=s.enqueue(task(oid,intent="settlement_difference"),"op","OPERATOR",now=10)
    assert s.tick("op","OPERATOR",now=10)["task"]["state"]=="awaiting_ceo"
    assert s.acknowledge(t["id"],"ceo","CEO")["state"]=="reviewed_demo"


def test_persistence_and_conflicts(setup):
    s,oid,path=setup
    t=s.enqueue(task(oid),"op","OPERATOR",now=10)
    db=connect(path)
    try:
        other=TaskStore(db)
        assert other.enqueue(task(oid),"another","ADMIN",now=20)["id"]==t["id"]
        with pytest.raises(Conflict): other.enqueue(task(oid,failures=1),"op","OPERATOR")
        with pytest.raises(Conflict): other.enqueue(task(oid,ref="DEMO-11"),"op","OPERATOR")
        assert other.tick("op","OPERATOR",now=20)["task"]["state"]=="draft_ready"
        assert len(other.snapshot()["audit"])==2
    finally: db.close()


def test_pause_and_permissions(setup):
    s,oid,_=setup
    with pytest.raises(PermissionError): s.enqueue(task(oid),"a","AUDITOR")
    s.enqueue(task(oid),"op","OPERATOR",now=10)
    with pytest.raises(PermissionError): s.tick("a","AUDITOR",now=10)
    s.orders.set_paused(True,"ceo","CEO")
    with pytest.raises(Paused): s.tick("op","OPERATOR",now=10)
    with pytest.raises(Paused): s.enqueue(task(oid,ref="DEMO-11",intent="delivery_delay"),"op","OPERATOR")
    s.orders.set_paused(False,"ceo","CEO")
    assert s.tick("op","OPERATOR",now=10)["task"]["state"]=="draft_ready"


def test_concurrent_tick_only_once(setup):
    s,oid,path=setup
    s.enqueue(task(oid),"op","OPERATOR",now=10)
    def tick(_):
        db=connect(path)
        try: return TaskStore(db).tick("op","OPERATOR",now=10)["task"]
        finally: db.close()
    with ThreadPoolExecutor(max_workers=4) as pool:
        results=list(pool.map(tick,range(4)))
    assert sum(x is not None for x in results)==1
    assert len(s.snapshot()["audit"])==2


def test_unknown_order(setup):
    s,_,_=setup
    with pytest.raises(ValueError): s.enqueue(task("DEMO-"+"0"*32),"op","OPERATOR")
