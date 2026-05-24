from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from src.agents.base import BaseAgent
from src.agents.llm_schemas import BudgetAnalystOutput
from src.agents.prompt_context import (
    accommodation_json,
    day_plans_json,
    gemini_quota_suffix,
    requirements_json,
    transport_json,
)
from src.context import TripContext
from src.data.registry import apply_provenance
from src.stub_data import stub_budget

if TYPE_CHECKING:
    from src.data.registry import DataRegistry


class BudgetAnalystAgent(BaseAgent):
    name = "budget_analyst"
    output_schema = BudgetAnalystOutput

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
            context.budget = stub_budget()
            b = context.budget
            self.log_trace(
                context,
                step,
                f"${b.estimated_total_usd:,.0f} / ${b.budget_usd:,.0f} ({b.status.value}) (stub)",
            )
            return context

        if self.data_registry:
            computed = self.data_registry.compute_budget(context)
            apply_provenance(context, self.data_registry)
            if computed and computed.source.confidence in ("high", "medium"):
                context.budget = computed.data
                b = context.budget
                status = b.status.value.replace("_", " ")
                self.log_trace(
                    context,
                    step,
                    f"${b.estimated_total_usd:,.0f} / ${b.budget_usd:,.0f} ({status}, computed) "
                    f"[{gemini_quota_suffix()}]",
                )
                return context

        system = self.load_prompt("budget_analyst.md")
        user = (
            f"Original request:\n{context.raw_request}\n\n"
            f"Travel requirements:\n{requirements_json(context)}\n\n"
            f"Day-by-day itinerary:\n{day_plans_json(context)}\n\n"
            f"Accommodation:\n{accommodation_json(context)}\n\n"
            f"Transport:\n{transport_json(context)}\n\n"
            "Estimate the total trip cost and compare to budget."
        )

        result = self.call_llm_with_retry(system, user, BudgetAnalystOutput)
        context.budget = result.budget

        b = context.budget
        status = b.status.value.replace("_", " ")
        suggestions = len(b.savings_suggestions)
        extra = f", {suggestions} savings tips" if suggestions else ""
        self.log_trace(
            context,
            step,
            f"${b.estimated_total_usd:,.0f} / ${b.budget_usd:,.0f} ({status}){extra} "
            f"[{gemini_quota_suffix()}]",
        )
        return context
