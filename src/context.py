from __future__ import annotations

import uuid
from typing import Literal, Optional

from pydantic import BaseModel, Field

from src.schemas import (
    AccommodationPlan,
    BudgetBreakdown,
    DataSourceRecord,
    DayPlan,
    DestinationResearch,
    TransportPlan,
    TravelRequirements,
    TripPlan,
    ValidationReport,
)


class TraceEntry(BaseModel):
    step: int
    agent: str
    provider: str
    model: str
    message: str


class TripContext(BaseModel):
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    raw_request: str = ""
    requirements: Optional[TravelRequirements] = None
    destination_research: list[DestinationResearch] = Field(default_factory=list)
    day_plans: list[DayPlan] = Field(default_factory=list)
    accommodation: list[AccommodationPlan] = Field(default_factory=list)
    transport: Optional[TransportPlan] = None
    budget: Optional[BudgetBreakdown] = None
    validation: Optional[ValidationReport] = None
    revision_count: int = 0
    revision_hints: list[str] = Field(default_factory=list)
    status: Literal["in_progress", "complete", "failed"] = "in_progress"
    trace: list[TraceEntry] = Field(default_factory=list)
    error_message: Optional[str] = None
    data_sources: list[DataSourceRecord] = Field(default_factory=list)
    data_provenance: dict[str, str] = Field(default_factory=dict)

    def add_trace(self, step: int, agent: str, provider: str, model: str, message: str) -> None:
        self.trace.append(
            TraceEntry(
                step=step,
                agent=agent,
                provider=provider,
                model=model,
                message=message,
            )
        )

    def to_trip_plan(self, *, requirements_only: bool = False) -> TripPlan:
        if self.status == "failed":
            return TripPlan(
                summary=self.error_message or "Request could not be processed.",
                requirements=self.requirements,
                status="failed",
            )

        assumptions = [a.reason for a in (self.requirements.assumptions if self.requirements else [])]
        validation_passed = self.validation.passed if self.validation else False

        if requirements_only and self.requirements:
            cities = ", ".join(self.requirements.destinations)
            summary = (
                f"{self.requirements.duration_days}-day trip to {cities} "
                f"(budget ${self.requirements.budget_usd:,.0f})"
            )
            return TripPlan(
                summary=summary,
                requirements=self.requirements,
                assumptions=assumptions,
                validation_passed=False,
                status="requirements_only",
            )

        summary = "Trip plan"
        if self.requirements:
            cities = ", ".join(self.requirements.destinations)
            summary = (
                f"{self.requirements.duration_days}-day trip to {cities} "
                f"(budget ${self.requirements.budget_usd:,.0f})"
            )
        if self.budget:
            summary += f" — estimated ${self.budget.estimated_total_usd:,.0f}"

        plan_status: str = "complete" if self.status == "complete" else "in_progress"

        return TripPlan(
            summary=summary,
            requirements=self.requirements,
            day_by_day=self.day_plans,
            neighborhoods_to_stay=self.accommodation,
            logistics=self.transport,
            budget=self.budget,
            assumptions=assumptions,
            validation_passed=validation_passed,
            status=plan_status,  # type: ignore[arg-type]
            data_sources=self.data_sources,
            data_provenance=self.data_provenance,
        )
