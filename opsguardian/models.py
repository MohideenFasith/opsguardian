from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field


def utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


class IncidentStatus(str, Enum):
    detected = "detected"
    investigating = "investigating"
    validating = "validating"
    awaiting_approval = "awaiting_approval"
    deploying = "deploying"
    verifying = "verifying"
    resolved = "resolved"
    failed = "failed"


class TimelineEvent(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    timestamp: str = Field(default_factory=utcnow)
    stage: str
    message: str
    agent: str = "orchestrator"
    severity: str = "info"
    details: dict[str, Any] = Field(default_factory=dict)


class Incident(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    title: str = "Schema drift in customer ingestion"
    status: IncidentStatus = IncidentStatus.detected
    created_at: str = Field(default_factory=utcnow)
    updated_at: str = Field(default_factory=utcnow)
    source: str = "demo"
    pipeline: str = "customer_360_daily"
    anomaly: dict[str, Any] = Field(default_factory=dict)
    diagnosis: dict[str, Any] = Field(default_factory=dict)
    blast_radius: list[str] = Field(default_factory=list)
    candidate_fixes: list[dict[str, Any]] = Field(default_factory=list)
    selected_fix: dict[str, Any] | None = None
    risk: dict[str, Any] = Field(default_factory=dict)
    approval: dict[str, Any] = Field(default_factory=dict)
    verification: dict[str, Any] = Field(default_factory=dict)
    incident_report: str = ""
    agent_mode: str = "offline"
    timeline: list[TimelineEvent] = Field(default_factory=list)


class InjectIncidentRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    scenario: Literal["schema_drift"] = "schema_drift"


class ApprovalRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    approved: bool
    actor: str = Field(default="demo-user", min_length=1, max_length=120)
    note: str = Field(default="", max_length=500)
