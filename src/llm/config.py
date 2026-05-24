from __future__ import annotations

import os
from pathlib import Path

import yaml
from pydantic import BaseModel

from src.llm.types import ModelProvider


class AgentModelConfig(BaseModel):
    provider: ModelProvider
    model: str


_CONFIG_PATH = Path(__file__).parent / "agent_models.yaml"

_ENV_MODEL_OVERRIDES: dict[ModelProvider, str] = {
    ModelProvider.GROQ: "GROQ_MODEL",
    ModelProvider.GEMINI: "GEMINI_MODEL",
}


def load_agent_models(config_path: Path | None = None) -> dict[str, AgentModelConfig]:
    path = config_path or _CONFIG_PATH
    with path.open() as f:
        raw = yaml.safe_load(f)

    return {
        agent_name: AgentModelConfig(
            provider=ModelProvider(entry["provider"]),
            model=entry["model"],
        )
        for agent_name, entry in raw.items()
    }


def _apply_env_override(config: AgentModelConfig) -> AgentModelConfig:
    env_key = _ENV_MODEL_OVERRIDES.get(config.provider)
    if not env_key:
        return config
    override = os.getenv(env_key)
    if override and override != config.model:
        return AgentModelConfig(provider=config.provider, model=override)
    return config


def get_agent_config(agent_name: str, config_path: Path | None = None) -> AgentModelConfig:
    models = load_agent_models(config_path)
    if agent_name not in models:
        raise KeyError(f"No model config for agent: {agent_name}")
    return _apply_env_override(models[agent_name])
