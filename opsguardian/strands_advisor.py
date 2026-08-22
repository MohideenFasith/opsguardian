from __future__ import annotations

import asyncio
import json
from typing import Any

from .config import settings
from .tools import dependency_lookup, inspect_incident, sandbox_validate


class StrandsAdvisor:
    """LLM reasoning layer backed by the open-source Strands Agents SDK.

    The deterministic workflow remains the authority for validation and policy. The model
    diagnoses, proposes, and summarizes; it cannot bypass the allowlisted repair engine.
    """

    def _build_agent(self, role: str, *, include_sandbox: bool = False):
        try:
            from strands import Agent, tool
            from strands.models import BedrockModel
        except ImportError as exc:
            raise RuntimeError(
                "Live Strands mode requires `pip install strands-agents`. "
                "Use STRANDS_MODE=offline for the credential-free demo."
            ) from exc

        @tool
        def inspect_pipeline_event(anomaly_json: str) -> dict:
            """Inspect normalized, non-secret facts from one pipeline incident."""
            return inspect_incident(json.loads(anomaly_json))

        @tool
        def trace_downstream_dependencies(dataset: str) -> dict:
            """Trace downstream assets from the bundled pipeline lineage graph."""
            return dependency_lookup(dataset)

        tools: list[Any] = [inspect_pipeline_event, trace_downstream_dependencies]
        if include_sandbox:
            @tool
            def run_sandbox_validation(operation: str) -> dict:
                """Execute the candidate repair against the bundled regression checks."""
                return sandbox_validate(operation)
            tools.append(run_sandbox_validation)

        model = BedrockModel(
            model_id=settings.bedrock_model_id,
            region_name=settings.aws_region,
            temperature=0.1,
        )
        return Agent(
            model=model,
            tools=tools,
            system_prompt=(
                f"You are OpsGuardian's {role}. Be evidence-driven and conservative. "
                "Never claim an action succeeded unless a tool result proves it. "
                "Production policy and deployment are enforced outside the model."
            ),
        )

    @staticmethod
    def _text(result: Any) -> str:
        message = getattr(result, "message", None)
        if isinstance(message, dict):
            parts = message.get("content", [])
            text = "".join(part.get("text", "") for part in parts if isinstance(part, dict))
            if text.strip():
                return text.strip()
        return str(result).strip()

    async def diagnose(self, anomaly: dict) -> dict:
        if not settings.ai_enabled:
            return {
                "root_cause": "Upstream CRM changed customer_id from INTEGER to STRING",
                "confidence": 0.96,
                "evidence": [
                    "ingest schema mismatch on customer_id",
                    "failure begins immediately after crm_export_v42",
                    "downstream joins expect numeric identity keys",
                ],
                "agent_note": "Offline deterministic mode; set STRANDS_MODE=bedrock for live Strands + Bedrock.",
            }
        agent = self._build_agent("investigator")
        prompt = (
            "Diagnose this pipeline incident. Use the tools before concluding. Return JSON only with "
            "root_cause, confidence (0-1), and evidence (array). Incident: " + json.dumps(anomaly)
        )
        result = await asyncio.to_thread(agent, prompt)
        return _json_or_text(self._text(result), "root_cause")

    async def propose_fix(self, context: dict) -> dict:
        if not settings.ai_enabled:
            return {
                "operation": "normalize_to_string",
                "summary": "Normalize customer_id to STRING at the ingestion boundary and cast legacy numeric IDs safely.",
                "patch": "CAST(customer_id AS STRING) AS customer_id",
                "why": "Preserves new alphanumeric IDs and remains backward-compatible with historic numeric IDs.",
            }
        agent = self._build_agent("repair planner", include_sandbox=True)
        prompt = (
            "Choose the smallest reversible repair. You may only choose normalize_to_string or "
            "coerce_to_integer. Call run_sandbox_validation before choosing. Return JSON only with "
            "operation, summary, patch, and why. Context: " + json.dumps(context)
        )
        result = await asyncio.to_thread(agent, prompt)
        return _json_or_text(self._text(result), "summary")

    async def write_report(self, context: dict) -> str:
        if not settings.ai_enabled:
            assets = len(context.get("blast_radius", []))
            selected = context.get("selected_fix") or {}
            checks = selected.get("checks_total", 0)
            return (
                "Resolved schema drift in customer_360_daily. The upstream CRM changed customer_id "
                f"from INTEGER to STRING. OpsGuardian traced {assets} impacted assets, validated a reversible "
                f"boundary-normalization repair against {checks} executable checks, required human approval for "
                "the medium-risk change, deployed it, and verified pipeline health without rollback."
            )
        agent = self._build_agent("incident reporter")
        prompt = (
            "Write a concise factual post-incident report. Do not invent facts or hidden actions. Context: "
            + json.dumps(context)
        )
        result = await asyncio.to_thread(agent, prompt)
        return self._text(result)


def _json_or_text(text: str, key: str) -> dict:
    cleaned = text.strip().removeprefix("```json").removesuffix("```").strip()
    try:
        parsed = json.loads(cleaned)
        if isinstance(parsed, dict):
            return parsed
    except json.JSONDecodeError:
        pass
    return {key: text, "raw": text}
