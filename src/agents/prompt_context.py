from __future__ import annotations

import json

from src.context import TripContext
from src.llm.rate_limiter import RateLimiter
from src.llm.types import ModelProvider


def groq_quota_suffix() -> str:
    return RateLimiter.get().usage(ModelProvider.GROQ).summary()


def gemini_quota_suffix() -> str:
    return RateLimiter.get().usage(ModelProvider.GEMINI).summary()


def transport_json(context: TripContext) -> str:
    if not context.transport:
        return "{}"
    return json.dumps(context.transport.model_dump(by_alias=True), indent=2)


def revision_hints_block(context: TripContext) -> str:
    if not context.revision_hints:
        return ""
    lines = "\n".join(f"- {hint}" for hint in context.revision_hints)
    return f"\n\nRevision notes (address these):\n{lines}\n"


def requirements_json(context: TripContext) -> str:
    if not context.requirements:
        return "{}"
    return json.dumps(context.requirements.model_dump(mode="json"), indent=2)


def destination_research_json(context: TripContext) -> str:
    return json.dumps(
        [d.model_dump() for d in context.destination_research],
        indent=2,
    )


def day_plans_json(context: TripContext) -> str:
    return json.dumps([d.model_dump() for d in context.day_plans], indent=2)


def accommodation_json(context: TripContext) -> str:
    return json.dumps([a.model_dump() for a in context.accommodation], indent=2)
