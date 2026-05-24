from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from src.agents.base import BaseAgent
from src.agents.llm_schemas import AccommodationOutput
from src.agents.prompt_context import (
    day_plans_json,
    destination_research_json,
    groq_quota_suffix,
    requirements_json,
    revision_hints_block,
)
from src.context import TripContext
from src.data.registry import apply_provenance
from src.stub_data import stub_accommodation

if TYPE_CHECKING:
    from src.data.registry import DataRegistry


class AccommodationAgent(BaseAgent):
    name = "accommodation"
    output_schema = AccommodationOutput

    def __init__(
        self,
        *,
        use_stub: bool = False,
        data_registry: Optional["DataRegistry"] = None,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self.use_stub = use_stub
        self.data_registry = data_registry

    def run(self, context: TripContext, step: int) -> TripContext:
        if self.use_stub:
            context.accommodation = stub_accommodation()
            neighborhoods = ", ".join(a.recommended_neighborhood for a in context.accommodation)
            self.log_trace(context, step, f"{neighborhoods} (stub)")
            return context

        provider_blocks = ""
        if self.data_registry and context.requirements:
            req = context.requirements
            for city in req.destinations:
                nights = self.data_registry.nights_for_city(context, city)
                result = self.data_registry.fetch_accommodation(
                    city=city,
                    nights=nights,
                    travel_style=req.travel_style,
                    budget_usd=req.budget_usd,
                    duration_days=req.duration_days,
                )
                provider_blocks += self.data_registry.provider_context_block(result)
            apply_provenance(context, self.data_registry)

        system = self.load_prompt("accommodation.md")
        user = (
            f"Original request:\n{context.raw_request}\n\n"
            f"Travel requirements:\n{requirements_json(context)}\n\n"
            f"Destination research:\n{destination_research_json(context)}\n\n"
            f"Day-by-day itinerary:\n{day_plans_json(context)}\n\n"
            "Recommend lodging for each city. Prefer structured provider data when supplied."
            f"{provider_blocks}"
            f"{revision_hints_block(context)}"
        )

        result = self.call_llm_with_retry(system, user, AccommodationOutput)
        context.accommodation = result.accommodation

        neighborhoods = ", ".join(a.recommended_neighborhood for a in context.accommodation)
        data_note = " + seed data" if provider_blocks else ""
        self.log_trace(context, step, f"{neighborhoods}{data_note} [{groq_quota_suffix()}]")
        return context
