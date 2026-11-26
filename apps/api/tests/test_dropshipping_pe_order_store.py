import hashlib
import hmac
import sqlite3
from concurrent.futures import ThreadPoolExecutor
import pytest
from pydantic import ValidationError
from app.services.dropshipping_pe_order_store import (
    DemoOrder, SignedDemoEvent, OrderStore, Conflict, Paused, canonical, verify_demo_signature,
)

SECRET = "synthetic-test-key-only-not-a-credential"
NOW = 1700000000


def connect(path):
    db = sqlite3.connect(path)
    db.row_factory = sqlite3.Row
    return db


@pytest.fixture
def store(tmp_path):
    db = connect(tmp_path / "orders.db")
    s = OrderStore(db)
    s.initialize()
    yield s
    db.close()


def order(reference="DEMO-1", region="lima"):
    return DemoOrder(reference=reference, provider="Dropi", cart={
        "lines":[{"product_id":"PE-019","pack":1,"quantity":1}],"region":region})


def event(oid, event_id="DEMO-1", state="CONFIRMED", timestamp=NOW, provider="Dropi"):
    return SignedDemoEvent(order_id=oid,provider=provider,event_id=event_id,
                           code="DEMO_"+provider.upper()+"_"+state,timestamp=timestamp)


def signature(e):
    return hmac.new(SECRET.encode(), canonical(e.model_dump(mode="json")).encode(), hashlib.sha256).hexdigest()


def receive(store,e,role="OPERATOR"):
    return store.receive(e,signature(e),SECRET,"operator-2",role,now=NOW)


def test_persistent_order_and_event_replay(store):
    first = store.create(order(),"operator-1","OPERATOR")
    assert first["quote"]["total_cents"] == 10100
    e = event(first["id"])
    assert receive(store,e)["state"] == "confirmed"
    path = store.db.execute("PRAGMA database_list").fetchone()[2]
    db = connect(path)
    try:
        other = OrderStore(db)
        replay = other.create(order(),"operator-2","OPERATOR")
        assert replay["id"] == first["id"] and replay["duplicate"]
        assert receive(other,e)["duplicate"]
        assert len(other.snapshot()["audit"]) == 2
        assert len(other.get(first["id"])["events"]) == 1
        assert not replay["real_order_created"]
    finally:
        db.close()


def test_conflicting_reference(store):
    store.create(order(),"actor","CEO")
    with pytest.raises(Conflict):
        store.create(order(region="provincia"),"actor","CEO")


def test_event_id_conflict_across_orders(store):
    a = store.create(order(),"actor","CEO")
    b = store.create(order("DEMO-2"),"actor","CEO")
    receive(store,event(a["id"]))
    with pytest.raises(Conflict):
        receive(store,event(b["id"]))
    assert store.get(b["id"])["state"] == "received"


def test_invalid_transition_rolls_back(store):
    a = store.create(order(),"actor","CEO")
    with pytest.raises(Conflict):
        receive(store,event(a["id"],state="DELIVERED"))
    assert len(store.get(a["id"])["events"]) == 0
    assert len(store.snapshot()["audit"]) == 1


def test_state_sequence(store):
    a = store.create(order(),"actor","CEO")
    for i,state in enumerate(("CONFIRMED","DISPATCHED","DELIVERED","RETURNED"),1):
        result = receive(store,event(a["id"],f"DEMO-{i}",state))
    assert result["state"] == "returned" and len(result["events"]) == 4
    assert not result["supplier_contacted"] and not result["payment_processed"]


@pytest.mark.parametrize("sig",["","0"*64,"NOT_HEX"])
def test_bad_signatures(sig,store):
    a = store.create(order(),"actor","CEO")
    with pytest.raises(PermissionError):
        store.receive(event(a["id"]),sig,SECRET,"actor","CEO",now=NOW)
    assert not store.get(a["id"])["events"]


def test_expired_and_future_signatures(store):
    a = store.create(order(),"actor","CEO")
    for ts in (NOW-301,NOW+301):
        e = event(a["id"],timestamp=ts)
        with pytest.raises(PermissionError):
            receive(store,e)


def test_unconfigured_key(store):
    a = store.create(order(),"actor","CEO")
    e = event(a["id"])
    with pytest.raises(RuntimeError):
        verify_demo_signature(e,signature(e),"short",now=NOW)


def test_provider_mismatch(store):
    a = store.create(order(),"actor","CEO")
    with pytest.raises(ValueError):
        receive(store,event(a["id"],provider="Aliclik"))


def test_pause_persists_and_blocks_writes(store):
    a = store.create(order(),"actor","CEO")
    store.set_paused(True,"ceo","CEO")
    with pytest.raises(Paused):
        store.create(order("DEMO-2"),"actor","OPERATOR")
    with pytest.raises(Paused):
        receive(store,event(a["id"]))
    assert store.status()["paused"] and not store.status()["live_enabled"]
    store.set_paused(False,"ceo","CEO")
    assert receive(store,event(a["id"]))["state"] == "confirmed"


def test_role_permissions(store):
    with pytest.raises(PermissionError):
        store.create(order(),"auditor","AUDITOR")
    with pytest.raises(PermissionError):
        store.set_paused(True,"operator","OPERATOR")
    a = store.create(order(),"actor","CEO")
    with pytest.raises(PermissionError):
        receive(store,event(a["id"]),"AUDITOR")


def test_concurrent_create_is_idempotent(store):
    path = store.db.execute("PRAGMA database_list").fetchone()[2]
    def create(_):
        db = connect(path)
        try:
            return OrderStore(db).create(order(),"actor","OPERATOR")
        finally:
            db.close()
    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(create,range(4)))
    assert len({r["id"] for r in results}) == 1
    assert sum(not r["duplicate"] for r in results) == 1


@pytest.mark.parametrize("patch",[{"live":True},{"phone":"123"},{"reference":"real-123"}])
def test_forbidden_input(patch):
    payload = order().model_dump()
    with pytest.raises(ValidationError):
        DemoOrder.model_validate({**payload,**patch})
