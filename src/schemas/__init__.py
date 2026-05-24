"""Pydantic schemas for travel planning artifacts."""

from src.schemas.requirements import AssumedField, TravelRequirements, TravelStyle
from src.schemas.trip_plan import (
    AccommodationOption,
    AccommodationPlan,
    Activity,
    Attraction,
    BudgetBreakdown,
    BudgetStatus,
    DayPlan,
    DestinationResearch,
    InterCityLeg,
    Neighborhood,
    TransportPlan,
    TripPlan,
    ValidationIssue,
    ValidationReport,
    DataSourceRecord,
)

__all__ = [
    "AccommodationOption",
    "AccommodationPlan",
    "Activity",
    "AssumedField",
    "Attraction",
    "BudgetBreakdown",
    "BudgetStatus",
    "DayPlan",
    "DataSourceRecord",
    "DestinationResearch",
    "InterCityLeg",
    "Neighborhood",
    "TransportPlan",
    "TravelRequirements",
    "TravelStyle",
    "TripPlan",
    "ValidationIssue",
    "ValidationReport",
]
