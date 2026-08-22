#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BUILD="$ROOT/.agentcore-build"
AGENT_NAME="${AGENT_NAME:-OpsGuardianAgent}"
PROJECT_DIR="$BUILD/$AGENT_NAME"

command -v aws >/dev/null || { echo "AWS CLI is required." >&2; exit 1; }
command -v node >/dev/null || { echo "Node.js 20+ is required by AgentCore CLI." >&2; exit 1; }
command -v uv >/dev/null || { echo "uv is required for AgentCore Python CodeZip deployments." >&2; exit 1; }
aws sts get-caller-identity >/dev/null

if ! command -v agentcore >/dev/null; then
  echo "Installing the official AgentCore CLI..."
  npm install -g @aws/agentcore
fi

mkdir -p "$BUILD"

# Preserve the generated AgentCore project after the first deployment so repeated
# runs update the same local deployment state instead of accidentally starting over.
if [[ ! -f "$PROJECT_DIR/agentcore/agentcore.json" ]]; then
  rm -rf "$PROJECT_DIR"
  cd "$BUILD"
  agentcore create \
    --name "$AGENT_NAME" \
    --framework Strands \
    --protocol HTTP \
    --model-provider Bedrock \
    --memory none \
    --build CodeZip
fi

if [[ ! -d "$PROJECT_DIR" ]]; then
  echo "Generated AgentCore project not found at $PROJECT_DIR" >&2
  exit 1
fi

MAIN_FILE="$(find "$PROJECT_DIR/app" -type f -name main.py | head -n 1)"
if [[ -z "$MAIN_FILE" ]]; then
  echo "Could not locate the generated AgentCore Python entrypoint." >&2
  exit 1
fi
APP_DIR="$(dirname "$MAIN_FILE")"

cp "$ROOT/agentcore_runtime/main.py" "$MAIN_FILE"
cp "$ROOT/agentcore_runtime/pyproject.toml" "$APP_DIR/pyproject.toml"
rm -rf "$APP_DIR/opsguardian" "$APP_DIR/sample_data"
cp -R "$ROOT/opsguardian" "$APP_DIR/opsguardian"
cp -R "$ROOT/sample_data" "$APP_DIR/sample_data"

# Keep the generated uv lock in sync with our tested dependency contract.
(
  cd "$APP_DIR"
  uv lock
)

cd "$PROJECT_DIR"
echo "Validating generated AgentCore project..."
agentcore validate
echo "Previewing deployment..."
agentcore deploy --dry-run

echo "Deploying OpsGuardian to Amazon Bedrock AgentCore Runtime..."
agentcore deploy -y
agentcore status

echo
echo "Deployment complete. Test it with:"
echo "  cd '$PROJECT_DIR'"
echo "  agentcore invoke --prompt 'Investigate the bundled schema drift and validate the safest repair.'"
