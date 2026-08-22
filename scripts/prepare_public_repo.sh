#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

bad=0
for pattern in 'AKIA[0-9A-Z]{16}' 'aws_secret_access_key' 'BEGIN (RSA|OPENSSH|EC) PRIVATE KEY' 'GOOGLE_API_KEY='; do
  if grep -RInE --exclude-dir=.git --exclude-dir=.agentcore-build --exclude='*.png' --exclude='*.zip' --exclude='prepare_public_repo.sh' "$pattern" .; then
    bad=1
  fi
done
if [[ "$bad" -ne 0 ]]; then
  echo "Potential secret-like content found. Review before publishing." >&2
  exit 1
fi

pytest -q
python scripts/demo_smoke.py
python -m compileall -q opsguardian web.py agentcore_runtime/main.py

echo "Public-repo checks passed."
echo "Next: git init && git add . && git commit -m 'Initial OpsGuardian hackathon submission'"
