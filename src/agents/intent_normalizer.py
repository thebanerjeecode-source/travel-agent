from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field

from src.schemas import AssumedField, TravelRequirements, TravelStyle


class IntentParserLLMOutput(BaseModel):
    """Raw structured output from the Intent Parser LLM — fields may be omitted."""

    duration_days: Optional[int] = Field(default=None, ge=1)
    destinations: list[str] = Field(default_factory=list)
    budget_usd: Optional[float] = Field(default=None, ge=0)
    interests: list[str] = Field(default_factory=list)
    dislikes: list[str] = Field(default_factory=list)
    travel_style: Optional[TravelStyle] = None
    party_size: Optional[int] = Field(default=None, ge=1)
    assumptions: list[AssumedField] = Field(default_factory=list)


def _estimate_budget(duration_days: int, party_size: int, travel_style: TravelStyle) -> float:
    daily_per_person = {
        TravelStyle.BUDGET: 80,
        TravelStyle.MID_RANGE: 150,
        TravelStyle.LUXURY: 350,
    }
    return duration_days * party_size * daily_per_person[travel_style]


def normalize_requirements(parsed: IntentParserLLMOutput) -> TravelRequirements | None:
    """
    Apply defaults for missing fields and merge assumptions.
    Returns None if no destinations (caller should abort).
    """
    destinations = [d.strip() for d in parsed.destinations if d.strip()]
    if not destinations:
        return None

    assumptions: list[AssumedField] = list(parsed.assumptions)
    travel_style = parsed.travel_style or TravelStyle.MID_RANGE
    party_size = parsed.party_size or 1

    duration_days = parsed.duration_days
    if duration_days is None:
        duration_days = 5
        assumptions.append(
            AssumedField(
                field="duration_days",
                assumed_value=5,
                reason="Duration not specified; defaulted to 5 days",
            )
        )

    budget_usd = parsed.budget_usd
    if budget_usd is None:
        budget_usd = _estimate_budget(duration_days, party_size, travel_style)
        assumptions.append(
            AssumedField(
                field="budget_usd",
                assumed_value=budget_usd,
                reason="Budget not specified; estimated from duration and travel style",
            )
        )

    if parsed.party_size is None and not any(a.field == "party_size" for a in assumptions):
        assumptions.append(
            AssumedField(
                field="party_size",
                assumed_value=1,
                reason="Party size not specified; assumed solo traveler",
            )
        )

    if parsed.travel_style is None and not any(a.field == "travel_style" for a in assumptions):
        assumptions.append(
            AssumedField(
                field="travel_style",
                assumed_value=travel_style.value,
                reason="Travel style not specified; assumed mid-range",
            )
        )

    return TravelRequirements(
        duration_days=duration_days,
        destinations=destinations,
        budget_usd=budget_usd,
        interests=parsed.interests,
        dislikes=parsed.dislikes,
        travel_style=travel_style,
        party_size=party_size,
        assumptions=assumptions,
    )
