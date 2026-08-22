from __future__ import annotations

import os
from dataclasses import dataclass

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


def _bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass
class Settings:
    strands_mode: str = os.getenv("STRANDS_MODE", "offline").lower()
    bedrock_model_id: str = os.getenv("BEDROCK_MODEL_ID", "global.anthropic.claude-sonnet-4-6")
    aws_region: str = os.getenv("AWS_REGION", os.getenv("AWS_DEFAULT_REGION", "us-west-2"))
    demo_delay_ms: int = int(os.getenv("DEMO_DELAY_MS", "420"))
    use_dynamodb: bool = _bool("USE_DYNAMODB", False)
    dynamodb_table: str = os.getenv("DYNAMODB_TABLE", "opsguardian-incidents")
    deployment_env: str = os.getenv("DEPLOYMENT_ENV", "local")

    @property
    def ai_enabled(self) -> bool:
        return self.strands_mode in {"live", "bedrock", "strands"}


settings = Settings()
