# Security and governance

OpsGuardian is deliberately restrictive because incident-response agents operate close to production systems.

## Least authority for the model

The AgentCore Strands runtime exposes exactly three model tools: incident-fact inspection, lineage traversal, and sandbox validation. There is no shell tool, no generic SQL executor, and no production-deploy function available to the LLM.

## Allowlisted remediation

The validator recognizes only known transforms. An operation such as `execute_arbitrary_sql` is rejected. This makes prompt injection or model improvisation insufficient to create a new execution primitive.

## Human approval

An approval decision is accepted only while the incident is in `awaiting_approval`. Approval before the gate, repeated approval, or approval after resolution returns an error. Human rejection terminates the incident without verification/deployment. Concurrent decisions are serialized inside the demo control process so the first valid decision wins.

The bundled FastAPI approval UI is a **local/demo control surface**, not a production identity system. Do not expose it as a real production approval endpoint without organization-specific authentication and authorization. The AgentCore runtime itself deliberately has no production-write tool.

## Credentials

AWS credentials use the normal AWS credential/provider chain or AgentCore execution role. The repository contains no access keys. `.env`, local databases, virtual environments, and AgentCore build output are gitignored.

## Observability

All workflow transitions are structured timeline events. AgentCore deployment adds AWS runtime and OpenTelemetry/CloudWatch visibility for live Strands invocations.

## Demo-data boundary

The repository ships only synthetic pipeline rows and a synthetic lineage graph. Do not point the demo at production data without implementing organization-specific authentication, authorization, secrets management, change control, and rollback integration.
