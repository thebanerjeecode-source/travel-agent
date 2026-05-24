from __future__ import annotations

from dataclasses import asdict
from typing import Any

from src.context import TripContext
from src.llm.rate_limiter import RateLimiter
from src.llm.types import ModelProvider
from src.schemas import TripPlan


def build_plan_payload(trip_plan: TripPlan, context: TripContext) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "raw_request": context.raw_request,
        "session_id": context.session_id,
        "trace": [entry.model_dump() for entry in context.trace],
        "trip_plan": trip_plan.model_dump(mode="json", by_alias=True),
    }
    groq_usage = RateLimiter.get().usage(ModelProvider.GROQ)
    gemini_usage = RateLimiter.get().usage(ModelProvider.GEMINI)
    payload["quota"] = {
        "groq": asdict(groq_usage),
        "gemini": asdict(gemini_usage),
    }
    if context.data_provenance:
        payload["data_provenance"] = context.data_provenance
    return payload


def gemini_rpd_warning() -> str | None:
    usage = RateLimiter.get().usage(ModelProvider.GEMINI)
    if usage.rpd_used >= usage.rpd_limit * 0.8:
        return (
            f"Gemini quota high: {usage.summary()} "
            f"(≥80% of daily limit). Use dry-run to demo without API calls."
        )
    return None


def quota_snapshot() -> dict[str, dict]:
    groq_usage = RateLimiter.get().usage(ModelProvider.GROQ)
    gemini_usage = RateLimiter.get().usage(ModelProvider.GEMINI)
    return {
        "groq": asdict(groq_usage),
        "gemini": asdict(gemini_usage),
    }
