import hashlib
import hmac
import time
from types import SimpleNamespace
from fastapi.testclient import TestClient
from app.main import app
from app.schemas.auth import ControlCenterRole
from app.services.dropshipping_pe_order_store import canonical
from auth_helpers import auth_headers

PREFIX="/api/v1/ecommerce-readiness/dropshipping-pe"
SECRET="synthetic-api-test-key-no-real-credential"


def test_persistent_order_api_permissions_and_signed_event(monkeypatch,tmp_path):
    from app.api import ecommerce_readiness as routes
    monkeypatch.setattr(routes,"get_settings",lambda:SimpleNamespace(environment="local",database_url="sqlite:///"+str(tmp_path/"orders.db")))
    monkeypatch.setenv("DROPSHIPPING_DEMO_EVENT_SECRET",SECRET)
    client=TestClient(app)
    payload={"reference":"DEMO-1","provider":"Dropi","cart":{"lines":[{"product_id":"PE-019","pack":1,"quantity":1}],"region":"lima"}}
    path=PREFIX+"/persistent-orders"
    assert client.get(path).status_code==401
    assert client.post(path,json=payload).status_code==401
    operator=auth_headers(client,ControlCenterRole.operator)
    ceo=auth_headers(client,ControlCenterRole.ceo)
    auditor=auth_headers(client,ControlCenterRole.auditor)
    assert client.post(path,json=payload,headers=auditor).status_code==403
    result=client.post(path,json=payload,headers=operator)
    assert result.status_code==200
    oid=result.json()["id"]
    assert client.post(path,json=payload,headers=ceo).json()["duplicate"]
    event={"order_id":oid,"provider":"Dropi","event_id":"DEMO-1","code":"DEMO_DROPI_CONFIRMED","timestamp":int(time.time())}
    signed={**operator,"X-Demo-Signature":hmac.new(SECRET.encode(),canonical(event).encode(),hashlib.sha256).hexdigest()}
    assert client.post(PREFIX+"/demo-events",json=event,headers=operator).status_code==403
    assert client.post(PREFIX+"/demo-events",json=event,headers=signed).json()["state"]=="confirmed"
    assert client.post(PREFIX+"/demo-events",json=event,headers=signed).json()["duplicate"]
    assert client.post(PREFIX+"/demo-pause",json={"paused":True},headers=operator).status_code==403
    assert client.post(PREFIX+"/demo-pause",json={"paused":True},headers=ceo).json()["paused"]
    assert client.post(path,json={**payload,"reference":"DEMO-2"},headers=ceo).status_code==409
    assert client.get(path+"/"+oid,headers=auditor).json()["state"]=="confirmed"
    assert client.get(path,headers=ceo).json()["live_enabled"] is False
    monkeypatch.setattr(routes,"get_settings",lambda:SimpleNamespace(environment="production",database_url="sqlite:///"+str(tmp_path/"orders.db")))
    assert client.get(path,headers=ceo).status_code==503
