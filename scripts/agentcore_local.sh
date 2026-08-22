#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if ! python -c 'import bedrock_agentcore, strands' >/dev/null 2>&1; then
  echo "Install dependencies first: pip install -r requirements.txt" >&2
  exit 1
fi

: "${AWS_REGION:=${AWS_DEFAULT_REGION:-us-west-2}}"
export AWS_REGION
export BEDROCK_MODEL_ID="${BEDROCK_MODEL_ID:-global.anthropic.claude-sonnet-4-6}"

echo "Starting the AgentCore-compatible Strands runtime on http://127.0.0.1:8080"
echo "POST JSON to /invocations, for example:"
echo "  curl -X POST http://127.0.0.1:8080/invocations -H 'Content-Type: application/json' -d '{\"prompt\":\"Investigate the bundled schema drift\"}'"
exec python agentcore_runtime/main.py
