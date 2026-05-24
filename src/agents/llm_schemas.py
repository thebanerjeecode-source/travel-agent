from __future__ import annotations

from pydantic import BaseModel, Field

from src.schemas import (
    AccommodationPlan,
    BudgetBreakdown,
    DayPlan,
    DestinationResearch,
    TransportPlan,
    ValidationReport,
)


class DestinationResearchOutput(BaseModel):
    destinations: list[DestinationResearch] = Field(min_length=1)


class ItineraryBuilderOutput(BaseModel):
    day_plans: list[DayPlan] = Field(min_length=1)


class AccommodationOutput(BaseModel):
    accommodation: list[AccommodationPlan] = Field(min_length=1)


class LogisticsOutput(BaseModel):
    transport: TransportPlan


class BudgetAnalystOutput(BaseModel):
    budget: BudgetBreakdown


class ValidatorOutput(BaseModel):
    validation: ValidationReport
