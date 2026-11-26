from types import SimpleNamespace
from fastapi.testclient import TestClient
from app.main import app
from app.schemas.auth import ControlCenterRole
from auth_helpers import auth_headers

PREFIX="/api/v1/ecommerce-readiness/dropshipping-pe"


def test_task_queue_api(monkeypatch,tmp_path):
    from app.api import ecommerce_readiness as routes
    monkeypatch.setattr(routes,"get_settings",lambda:SimpleNamespace(environment="local",database_url="sqlite:///"+str(tmp_path/"tasks.db")))
    c=TestClient(app)
    op=auth_headers(c,ControlCenterRole.operator)
    ceo=auth_headers(c,ControlCenterRole.ceo)
    auditor=auth_headers(c,ControlCenterRole.auditor)
    order=c.post(PREFIX+"/persistent-orders",headers=op,json={"reference":"DEMO-1","provider":"Dropi","cart":{"lines":[{"product_id":"PE-019","pack":1,"quantity":1}],"region":"lima"}})
    assert order.status_code==200
    data={"reference":"DEMO-2","order_id":order.json()["id"],"intent":"settlement_difference"}
    path=PREFIX+"/tasks"
    assert c.get(path).status_code==401
    assert c.post(path,headers=auditor,json=data).status_code==403
    t=c.post(path,headers=op,json=data)
    assert t.status_code==200
    tid=t.json()["id"]
    assert c.post(path,headers=op,json=data).json()["duplicate"]
    assert c.post(path+"/tick",headers=op).json()["task"]["state"]=="awaiting_ceo"
    assert c.post(path+"/"+tid+"/acknowledge",headers=op).status_code==403
    assert c.post(path+"/"+tid+"/acknowledge",headers=ceo).json()["state"]=="reviewed_demo"
    assert c.post(path+"/tick",headers=op).json()["task"] is None
    assert c.get(path,headers=auditor).json()["worker_running"] is False
    monkeypatch.setattr(routes,"get_settings",lambda:SimpleNamespace(environment="production",database_url="sqlite:///"+str(tmp_path/"tasks.db")))
    assert c.get(path,headers=ceo).status_code==503
