from __future__ import annotations

from src.agents.base import BaseAgent
from src.agents.llm_schemas import ValidatorOutput
from src.agents.prompt_context import (
    accommodation_json,
    day_plans_json,
    destination_research_json,
    gemini_quota_suffix,
    requirements_json,
    transport_json,
)
from src.context import TripContext
from src.stub_data import stub_validation


class ValidatorAgent(BaseAgent):
    name = "validator"
    output_schema = ValidatorOutput

    def __init__(self, *, use_stub: bool = False, **kwargs) -> None:
        super().__init__(**kwargs)
        self.use_stub = use_stub

    def run(self, context: TripContext, step: int) -> TripContext:
        if self.use_stub:
            context.validation = stub_validation()
            status = "PASSED" if context.validation.passed else "FAILED"
            self.log_trace(context, step, f"{status} (stub)")
            return context

        budget_block = "{}"
        if context.budget:
            budget_block = context.budget.model_dump_json(indent=2)

        system = self.load_prompt("validator.md")
        user = (
            f"Original request:\n{context.raw_request}\n\n"
            f"Travel requirements:\n{requirements_json(context)}\n\n"
            f"Destination research:\n{destination_research_json(context)}\n\n"
            f"Day-by-day itinerary:\n{day_plans_json(context)}\n\n"
            f"Accommodation:\n{accommodation_json(context)}\n\n"
            f"Transport:\n{transport_json(context)}\n\n"
            f"Budget:\n{budget_block}\n\n"
            "Validate this plan against the original request."
        )

        result = self.call_llm_with_retry(system, user, ValidatorOutput)
        context.validation = result.validation

        if context.validation.passed:
            msg = f"PASSED [{gemini_quota_suffix()}]"
        else:
            errors = [i for i in context.validation.issues if i.severity == "error"]
            checks = ", ".join(i.check for i in errors[:3]) or "issues found"
            msg = f"FAILED ({checks}) [{gemini_quota_suffix()}]"
        self.log_trace(context, step, msg)
        return context
