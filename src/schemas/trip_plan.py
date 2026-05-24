from __future__ import annotations

from enum import Enum
from typing import Literal, Optional

from pydantic import BaseModel, Field

from src.schemas.requirements import TravelRequirements


class DataSourceRecord(BaseModel):
    """Provenance record for Phase 4 data layer (re-exported from data.base)."""

    domain: str
    provider: str
    source: str
    source_type: str
    confidence: str
    fetched_at: str = ""


class Neighborhood(BaseModel):
    name: str
    fit_score: float = Field(ge=0, le=1)
    reason: str


class Attraction(BaseModel):
    name: str
    category: str
    crowd_level: Literal["low", "medium", "high"] = "medium"
    best_time: str = ""
    estimated_cost_usd: float = Field(default=0, ge=0)


class DestinationResearch(BaseModel):
    city: str
    neighborhoods: list[Neighborhood] = Field(default_factory=list)
    attractions: list[Attraction] = Field(default_factory=list)
    food_highlights: list[str] = Field(default_factory=list)


class Activity(BaseModel):
    time: str
    name: str
    duration_hours: float = Field(ge=0)


class DayPlan(BaseModel):
    day: int = Field(ge=1)
    city: str
    theme: str
    activities: list[Activity] = Field(default_factory=list)


class AccommodationOption(BaseModel):
    name: str
    price_per_night_usd: float = Field(ge=0)
    tier: Literal["budget", "mid-range", "luxury"] = "mid-range"


class AccommodationPlan(BaseModel):
    city: str
    nights: int = Field(ge=0)
    recommended_neighborhood: str
    reason: str
    options: list[AccommodationOption] = Field(default_factory=list)


class InterCityLeg(BaseModel):
    from_city: str = Field(alias="from")
    to_city: str = Field(alias="to")
    mode: str
    duration_hours: float = Field(ge=0)
    estimated_cost_usd: float = Field(ge=0)
    suggested_day: int = Field(ge=1)

    model_config = {"populate_by_name": True}


class TransportPlan(BaseModel):
    inter_city: list[InterCityLeg] = Field(default_factory=list)
    local_transit_notes: str = ""


class BudgetStatus(str, Enum):
    WITHIN_BUDGET = "within_budget"
    OVER_BUDGET = "over_budget"


class BudgetBreakdown(BaseModel):
    budget_usd: float = Field(ge=0)
    estimated_total_usd: float = Field(ge=0)
    breakdown: dict[str, float] = Field(default_factory=dict)
    status: BudgetStatus
    savings_suggestions: list[str] = Field(default_factory=list)


class ValidationIssue(BaseModel):
    severity: Literal["error", "warning"]
    check: str
    message: str
    suggested_agent: str = ""


class ValidationReport(BaseModel):
    passed: bool
    issues: list[ValidationIssue] = Field(default_factory=list)


class TripPlan(BaseModel):
    summary: str
    requirements: Optional[TravelRequirements] = None
    day_by_day: list[DayPlan] = Field(default_factory=list)
    neighborhoods_to_stay: list[AccommodationPlan] = Field(default_factory=list)
    logistics: Optional[TransportPlan] = None
    budget: Optional[BudgetBreakdown] = None
    assumptions: list[str] = Field(default_factory=list)
    validation_passed: bool = False
    status: Literal["in_progress", "complete", "failed", "requirements_only"] = "in_progress"
    data_sources: list[DataSourceRecord] = Field(default_factory=list)
    data_provenance: dict[str, str] = Field(default_factory=dict)
