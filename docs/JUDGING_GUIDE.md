# Judge verification guide

## Technological Implementation

- `opsguardian/strands_advisor.py` — live Strands `Agent`, `@tool`, `BedrockModel`, role-specific prompts.
- `agentcore_runtime/main.py` — `BedrockAgentCoreApp` + Strands-native AgentCore entrypoint.
- `scripts/deploy_agentcore.sh` — current CLI-generated AgentCore project, dry run, deploy, status.
- `opsguardian/validator.py` — 17 executable checks; no model self-scoring.
- `opsguardian/lineage.py` — actual graph traversal.
- `tests/` — offline reproducibility and safety regression coverage.

## Design

Open the web console, click **Inject schema drift**, and watch the timeline progress without additional prompts. The UI surfaces only the real human decision point.

## Potential Impact

The target user is a data engineer/on-call engineer. OpsGuardian automates repetitive triage, impact analysis, repair comparison, validation, verification, and incident documentation while leaving material risk decisions to the human.

## Creativity & Originality

The differentiator is the authority split: the model reasons, but deterministic tools prove. Instead of making an LLM a production superuser, the system treats the LLM as a bounded investigator/planner within an explicit incident state machine.

## Presentation

The bundled demo creates an observable failure with an unsafe obvious fix. The judge can see the agent reject that repair, request approval, recover the pipeline, and create the final report in under five minutes.
