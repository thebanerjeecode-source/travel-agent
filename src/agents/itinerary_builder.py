from __future__ import annotations

from src.agents.base import BaseAgent
from src.agents.llm_schemas import ItineraryBuilderOutput
from src.agents.prompt_context import (
    destination_research_json,
    groq_quota_suffix,
    requirements_json,
    revision_hints_block,
)
from src.context import TripContext
from src.stub_data import stub_day_plans


class ItineraryBuilderAgent(BaseAgent):
    name = "itinerary_builder"
    output_schema = ItineraryBuilderOutput

    def __init__(self, *, use_stub: bool = False, **kwargs) -> None:
        super().__init__(**kwargs)
        self.use_stub = use_stub

    def run(self, context: TripContext, step: int) -> TripContext:
        if self.use_stub:
            context.day_plans = stub_day_plans()
            self.log_trace(context, step, f"{len(context.day_plans)} day plans created (stub)")
            return context

        system = self.load_prompt("itinerary_builder.md")
        days = context.requirements.duration_days if context.requirements else "?"
        user = (
            f"Original request:\n{context.raw_request}\n\n"
            f"Travel requirements:\n{requirements_json(context)}\n\n"
            f"Destination research:\n{destination_research_json(context)}\n\n"
            f"Build exactly {days} day plans."
            f"{revision_hints_block(context)}"
        )

        result = self.call_llm_with_retry(system, user, ItineraryBuilderOutput)
        context.day_plans = sorted(result.day_plans, key=lambda d: d.day)

        themes = ", ".join(d.theme for d in context.day_plans[:3])
        suffix = "…" if len(context.day_plans) > 3 else ""
        self.log_trace(
            context,
            step,
            f"{len(context.day_plans)} days: {themes}{suffix} [{groq_quota_suffix()}]",
        )
        return context
