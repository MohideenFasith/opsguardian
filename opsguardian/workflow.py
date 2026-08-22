from __future__ import annotations

import asyncio
import logging
import threading

from .strands_advisor import StrandsAdvisor
from .config import settings
from .models import Incident, IncidentStatus, TimelineEvent
from .storage import Store
from .lineage import trace_downstream
from .validator import validate_repair_candidates, verify_deployed_transform

logger = logging.getLogger(__name__)


def _confidence_percent(value: object, default: float = 0.96) -> int:
    """Convert model confidence to a bounded display percentage without crashing the workflow."""
    try:
        if isinstance(value, str):
            text = value.strip()
            if text.endswith("%"):
                numeric = float(text[:-1]) / 100.0
            else:
                numeric = float(text)
        else:
            numeric = float(value)
    except (TypeError, ValueError):
        numeric = default
    numeric = min(max(numeric, 0.0), 1.0)
    return int(round(numeric * 100))


class IncidentEngine:
    def __init__(self, store: Store, advisor: StrandsAdvisor | None = None) -> None:
        self.store = store
        self.advisor = advisor or StrandsAdvisor()
        # Approval endpoints may run concurrently in FastAPI's threadpool. Keep the
        # read/check/write decision atomic within this demo control process.
        self._approval_lock = threading.Lock()

    async def _pause(self, factor: float = 1.0) -> None:
        await asyncio.sleep(max(settings.demo_delay_ms * factor / 1000.0, 0))

    def _event(
        self,
        incident: Incident,
        stage: str,
        message: str,
        *,
        agent: str = "orchestrator",
        severity: str = "info",
        details: dict | None = None,
    ) -> None:
        incident.timeline.append(
            TimelineEvent(
                stage=stage,
                message=message,
                agent=agent,
                severity=severity,
                details=details or {},
            )
        )
        self.store.upsert(incident)
        logger.info(
            "incident_event incident_id=%s stage=%s agent=%s severity=%s status=%s message=%s",
            incident.id, stage, agent, severity, incident.status.value, message,
        )

    def create_incident(self, source: str = "demo", auto_approve: bool | None = None) -> Incident:
        incident = Incident(
            source=source,
            agent_mode=f"Strands Agents + Amazon Bedrock ({settings.bedrock_model_id})" if settings.ai_enabled else "offline deterministic demo",
            anomaly={
                "dataset": "crm.customer_export",
                "field": "customer_id",
                "expected_type": "INTEGER",
                "observed_type": "STRING",
                "first_bad_version": "crm_export_v42",
                "sample_new_values": ["100482", "C-100483"],
                "auto_approve_requested": auto_approve,
            },
        )
        self._event(
            incident,
            "detect",
            "Schema drift detected: customer_id changed INTEGER → STRING",
            agent="detector",
            severity="warning",
        )
        return incident

    async def run(self, incident_id: str) -> None:
        incident = self.store.get(incident_id)
        if not incident:
            return
        # Event sources may redeliver. Only a freshly detected incident may start a new run.
        if incident.status != IncidentStatus.detected:
            return
        try:
            incident.status = IncidentStatus.investigating
            self._event(incident, "investigate", "Investigation started", agent="strands-investigator")
            await self._pause()

            incident.diagnosis = await self.advisor.diagnose(incident.anomaly)
            self._event(
                incident,
                "diagnose",
                f"Root cause isolated with {_confidence_percent(incident.diagnosis.get('confidence', 0.96))}% confidence",
                agent="strands-investigator",
                details=incident.diagnosis,
            )
            await self._pause()

            incident.blast_radius = trace_downstream(incident.anomaly.get("dataset", "crm.customer_export"))
            self._event(
                incident,
                "blast-radius",
                f"Traced dependency graph: {len(incident.blast_radius)} downstream assets affected",
                agent="lineage-tool",
                details={"assets": incident.blast_radius},
            )
            await self._pause()

            proposed = await self.advisor.propose_fix(
                {"anomaly": incident.anomaly, "diagnosis": incident.diagnosis, "blast_radius": incident.blast_radius}
            )
            validation_results = validate_repair_candidates(proposed)
            incident.candidate_fixes = [result.as_dict() for result in validation_results]
            passing = [result for result in validation_results if result.status == "passed"]
            if not passing:
                raise RuntimeError("No repair candidate passed sandbox validation")
            selected = max(passing, key=lambda item: item.checks_passed)
            incident.selected_fix = selected.as_dict()
            incident.status = IncidentStatus.validating
            summary = "; ".join(
                f"candidate fix #{index} {result.status} "
                f"({result.checks_passed}/{result.checks_total})"
                for index, result in enumerate(validation_results, start=1)
            )
            self._event(
                incident,
                "validate",
                f"Sandbox evaluation complete: {summary}; selected {selected.id}",
                agent="sandbox-validator",
                details={"candidates": incident.candidate_fixes, "selected": selected.id},
            )
            await self._pause()

            incident.risk = {
                "level": "medium",
                "score": 0.58,
                "reasons": [
                    "customer identity key is business-critical",
                    f"change affects {len(incident.blast_radius)} downstream assets",
                    "repair is reversible and fully validated",
                ],
            }
            self._event(
                incident,
                "risk",
                "Risk classified MEDIUM; policy requires human approval",
                agent="policy-engine",
                severity="warning",
                details=incident.risk,
            )

            auto_requested = incident.anomaly.get("auto_approve_requested")
            if auto_requested is True:
                incident.approval = {"approved": True, "actor": "demo-auto-approver", "note": "Demo override"}
            else:
                incident.status = IncidentStatus.awaiting_approval
                self._event(
                    incident,
                    "approval",
                    "Human authorization requested",
                    agent="policy-engine",
                    severity="warning",
                )
                # Poll durable state instead of using an in-memory Event so approval and workflow
                # processing may happen in separate processes or runtime invocations.
                approved_incident = None
                for _ in range(600):  # ~5 minutes at 0.5 s intervals
                    await asyncio.sleep(0.5)
                    current = self.store.get(incident.id)
                    if current and "approved" in current.approval:
                        approved_incident = current
                        break
                if approved_incident is None:
                    incident = self.store.get(incident.id) or incident
                    incident.status = IncidentStatus.failed
                    self._event(
                        incident,
                        "approval",
                        "Approval window expired; no production change applied",
                        severity="error",
                    )
                    return
                incident = approved_incident
                if not incident.approval.get("approved"):
                    incident.status = IncidentStatus.failed
                    self._event(
                        incident,
                        "approval",
                        "Change rejected by human reviewer; incident stopped safely",
                        severity="error",
                    )
                    return

            incident.status = IncidentStatus.deploying
            self._event(
                incident,
                "deploy",
                "Approved repair applied to the controlled pipeline configuration",
                agent="deployment-tool",
                details={"rollback_checkpoint": "pipeline-config-v41"},
            )
            await self._pause(1.2)

            incident.status = IncidentStatus.verifying
            incident.verification = verify_deployed_transform(incident.selected_fix["id"])
            if incident.verification.get("rollback_required"):
                incident.status = IncidentStatus.failed
                self._event(
                    incident,
                    "rollback",
                    "Post-deployment verification failed; rollback required",
                    agent="verification-tool",
                    severity="error",
                    details=incident.verification,
                )
                return
            self._event(
                incident,
                "verify",
                "Pipeline healthy: executable checks, row counts, null rate, join cardinality, and alphanumeric ID preservation passed",
                agent="verification-tool",
                details=incident.verification,
            )
            await self._pause()

            incident.incident_report = await self.advisor.write_report(
                {
                    "diagnosis": incident.diagnosis,
                    "blast_radius": incident.blast_radius,
                    "selected_fix": incident.selected_fix,
                    "risk": incident.risk,
                    "approval": incident.approval,
                    "verification": incident.verification,
                }
            )
            incident.status = IncidentStatus.resolved
            self._event(
                incident,
                "resolved",
                "Incident resolved autonomously with policy-gated human approval",
                agent="orchestrator",
            )
        except Exception as exc:  # fail closed and surface the reason in the audit trail
            incident = self.store.get(incident_id) or incident
            incident.status = IncidentStatus.failed
            self._event(
                incident,
                "failed",
                f"Workflow failed safely: {type(exc).__name__}: {exc}",
                severity="error",
            )

    def approve(self, incident_id: str, approved: bool, actor: str, note: str = "") -> Incident | None:
        with self._approval_lock:
            incident = self.store.get(incident_id)
            if not incident:
                return None
            if incident.status != IncidentStatus.awaiting_approval:
                raise ValueError(f"Incident is not awaiting approval (current status: {incident.status.value})")
            if "approved" in incident.approval:
                raise ValueError("An approval decision has already been recorded")
            incident.approval = {"approved": approved, "actor": actor, "note": note}
            self._event(
                incident,
                "approval",
                "Authorization received" if approved else "Authorization denied",
                agent="human-reviewer",
                severity="info" if approved else "warning",
                details=incident.approval,
            )
            return incident
