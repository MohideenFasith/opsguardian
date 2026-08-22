# Contributing

OpsGuardian is a hackathon reference build. Keep changes small, testable, and policy-safe.

1. Create a branch.
2. Add or update tests for behavior changes.
3. Run `pytest -q` and `python scripts/demo_smoke.py`.
4. Never commit `.env`, AWS credentials, access keys, session tokens, account IDs, or production customer data.
5. Do not add arbitrary shell/database execution as an LLM tool. New action tools must be narrowly scoped and have explicit validation and authorization boundaries.
