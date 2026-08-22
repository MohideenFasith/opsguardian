from __future__ import annotations

import asyncio
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from opsguardian.config import settings
from opsguardian.models import ApprovalRequest, InjectIncidentRequest
from opsguardian.storage import build_store
from opsguardian.workflow import IncidentEngine

store = build_store()
engine = IncidentEngine(store)
background_tasks: set[asyncio.Task] = set()

app = FastAPI(
    title="OpsGuardian",
    version="1.0.0",
    description="Professional incident-response agent built with Strands Agents SDK and Amazon Bedrock.",
)

static_dir = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=static_dir), name="static")


@app.get("/", include_in_schema=False)
def ui():
    return FileResponse(static_dir / "index.html")


@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "opsguardian",
        "framework": "Strands Agents SDK",
        "model": settings.bedrock_model_id,
        "agent_mode": settings.strands_mode,
        "persistence": "dynamodb" if settings.use_dynamodb else "sqlite",
        "deployment_env": settings.deployment_env,
    }


@app.get("/api/incidents")
def list_incidents():
    return [item.model_dump(mode="json") for item in store.list()]


@app.get("/api/incidents/{incident_id}")
def get_incident(incident_id: str):
    incident = store.get(incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    return incident.model_dump(mode="json")


@app.post("/api/demo/inject")
async def inject_demo(req: InjectIncidentRequest):
    incident = engine.create_incident(source="demo-ui")
    task = asyncio.create_task(engine.run(incident.id))
    background_tasks.add(task)
    task.add_done_callback(background_tasks.discard)
    return {"incident_id": incident.id, "status": incident.status, "queued": True}


@app.post("/api/incidents/{incident_id}/approval")
def approve(incident_id: str, req: ApprovalRequest):
    try:
        incident = engine.approve(incident_id, req.approved, req.actor, req.note)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    return incident.model_dump(mode="json")


@app.post("/api/demo/reset")
async def reset_demo():
    tasks = list(background_tasks)
    for task in tasks:
        task.cancel()
    if tasks:
        await asyncio.gather(*tasks, return_exceptions=True)
    background_tasks.clear()
    store.clear()
    return {"status": "reset"}
