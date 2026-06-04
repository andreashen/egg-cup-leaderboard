from pathlib import Path

import yaml
from pydantic import BaseModel, Field


class ProviderConfig(BaseModel):
    season: str
    base_url: str
    timeout_seconds: int = Field(gt=0)
    retries: int = Field(ge=0)
    endpoints: dict[str, str]


def load_provider_config(path: Path) -> ProviderConfig:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return ProviderConfig.model_validate(data)
