from __future__ import annotations

import json
from abc import ABC, abstractmethod
from pathlib import Path
from typing import TypeVar

import structlog
from pydantic import BaseModel, ValidationError

from src.context import TripContext
from src.llm.config import AgentModelConfig, get_agent_config
from src.llm.providers import LLMClient, extract_json, get_llm_client
from src.llm.rate_limiter import RateLimiter

logger = structlog.get_logger()

T = TypeVar("T", bound=BaseModel)

PROMPTS_DIR = Path(__file__).parent.parent.parent / "prompts"


class BaseAgent(ABC):
    name: str
    output_schema: type[BaseModel] | None = None

    def __init__(
        self,
        config: AgentModelConfig | None = None,
        llm_client: LLMClient | None = None,
    ) -> None:
        self.config = config or get_agent_config(self.name)
        self.llm_client = llm_client or get_llm_client(self.config.provider)

    def load_prompt(self, filename: str) -> str:
        path = PROMPTS_DIR / filename
        if path.exists():
            return path.read_text()
        return f"You are the {self.name} agent."

    def parse_output(self, raw: str, schema: type[T]) -> T:
        data = extract_json(raw)
        return schema.model_validate(data)

    def call_llm(self, system: str, user: str) -> str:
        response = self.llm_client.complete(
            system=system,
            user=user,
            model=self.config.model,
        )
        return response.content

    def call_llm_with_retry(self, system: str, user: str, schema: type[T]) -> T:
        try:
            raw = self.call_llm(system, user)
            return self.parse_output(raw, schema)
        except (ValidationError, json.JSONDecodeError) as first_error:
            logger.warning("agent_parse_failed", agent=self.name, error=str(first_error))
            limiter = RateLimiter.get()
            if not limiter.can_acquire(self.config.provider):
                raise
            retry_user = (
                f"{user}\n\n"
                f"Your previous response was invalid: {first_error}\n"
                "Return valid JSON matching the required schema."
            )
            raw = self.call_llm(system, retry_user)
            return self.parse_output(raw, schema)

    @abstractmethod
    def run(self, context: TripContext, step: int) -> TripContext:
        ...

    def log_trace(self, context: TripContext, step: int, message: str) -> None:
        context.add_trace(
            step=step,
            agent=self.name,
            provider=self.config.provider.value,
            model=self.config.model,
            message=message,
        )
        logger.info(
            "agent_step",
            step=step,
            agent=self.name,
            provider=self.config.provider.value,
            model=self.config.model,
            message=message,
        )
