# Demo video script — target 4:20 to 4:45

The Devpost limit is five minutes. Keep the recording focused on real execution; do not spend half the video on slides.

## 0:00–0:30 — Problem, user, why it matters

**Voiceover:**

“Data engineers lose on-call time to repetitive incident work: opening logs, tracing dependencies, comparing fixes, running validation, waiting for recovery, and then writing the report. OpsGuardian is a Professional Agent built with the Strands Agents SDK. It handles that toil autonomously and interrupts the engineer only when a real judgment call is required.”

Show the OpsGuardian dashboard with no active incident.

## 0:30–0:55 — Architecture proof

Briefly show `infra/architecture.png`, then `opsguardian/strands_advisor.py` and `agentcore_runtime/main.py`.

**Voiceover:**

“The reasoning layer is a real Strands agent on Amazon Bedrock with bounded tools for evidence, lineage, and sandbox validation. Deterministic code owns policy, approval, and verification. The same Strands agent has an AgentCore Runtime entrypoint for production deployment and observability.”

Do not scroll through code for long.

## 0:55–2:55 — Live working demo

Return to the dashboard. Click **Inject schema drift** once, then stop interacting.

Narrate only what appears:

“The upstream CRM changed `customer_id` from integer to string. OpsGuardian wakes up, isolates the root cause, and walks the lineage graph. Four downstream assets are affected.”

When validation appears:

“Now it compares repairs. Integer coercion fails because the new export contains an alphanumeric ID. The string-normalization repair passes all 17 executable checks. Those scores come from code, not from the model grading itself.”

At the approval state:

“This is the only point where OpsGuardian interrupts me. The repair is validated and reversible, but the customer identity key is business-critical, so policy classifies the change as medium risk.”

Click **Approve repair**.

“As soon as I approve, the workflow continues without another prompt.”

Let verification and the report finish.

## 2:55–3:35 — Safety / engineering depth

Show the timeline, then briefly open a test or validator file.

**Voiceover:**

“The agent cannot invent a new execution primitive. Repairs are allowlisted, unsupported operations fail closed, approval only works in the correct lifecycle state, and verification re-executes the selected transform after the simulated deployment. The repository includes a full offline regression suite so judges can reproduce the behavior without AWS credentials.”

## 3:35–4:10 — AgentCore proof

Show either the real AgentCore console/status/logs from your deployed build or terminal output from `agentcore status` and a real `agentcore invoke`. Do not fake this section.

**Voiceover:**

“For the production path, the Strands entrypoint runs on Amazon Bedrock AgentCore. AgentCore provides managed runtime isolation and observability while Strands remains responsible for the agent and tool loop.”

## 4:10–4:35 — Close

Return to the resolved incident/report.

**Voiceover:**

“OpsGuardian doesn’t try to remove human judgment. It removes everything around the judgment: investigation, impact analysis, repair comparison, testing, verification, and documentation. The engineer gets their time back without handing an LLM unrestricted production authority.”

End on the project name and public repository URL.
