import time

from fastapi.testclient import TestClient

import web

client = TestClient(web.app)


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body["service"] == "opsguardian"
    assert body["framework"] == "Strands Agents SDK"


def test_ui_loads_and_is_aws_native():
    r = client.get("/")
    assert r.status_code == 200
    assert "OpsGuardian" in r.text
    assert "Strands Agents" in r.text
    assert "AgentCore" in r.text


def test_demo_api_end_to_end(monkeypatch):
    monkeypatch.setattr(web.settings, "demo_delay_ms", 0)
    monkeypatch.setattr(web.settings, "strands_mode", "offline")
    with TestClient(web.app) as live_client:
        live_client.post("/api/demo/reset")
        start = live_client.post("/api/demo/inject", json={"scenario": "schema_drift"})
        assert start.status_code == 200
        incident_id = start.json()["incident_id"]
        current = None
        for _ in range(150):
            current = live_client.get(f"/api/incidents/{incident_id}").json()
            if current["status"] == "awaiting_approval":
                break
            time.sleep(0.01)
        assert current["status"] == "awaiting_approval"
        approved = live_client.post(
            f"/api/incidents/{incident_id}/approval",
            json={"approved": True, "actor": "api-test"},
        )
        assert approved.status_code == 200
        for _ in range(150):
            current = live_client.get(f"/api/incidents/{incident_id}").json()
            if current["status"] == "resolved":
                break
            time.sleep(0.01)
        assert current["status"] == "resolved"
        assert current["verification"]["pipeline_run"] == "success"


def test_approval_rejected_outside_gate(monkeypatch):
    monkeypatch.setattr(web.settings, "strands_mode", "offline")
    with TestClient(web.app) as live_client:
        live_client.post("/api/demo/reset")
        incident = web.engine.create_incident(auto_approve=True)
        r = live_client.post(
            f"/api/incidents/{incident.id}/approval",
            json={"approved": True, "actor": "api-test"},
        )
        assert r.status_code == 409


def test_reset_cancels_background_work(monkeypatch):
    monkeypatch.setattr(web.settings, "demo_delay_ms", 100)
    monkeypatch.setattr(web.settings, "strands_mode", "offline")
    with TestClient(web.app) as live_client:
        live_client.post("/api/demo/reset")
        started = live_client.post("/api/demo/inject", json={"scenario": "schema_drift"})
        assert started.status_code == 200
        assert live_client.post("/api/demo/reset").status_code == 200
        time.sleep(0.2)
        assert live_client.get("/api/incidents").json() == []


def test_public_api_cannot_bypass_human_approval(monkeypatch):
    monkeypatch.setattr(web.settings, "strands_mode", "offline")
    with TestClient(web.app) as live_client:
        live_client.post("/api/demo/reset")
        r = live_client.post(
            "/api/demo/inject",
            json={"scenario": "schema_drift", "auto_approve": True},
        )
        assert r.status_code == 422
        assert live_client.get("/api/incidents").json() == []


def test_invalid_scenario_is_rejected_before_work_starts(monkeypatch):
    monkeypatch.setattr(web.settings, "strands_mode", "offline")
    with TestClient(web.app) as live_client:
        live_client.post("/api/demo/reset")
        r = live_client.post("/api/demo/inject", json={"scenario": "arbitrary_shell"})
        assert r.status_code == 422
        assert live_client.get("/api/incidents").json() == []


def test_blank_approval_actor_is_rejected():
    r = client.post(
        "/api/incidents/does-not-matter/approval",
        json={"approved": True, "actor": "   "},
    )
    assert r.status_code == 422
