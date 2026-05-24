from __future__ import annotations

import json
import os
import re
from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel

from src.llm.rate_limiter import RateLimitExceeded, RateLimiter
from src.llm.types import ModelProvider


class LLMResponse(BaseModel):
    content: str
    provider: ModelProvider
    model: str


class LLMClient(ABC):
    provider: ModelProvider

    @abstractmethod
    def complete(self, system: str, user: str, model: str) -> LLMResponse:
        ...


class GroqClient(LLMClient):
    provider = ModelProvider.GROQ

    def __init__(self, api_key: str | None = None, rate_limiter: RateLimiter | None = None) -> None:
        self._api_key = api_key or os.getenv("GROQ_API_KEY")
        self._rate_limiter = rate_limiter or RateLimiter.get()

    def complete(self, system: str, user: str, model: str) -> LLMResponse:
        if not self._api_key:
            raise RuntimeError("GROQ_API_KEY is not set")

        estimated_tokens = (len(system) + len(user)) // 4
        self._rate_limiter.acquire(self.provider, estimated_tokens=estimated_tokens)

        from groq import Groq

        client = Groq(api_key=self._api_key)
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                response_format={"type": "json_object"},
            )
        except Exception as exc:
            if _is_rate_limit_error(exc):
                raise RateLimitExceeded(
                    self.provider,
                    f"Groq rate limit hit: {exc}. Try again shortly or use --stub.",
                ) from exc
            raise

        content = response.choices[0].message.content or ""
        tokens = estimated_tokens
        if response.usage and response.usage.total_tokens:
            tokens = response.usage.total_tokens
        self._rate_limiter.record(self.provider, tokens=tokens)
        return LLMResponse(content=content, provider=self.provider, model=model)


class GeminiClient(LLMClient):
    provider = ModelProvider.GEMINI

    def __init__(self, api_key: str | None = None, rate_limiter: RateLimiter | None = None) -> None:
        self._api_key = api_key or os.getenv("GEMINI_API_KEY")
        self._rate_limiter = rate_limiter or RateLimiter.get()

    def complete(self, system: str, user: str, model: str) -> LLMResponse:
        if not self._api_key:
            raise RuntimeError("GEMINI_API_KEY is not set")

        estimated_tokens = (len(system) + len(user)) // 4
        self._rate_limiter.acquire(self.provider, estimated_tokens=estimated_tokens)

        import google.generativeai as genai

        genai.configure(api_key=self._api_key)
        gemini_model = genai.GenerativeModel(
            model_name=model,
            system_instruction=system,
            generation_config={"response_mime_type": "application/json"},
        )
        try:
            response = gemini_model.generate_content(user)
        except Exception as exc:
            if _is_rate_limit_error(exc):
                raise RateLimitExceeded(
                    self.provider,
                    f"Gemini quota exceeded: {exc}. Daily limit is 20 RPD — use --stub for offline mode.",
                ) from exc
            raise

        content = response.text or ""
        self._rate_limiter.record(self.provider, tokens=estimated_tokens)
        return LLMResponse(content=content, provider=self.provider, model=model)


def _is_rate_limit_error(exc: Exception) -> bool:
    text = str(exc).lower()
    return "429" in text or "rate limit" in text or "quota" in text or "resource_exhausted" in text


def get_llm_client(provider: ModelProvider) -> LLMClient:
    if provider == ModelProvider.GROQ:
        return GroqClient()
    if provider == ModelProvider.GEMINI:
        return GeminiClient()
    raise ValueError(f"Unknown provider: {provider}")


def extract_json(text: str) -> dict[str, Any]:
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{[\s\S]*\}", text)
        if match:
            return json.loads(match.group())
        raise
