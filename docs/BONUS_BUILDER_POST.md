# Agents for Humans: Building OpsGuardian with Strands Agents and Amazon Bedrock

Data-pipeline incidents are a good example of work that is partly repetitive and partly judgment-heavy. The engineer still needs to own consequential production decisions, but they should not have to spend the first part of every incident collecting the same evidence, tracing the same lineage, running the same checks, and writing the same report.

For the **Agents for Humans** hackathon, I built **OpsGuardian**, a Professional Agent that automates that surrounding work with the Strands Agents SDK.

## The design constraint

The easiest agent architecture would expose broad shell or database tools and ask the model to solve everything. I intentionally did the opposite. OpsGuardian separates probabilistic reasoning from deterministic authority.

The Strands agent can inspect normalized incident facts, walk an approved lineage graph, and run an allowlisted sandbox validator. It can diagnose and propose. It cannot create a new execution primitive, declare its own test result valid, or bypass the human approval state.

## The incident

The demo injects a schema change in `customer_id`: INTEGER becomes STRING and one new ID is alphanumeric. That detail matters. Coercing IDs back to integers looks like a simple fix until it destroys a legitimate value.

OpsGuardian traces four affected assets and evaluates two candidate repairs. The integer repair is rejected. String normalization passes 17 executable checks. Because the identity key is business-critical, the state machine requires human approval before the controlled deployment proceeds.

## Why Strands

Strands makes the tool boundary explicit. The reasoning agent uses custom Python tools while Amazon Bedrock supplies the model. The project also includes an Amazon Bedrock AgentCore Runtime entrypoint so the same Strands-native logic can run inside a managed production agent runtime with observability.

## What I learned

The most useful agent is not necessarily the one with the most permissions. For operational work, reliability improves when the model is allowed to reason broadly but act narrowly. The combination of model-driven investigation, executable validators, explicit lifecycle state, and human approval at the material-risk boundary created a much stronger product than a general-purpose “AI SRE” chatbot.

OpsGuardian's goal is straightforward: **automate the toil around judgment, not the judgment itself.**

---

This post was created for my entry in the AWS **Agents for Humans** hackathon. Before publishing, add the public repository/demo links and use any exact hashtag/title requirements shown in the current hackathon rules.
