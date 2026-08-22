# Architecture

OpsGuardian separates probabilistic reasoning from deterministic authority.

## Components

**Web console / event source** starts the incident and shows the audit timeline. The console is not the agent; it is the observation and approval surface.

**Incident Engine** is a deterministic state machine. It decides which stage runs next, persists every transition, enforces approval state, and fails closed.

**Strands reasoning layer** uses Amazon Bedrock through `BedrockModel`. The investigator and repair-planner prompts receive narrowly scoped custom tools. The model can inspect normalized facts, trace lineage, and ask the sandbox validator to evaluate an allowlisted operation.

**Lineage tool** performs a real breadth-first traversal over `sample_data/lineage.json`.

**Sandbox validator** executes proposed transforms against bundled rows and 17 invariants. It rejects the lossy integer coercion because an alphanumeric customer ID would be destroyed.

**Policy engine** is ordinary code, not a prompt. Medium-risk changes transition to `awaiting_approval`; only then can an approval decision be recorded.

**Verification tool** independently re-executes the selected transform and checks pipeline health after the simulated deployment.

**AgentCore Runtime** hosts a Strands-native entrypoint for production evaluation. AgentCore provides runtime isolation and observability while leaving tool orchestration in Strands.

**DynamoDB (optional)** provides durable web-demo state. SQLite is the local default.

## Trust boundary

```text
LLM reasoning  ── proposes / explains ──┐
                                       ▼
Deterministic code ─ lineage ─ validation ─ policy ─ approval ─ verification
                                       │
                                       └── only validated, authorized actions continue
```

The model cannot invent a passing test, bypass the approval state, or call an arbitrary production-write tool.
