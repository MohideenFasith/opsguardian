# Validation report

Validated on **2026-08-22** before packaging.

## Passed

- `pytest -q` — **19/19 tests passed**.
- `python scripts/demo_smoke.py` — complete offline incident reached `resolved`, with 9 audited timeline events and 17/17 checks on the selected repair.
- Real FastAPI/uvicorn HTTP run — `/health`, `/`, incident injection, background workflow, and resolved incident retrieval passed.
- Python bytecode compilation — `opsguardian/`, `web.py`, AgentCore entrypoint, and scripts passed.
- JavaScript syntax — `static/app.js` passed `node --check`.
- Shell syntax — deployment/helper scripts passed `bash -n`.
- Public-repository secret scan — no AWS access-key pattern, private-key marker, or secret-access-key assignment found.
- AWS migration scan — no prior Google runtime/framework dependencies or branding remained in the packaged project.
- Mocked AgentCore deployment flow — the deployment script successfully created a current-CLI project skeleton, replaced the generated entrypoint, copied the core package/data, ran dry-run/deploy/status calls, and produced the expected deployable layout.
- MIT license present at repository root.
- Fresh-extract release test — the packaged ZIP was extracted into a new temporary directory; archive hygiene, 19/19 tests, smoke workflow, Python compilation, JavaScript syntax, and shell syntax passed.

## What was not claimed as locally executed

This build environment does not contain authenticated AWS credentials or the live `strands-agents` / `bedrock-agentcore` runtime packages, so a real Amazon Bedrock model call and a real AgentCore cloud deployment were **not** fabricated or marked as passed. The live code follows the current official Strands `Agent` / `@tool` / `BedrockModel` API and AgentCore `BedrockAgentCoreApp` entrypoint pattern; the actual AWS invocation must be run in the submitter's AWS account before recording deployment evidence.

## Release policy

Only the ZIP produced after these checks should be uploaded. Local databases, `.env`, `.venv`, caches, compiled bytecode, temporary AgentCore build directories, and credentials are excluded from the release archive.
