from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Literal, Optional, Protocol, runtime_checkable

from pydantic import BaseModel, Field


class DataMode(str, Enum):
    SEED = "seed"
    LIVE = "live"
    AUTO = "auto"


Confidence = Literal["high", "medium", "low"]
SourceType = Literal["live_api", "seed_file", "llm_estimate", "computed"]


class DataSource(BaseModel):
    domain: str
    provider: str
    source: str
    source_type: SourceType
    confidence: Confidence
    fetched_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ProviderResult(BaseModel):
    data: Any
    source: DataSource


@runtime_checkable
class DataProvider(Protocol):
    name: str

    def fetch(self, **kwargs: Any) -> Optional[ProviderResult]:
        ...
