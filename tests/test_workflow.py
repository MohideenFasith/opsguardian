import asyncio
from pathlib import Path

from opsguardian.storage import SQLiteStore
from opsguardian.strands_advisor import StrandsAdvisor
from opsguardian.workflow import IncidentEngine


def test_offline_workflow_resolves(tmp_path: Path, monkeypatch):
    monkeypatch.setattr("opsguardian.workflow.settings.demo_delay_ms", 0)
    monkeypatch.setattr("opsguardian.strands_advisor.settings.strands_mode", "offline")
    store = SQLiteStore(str(tmp_path / "test.db"))
    engine = IncidentEngine(store, StrandsAdvisor())
    incident = engine.create_incident(auto_approve=True)
    asyncio.run(engine.run(incident.id))
    final = store.get(incident.id)
    assert final is not None
    assert final.status.value == "resolved"
    assert final.diagnosis["confidence"] == 0.96
    assert len(final.blast_radius) == 4
    assert final.selected_fix["checks_passed"] == 17
    assert final.verification["pipeline_run"] == "success"
    assert any(e.agent == "strands-investigator" for e in final.timeline)


def test_rejected_change_fails_closed(tmp_path: Path, monkeypatch):
    async def scenario():
        monkeypatch.setattr("opsguardian.workflow.settings.demo_delay_ms", 0)
        monkeypatch.setattr("opsguardian.strands_advisor.settings.strands_mode", "offline")
        store = SQLiteStore(str(tmp_path / "reject.db"))
        engine = IncidentEngine(store, StrandsAdvisor())
        incident = engine.create_incident(auto_approve=False)
        task = asyncio.create_task(engine.run(incident.id))
        for _ in range(100):
            await asyncio.sleep(0.01)
            current = store.get(incident.id)
            if current and current.status.value == "awaiting_approval":
                engine.approve(incident.id, False, "tester", "unsafe")
                break
        await task
        final = store.get(incident.id)
        assert final.status.value == "failed"
        assert final.approval["approved"] is False
        assert not final.verification
    asyncio.run(scenario())


def test_approval_cannot_bypass_policy_gate(tmp_path: Path):
    store = SQLiteStore(str(tmp_path / "gate.db"))
    engine = IncidentEngine(store, StrandsAdvisor())
    incident = engine.create_incident(auto_approve=True)
    try:
        engine.approve(incident.id, True, "tester")
        raised = False
    except ValueError:
        raised = True
    assert raised


def test_model_confidence_format_does_not_crash_timeline():
    from opsguardian.workflow import _confidence_percent

    assert _confidence_percent("96%") == 96
    assert _confidence_percent("0.91") == 91
    assert _confidence_percent("n/a") == 96
    assert _confidence_percent(5) == 100
    assert _confidence_percent(-1) == 0


def test_concurrent_approval_decisions_cannot_overwrite_each_other(tmp_path: Path, monkeypatch):
    import threading

    monkeypatch.setattr("opsguardian.workflow.settings.demo_delay_ms", 0)
    store = SQLiteStore(str(tmp_path / "approval-race.db"))
    engine = IncidentEngine(store, StrandsAdvisor())
    incident = engine.create_incident(auto_approve=False)
    current = store.get(incident.id)
    current.status = __import__("opsguardian.models", fromlist=["IncidentStatus"]).IncidentStatus.awaiting_approval
    store.upsert(current)

    results = []

    def decide(value):
        try:
            engine.approve(incident.id, value, f"reviewer-{value}")
            results.append("accepted")
        except ValueError:
            results.append("rejected")

    a = threading.Thread(target=decide, args=(True,))
    b = threading.Thread(target=decide, args=(False,))
    a.start(); b.start(); a.join(); b.join()

    assert sorted(results) == ["accepted", "rejected"]
    final = store.get(incident.id)
    approval_events = [e for e in final.timeline if e.agent == "human-reviewer"]
    assert len(approval_events) == 1
