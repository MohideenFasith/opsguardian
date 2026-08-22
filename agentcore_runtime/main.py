"""Amazon Bedrock AgentCore entrypoint for OpsGuardian.

This file is intentionally small and framework-native: AgentCore owns runtime isolation and
observability, while Strands owns model/tool orchestration. Production write actions are not
exposed as model tools; the agent can inspect, trace, and validate, then recommend an action.
"""
from __future__ import annotations

import json
import os

from bedrock_agentcore.runtime import BedrockAgentCoreApp
from strands import Agent, tool
from strands.models import BedrockModel

from opsguardian.tools import dependency_lookup, inspect_incident, sandbox_validate

app = BedrockAgentCoreApp()


@tool
def inspect_pipeline_incident(anomaly_json: str) -> dict:
    """Inspect normalized facts from a pipeline incident."""
    return inspect_incident(json.loads(anomaly_json))


@tool
def trace_pipeline_lineage(dataset: str) -> dict:
    """Trace downstream assets from the approved lineage graph."""
    return dependency_lookup(dataset)


@tool
def validate_repair_in_sandbox(operation: str) -> dict:
    """Run one allowlisted repair operation through executable regression checks."""
    return sandbox_validate(operation)


model = BedrockModel(
    model_id=os.getenv("BEDROCK_MODEL_ID", "global.anthropic.claude-sonnet-4-6"),
    region_name=os.getenv("AWS_REGION", os.getenv("AWS_DEFAULT_REGION", "us-west-2")),
    temperature=0.1,
)

agent = Agent(
    model=model,
    tools=[inspect_pipeline_incident, trace_pipeline_lineage, validate_repair_in_sandbox],
    system_prompt=(
        "You are OpsGuardian, an autonomous incident-response partner for data engineers. "
        "Inspect evidence, trace downstream impact, and validate candidate repairs with tools. "
        "Never claim that a production repair was deployed: this runtime has no production-write tool. "
        "If risk is material, explicitly request a human decision."
    ),
)


def _result_text(result) -> str:
    message = getattr(result, "message", None)
    if isinstance(message, dict):
        text = "".join(
            part.get("text", "") for part in message.get("content", []) if isinstance(part, dict)
        )
        if text.strip():
            return text.strip()
    return str(result).strip()


@app.entrypoint
def invoke(payload):
    if not isinstance(payload, dict):
        raise ValueError("payload must be a JSON object")
    prompt = payload.get("prompt")
    if not isinstance(prompt, str) or not prompt.strip():
        anomaly = payload.get("anomaly")
        if isinstance(anomaly, dict):
            prompt = (
                "Investigate this incident end to end. Use tools. Compare normalize_to_string and "
                "coerce_to_integer, report blast radius, sandbox evidence, risk, and whether human "
                "approval is required. Incident: " + json.dumps(anomaly)
            )
        else:
            raise ValueError("payload must contain a non-empty 'prompt' string or an 'anomaly' object")
    result = agent(prompt)
    return {
        "response": _result_text(result),
        "framework": "Strands Agents SDK",
        "model": os.getenv("BEDROCK_MODEL_ID", "global.anthropic.claude-sonnet-4-6"),
        "available_tools": list(agent.tool_names),
        "safety_boundary": "read/trace/validate only; production writes are policy-gated outside the model",
    }


if __name__ == "__main__":
    app.run()
