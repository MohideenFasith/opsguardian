# OpsGuardian

**Autonomous incident response for data engineers — built with the Strands Agents SDK for AWS Agents for Humans.**

OpsGuardian removes the repetitive first 20–40 minutes of data-pipeline incident response. When a pipeline breaks, it investigates the event, traces downstream impact, proposes constrained repairs, executes sandbox regression checks, applies a risk policy, interrupts a human only when judgment is required, verifies recovery, and writes the post-incident report.

> Track: **Professional Agents**  
> Framework: **Strands Agents SDK**  
> Model provider: **Amazon Bedrock**  
> Production runtime: **Amazon Bedrock AgentCore compatible**  
> License: **MIT**

![OpsGuardian architecture](infra/architecture.png)

## Why this is an agent, not a chatbot

A chat UI would still leave the engineer doing the work. OpsGuardian owns a workflow:

1. Detect a controlled schema-drift incident.
2. Normalize the evidence available to the model.
3. Use a Strands investigator to reason over the failure.
4. Walk the actual dependency graph to calculate blast radius.
5. Generate a constrained repair proposal.
6. Execute two candidate transforms against 17 regression checks.
7. Reject the lossy repair.
8. Classify production risk outside the model.
9. Stop for a human decision only when policy requires it.
10. Apply the approved repair to the controlled demo pipeline.
11. Re-run verification checks.
12. Write an evidence-backed incident report.

The LLM is deliberately **not** trusted to declare its own repair safe. Validation, policy, approval state, and deployment boundaries are deterministic code.

## Strands implementation

Live mode uses `strands.Agent`, `strands.tool`, and `strands.models.BedrockModel`. The agent can call three bounded tools:

- `inspect_pipeline_event` — exposes normalized incident evidence.
- `trace_downstream_dependencies` — executes a breadth-first lineage graph walk.
- `run_sandbox_validation` — executes an allowlisted repair operation against real regression checks.

The AgentCore runtime entrypoint is in [`agentcore_runtime/main.py`](agentcore_runtime/main.py). It exposes **read / trace / validate** tools only; it has no arbitrary production-write tool.

## Repository layout

```text
opsguardian-strands/
├── opsguardian/                 # core workflow, Strands layer, validation, storage
├── agentcore_runtime/           # Bedrock AgentCore + Strands entrypoint
├── static/                      # judge-facing operations console
├── sample_data/                 # deterministic incident, rows, and lineage graph
├── tests/                       # 31 regression/contract tests
├── scripts/                     # smoke test, AgentCore deploy, DynamoDB helper
├── infra/                       # architecture diagrams
├── docs/                        # Devpost copy, demo script, judging/security docs
├── web.py                       # FastAPI demo UI/API
├── requirements.txt
├── Dockerfile
└── LICENSE                      # MIT
```

## Run locally — no AWS credentials required

Python 3.12+ is recommended (Python 3.13 is used by the container and recommended for AgentCore direct-code deployment).

```bash
python -m venv .venv
source .venv/bin/activate       # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
cp .env.example .env
pytest
uvicorn web:app --reload --port 8080
```

Open `http://localhost:8080` and click **Inject schema drift**. The default `STRANDS_MODE=offline` keeps the workflow reproducible for judges without AWS credentials while exercising the exact same deterministic lineage, policy, validation, approval, and verification code.

For a one-command workflow check:

```bash
python scripts/demo_smoke.py
```

Expected result:

```text
SMOKE PASS ... status=resolved events=9
```

## Run with live Strands + Amazon Bedrock

Configure normal AWS credentials locally, then enable live mode:

```bash
export AWS_REGION=us-west-2
export STRANDS_MODE=bedrock
export BEDROCK_MODEL_ID=global.anthropic.claude-sonnet-4-6
uvicorn web:app --port 8080
```

Your AWS account must have access to the selected Bedrock model. No AWS key or secret belongs in this repository.

## Deploy the Strands agent to Amazon Bedrock AgentCore

Prerequisites:

- AWS CLI authenticated to the AWS account you want to use.
- Node.js 20+.
- `uv` installed (required for Python CodeZip dependency resolution).
- Permissions to deploy AgentCore resources and invoke the Bedrock model.
- The official AgentCore CLI (`@aws/agentcore`). The script installs it if missing.

Run:

```bash
./scripts/deploy_agentcore.sh
```

On the first run, the script lets the **current AgentCore CLI generate its own `agentcore.json` schema**. It then copies this repository's tested Strands entrypoint into that generated project, refreshes the `uv` dependency lock, runs `agentcore validate` and `agentcore deploy --dry-run`, deploys with confirmation disabled for reproducibility, and prints `agentcore status`. Later runs reuse the generated project so deployment state is preserved. This avoids checking in a stale hand-written AgentCore configuration while keeping updates idempotent.

To exercise the AgentCore-compatible runtime locally with real Bedrock credentials, run `./scripts/agentcore_local.sh`.

After deployment, invoke it using the command printed by the script, or from the generated directory:

```bash
agentcore invoke --prompt "Investigate the bundled schema drift and validate the safest repair."
```

AgentCore Runtime adds production isolation and CloudWatch/OpenTelemetry observability to the Strands agent.

## Optional durable incident state

Local mode uses SQLite. For an AWS-hosted web UI, create an on-demand DynamoDB table:

```bash
export AWS_REGION=us-west-2
./scripts/create_dynamodb_table.sh
export USE_DYNAMODB=true
export DYNAMODB_TABLE=opsguardian-incidents
```

The table uses `incident_id` as its partition key. This is optional for the hackathon's AgentCore runtime deployment.

## Controlled demo scenario

The bundled failure is intentionally realistic and deterministic:

```text
crm.customer_export.customer_id
INTEGER  →  STRING
```

The new export contains both `"100482"` and `"C-100483"`. A naive integer coercion therefore destroys a valid identifier and is rejected. Normalizing IDs to strings preserves both old numeric identifiers and new alphanumeric identifiers.

The dependency graph is executable, not hard-coded presentation text:

```text
crm.customer_export
  → stg_customer_normalized
    → fct_orders_customer_join
      → customer_ltv_features
        → executive_customer_dashboard
```

## Safety design

OpsGuardian has four explicit boundaries:

- **Evidence boundary:** the model receives normalized facts, not secrets.
- **Tool boundary:** the Strands tools are specific functions, not unrestricted shell/database access.
- **Validation boundary:** only allowlisted transforms are executable; unknown operations fail closed.
- **Approval boundary:** medium-risk production changes cannot bypass the `awaiting_approval` lifecycle state.

See [`docs/SECURITY.md`](docs/SECURITY.md) for details.

## Tests

```bash
pytest -q
```

The suite covers the dependency graph, 17-check sandbox evaluator, unsafe-operation rejection, post-deploy verification, approval gating, human rejection, API workflow, reset races, Strands source contract, AgentCore entrypoint, deployment-script contract, AWS-native dependencies, and MIT license.

## Hackathon submission assets

- [`docs/DEVPOST_SUBMISSION.md`](docs/DEVPOST_SUBMISSION.md) — ready-to-paste project description.
- [`docs/DEMO_SCRIPT.md`](docs/DEMO_SCRIPT.md) — ≤5-minute demo/pitch script.
- [`docs/JUDGING_GUIDE.md`](docs/JUDGING_GUIDE.md) — where judges can verify each claim.
- [`docs/UPLOAD_CHECKLIST.md`](docs/UPLOAD_CHECKLIST.md) — final Devpost checklist.
- [`docs/BONUS_BUILDER_POST.md`](docs/BONUS_BUILDER_POST.md) — optional builder.aws.com article draft.
- [`docs/HIGGSFIELD_MEDIA_PLAN.md`](docs/HIGGSFIELD_MEDIA_PLAN.md) — optional cover/intro media plan; generated media is never used as proof that the backend works.

## What still requires the submitter's account

A repository can be upload-ready without pretending account-specific URLs already exist. Before final Devpost submission you must add:

1. the **public GitHub/GitLab/Bitbucket URL**,
2. your **AWS Builder ID**,
3. the **public YouTube/Vimeo demo video URL**,
4. optionally a live demo URL and AgentCore deployment evidence.

## License

MIT. When you publish the repo on GitHub, also select **MIT License** in the repository's About/license metadata so the license is obvious to judges.
