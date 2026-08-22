#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
pytest -q
python scripts/demo_smoke.py
python -m compileall -q opsguardian web.py agentcore_runtime/main.py scripts
node --check static/app.js
bash -n scripts/*.sh
./scripts/prepare_public_repo.sh
if grep -RInE 'DataOps Autopilot|google-adk|google-cloud-firestore|google-cloud-pubsub|Gemini 3\.5|All Things Agentic' \
  --exclude-dir=.git --exclude-dir=.pytest_cache --exclude-dir=__pycache__ --exclude='*.png' --exclude='*.svg' --exclude='validate_release.sh' .; then
  echo "Stale project/runtime reference found." >&2
  exit 1
fi
echo "RELEASE VALIDATION PASS"
