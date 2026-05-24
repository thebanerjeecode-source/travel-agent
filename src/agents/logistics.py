from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from src.agents.base import BaseAgent
from src.agents.llm_schemas import LogisticsOutput
from src.agents.prompt_context import (
    day_plans_json,
    groq_quota_suffix,
    requirements_json,
    revision_hints_block,
)
from src.context import TripContext
from src.data.registry import apply_provenance
from src.stub_data import stub_transport

if TYPE_CHECKING:
    from src.data.registry import DataRegistry


class LogisticsAgent(BaseAgent):
    name = "logistics"
    output_schema = LogisticsOutput

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
            context.transport = stub_transport()
            leg = context.transport.inter_city[0] if context.transport.inter_city else None
            msg = "local transit only (stub)"
            if leg:
                msg = f"{leg.mode} {leg.from_city}→{leg.to_city} on Day {leg.suggested_day} (stub)"
            self.log_trace(context, step, msg)
            return context

        provider_block = ""
        seed_transport = None
        if self.data_registry:
            result = self.data_registry.fetch_transport(context)
            provider_block = self.data_registry.provider_context_block(result)
            if result:
                seed_transport = result.data
            apply_provenance(context, self.data_registry)

        system = self.load_prompt("logistics.md")
        user = (
            f"Original request:\n{context.raw_request}\n\n"
            f"Travel requirements:\n{requirements_json(context)}\n\n"
            f"Day-by-day itinerary:\n{day_plans_json(context)}\n\n"
            "Plan inter-city transport and local transit tips. "
            "Use exact inter-city legs from provider data when supplied."
            f"{provider_block}"
            f"{revision_hints_block(context)}"
        )

        result = self.call_llm_with_retry(system, user, LogisticsOutput)
        context.transport = result.transport

        if seed_transport and seed_transport.inter_city:
            context.transport.inter_city = seed_transport.inter_city
            if seed_transport.local_transit_notes and not context.transport.local_transit_notes:
                context.transport.local_transit_notes = seed_transport.local_transit_notes

        leg = context.transport.inter_city[0] if context.transport.inter_city else None
        if leg:
            msg = f"{leg.mode} {leg.from_city}→{leg.to_city} on Day {leg.suggested_day}"
        else:
            msg = "local transit only"
        data_note = " + seed routes" if provider_block else ""
        self.log_trace(context, step, f"{msg}{data_note} [{groq_quota_suffix()}]")
        return context
