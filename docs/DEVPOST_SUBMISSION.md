# Devpost submission copy

## Project name

**OpsGuardian — Autonomous Incident Response with Strands Agents**

## Track

**Professional Agents**

## What it does

OpsGuardian is an autonomous on-call partner for data engineers. When a data pipeline breaks, it performs the repetitive incident work before interrupting a human: it inspects the failure, traces downstream impact, proposes constrained repairs, executes sandbox regression checks, classifies risk, requests a decision only when policy requires one, verifies recovery, and writes the post-incident report.

The demo starts with a realistic schema-drift event: an upstream CRM changes `customer_id` from INTEGER to STRING and introduces an alphanumeric ID. A naive integer-coercion repair looks convenient but would corrupt the new identifier. OpsGuardian tests candidate repairs against 17 executable invariants, rejects the lossy option, selects the reversible string-normalization repair, and stops at a human approval gate because the identity key is business-critical. After approval it applies the controlled repair, independently verifies pipeline health, and closes the incident with an evidence-backed report.

## Who it is for

Data engineers, analytics engineers, platform teams, and small technical teams that lose on-call time to repetitive pipeline triage and remediation steps.

## Why it matters

Many operational incidents require judgment, but much of the work around that judgment is mechanical: gathering evidence, tracing dependencies, comparing safe fixes, running checks, documenting actions, and confirming recovery. OpsGuardian automates that toil while preserving the human decision where risk is material.

## How we used Strands Agents

Live mode uses the open-source **Strands Agents SDK** with Amazon Bedrock. The Strands agent has custom tools for normalized incident inspection, dependency-graph traversal, and executable sandbox validation. The model is not allowed to self-certify a repair or bypass policy. Deterministic code owns the incident state machine, allowlist, approval gate, and post-deployment verification.

The repository also includes a native **Amazon Bedrock AgentCore Runtime** entrypoint using `BedrockAgentCoreApp`. The AgentCore runtime exposes only read/trace/validate tools to the Strands agent, keeping production-write authority outside the model boundary. The provided deployment script uses the current AgentCore CLI to generate its configuration, preview the deployment, deploy, and show runtime status.

## Technologies used

Python, Strands Agents SDK, Amazon Bedrock, Amazon Bedrock AgentCore Runtime, FastAPI, Pydantic, SQLite, optional Amazon DynamoDB, OpenTelemetry/CloudWatch observability, Docker, pytest, HTML/CSS/JavaScript.

## Architecture

See `infra/architecture.png` and `docs/ARCHITECTURE.md`.

## Reproducibility

The default offline mode requires no cloud credentials and runs the same workflow, graph traversal, sandbox validator, risk policy, approval logic, and verification path. `pytest -q` runs the regression suite and `python scripts/demo_smoke.py` runs the complete auto-approved incident flow. Live Strands mode is enabled with `STRANDS_MODE=bedrock` and normal AWS credentials/model access.

## Source repository

`PASTE_PUBLIC_REPOSITORY_URL_HERE`

## Demo video

`PASTE_PUBLIC_YOUTUBE_OR_VIMEO_URL_HERE`

## AWS Builder ID

`ADD_IN_DEVPOST_FORM`

## Optional live demo / AgentCore evidence

`PASTE_LIVE_DEMO_OR_AGENTCORE_EVIDENCE_HERE_IF_AVAILABLE`
