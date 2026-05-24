from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from src.agents.base import BaseAgent
from src.agents.llm_schemas import DestinationResearchOutput
from src.agents.prompt_context import groq_quota_suffix, requirements_json
from src.context import TripContext
from src.data.registry import apply_provenance
from src.stub_data import stub_destination_research

if TYPE_CHECKING:
    from src.data.registry import DataRegistry


class DestinationResearchAgent(BaseAgent):
    name = "destination_research"
    output_schema = DestinationResearchOutput

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
            context.destination_research = stub_destination_research()
            count = sum(len(d.attractions) for d in context.destination_research)
            self.log_trace(
                context,
                step,
                f"{count} attractions across {len(context.destination_research)} cities (stub)",
            )
            return context

        provider_blocks = ""
        if self.data_registry and context.requirements:
            for city in context.requirements.destinations:
                result = self.data_registry.fetch_destination(
                    city,
                    context.requirements.interests,
                )
                provider_blocks += self.data_registry.provider_context_block(result)
            apply_provenance(context, self.data_registry)

        system = self.load_prompt("destination_research.md")
        user = (
            f"Original request:\n{context.raw_request}\n\n"
            f"Travel requirements:\n{requirements_json(context)}\n\n"
            "Research each destination city. Prefer structured provider data when supplied."
            f"{provider_blocks}"
        )

        result = self.call_llm_with_retry(system, user, DestinationResearchOutput)
        context.destination_research = result.destinations

        count = sum(len(d.attractions) for d in context.destination_research)
        cities = ", ".join(d.city for d in context.destination_research)
        data_note = " + seed data" if provider_blocks else ""
        self.log_trace(
            context,
            step,
            f"{count} attractions across {cities}{data_note} [{groq_quota_suffix()}]",
        )
        return context
