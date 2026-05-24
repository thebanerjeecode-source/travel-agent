from __future__ import annotations

import structlog

from src.agents.base import BaseAgent
from src.agents.intent_normalizer import IntentParserLLMOutput, normalize_requirements
from src.context import TripContext
from src.llm.rate_limiter import RateLimiter
from src.stub_data import stub_requirements

logger = structlog.get_logger()


class IntentParserAgent(BaseAgent):
    name = "intent_parser"
    output_schema = IntentParserLLMOutput

    def __init__(self, *, use_stub: bool = False, **kwargs) -> None:
        super().__init__(**kwargs)
        self.use_stub = use_stub

    def run(self, context: TripContext, step: int) -> TripContext:
        if self.use_stub:
            context.requirements = stub_requirements()
            self.log_trace(context, step, "extracted requirements (stub)")
            return context

        system = self.load_prompt("intent_parser.md")
        user = f"Extract travel requirements from this request:\n\n{context.raw_request}"

        parsed = self.call_llm_with_retry(system, user, IntentParserLLMOutput)
        requirements = normalize_requirements(parsed)

        if requirements is None:
            context.status = "failed"
            context.error_message = (
                "I couldn't identify any destinations in your request. "
                "Please specify at least one city or region, e.g. "
                "'Plan a 5-day trip to Tokyo and Kyoto with a $3,000 budget.'"
            )
            self.log_trace(context, step, "no destinations extracted — abort")
            return context

        context.requirements = requirements

        cities = ", ".join(requirements.destinations)
        quota = RateLimiter.get().usage(self.config.provider).summary()
        self.log_trace(
            context,
            step,
            f"extracted {requirements.duration_days}-day, {cities}, "
            f"${requirements.budget_usd:,.0f} budget [{quota}]",
        )
        return context
