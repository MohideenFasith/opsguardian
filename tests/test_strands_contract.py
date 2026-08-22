from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_live_advisor_uses_strands_agent_and_bedrock_model():
    text = (ROOT / "opsguardian" / "strands_advisor.py").read_text()
    assert "from strands import Agent, tool" in text
    assert "from strands.models import BedrockModel" in text
    assert "run_sandbox_validation" in text
    assert "Agent(" in text


def test_agentcore_runtime_is_framework_native():
    text = (ROOT / "agentcore_runtime" / "main.py").read_text()
    assert "BedrockAgentCoreApp" in text
    assert "@app.entrypoint" in text
    assert "@tool" in text
    assert "Strands Agents SDK" in text
    assert "production-write tool" in text


def test_agentcore_deploy_script_uses_current_cli_flow():
    text = (ROOT / "scripts" / "deploy_agentcore.sh").read_text()
    assert "agentcore create" in text
    assert "--framework Strands" in text
    assert "--build CodeZip" in text
    assert "agentcore deploy --dry-run" in text
    assert "agentcore deploy" in text
    assert "agentcore status" in text


def test_repository_uses_aws_agent_runtime_dependencies():
    req = (ROOT / "requirements.txt").read_text().lower()
    assert "strands-agents" in req
    assert "bedrock-agentcore" in req


def test_license_is_mit():
    assert (ROOT / "LICENSE").read_text().startswith("MIT License")


def test_agentcore_local_script_runs_the_checked_in_runtime():
    text = (ROOT / "scripts" / "agentcore_local.sh").read_text()
    assert "python agentcore_runtime/main.py" in text
    assert "agentcore dev" not in text


def test_agentcore_deploy_script_validates_and_is_noninteractive():
    text = (ROOT / "scripts" / "deploy_agentcore.sh").read_text()
    assert "agentcore validate" in text
    assert "agentcore deploy -y" in text


def test_agentcore_runtime_targets_maintained_python():
    text = (ROOT / "agentcore_runtime" / "pyproject.toml").read_text()
    assert 'requires-python = ">=3.12,<3.15"' in text


def test_runtime_dependencies_target_current_major_versions():
    req = (ROOT / "requirements.txt").read_text().lower()
    runtime_req = (ROOT / "agentcore_runtime" / "pyproject.toml").read_text().lower()
    for text in (req, runtime_req):
        assert "strands-agents>=1.50,<2" in text
        assert "bedrock-agentcore>=1.21,<2" in text
        assert "bedrock-agentcore>=0.1,<1" not in text
