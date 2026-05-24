from __future__ import annotations

from enum import Enum
from typing import Union

from pydantic import BaseModel, Field


class TravelStyle(str, Enum):
    BUDGET = "budget"
    MID_RANGE = "mid-range"
    LUXURY = "luxury"


class AssumedField(BaseModel):
    field: str
    assumed_value: Union[str, int, float, bool]
    reason: str


class TravelRequirements(BaseModel):
    duration_days: int = Field(ge=1)
    destinations: list[str] = Field(min_length=1)
    budget_usd: float = Field(ge=0)
    interests: list[str] = Field(default_factory=list)
    dislikes: list[str] = Field(default_factory=list)
    travel_style: TravelStyle = TravelStyle.MID_RANGE
    party_size: int = Field(default=1, ge=1)
    assumptions: list[AssumedField] = Field(default_factory=list)
