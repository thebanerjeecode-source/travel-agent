from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import BaseModel, Field, field_validator


class PlanRequest(BaseModel):
    request: str = Field(..., min_length=1, description="Natural-language travel request")
    dry_run: bool = False
    intent_only: bool = False
    planning_only: bool = False
    data_mode: Optional[Literal["auto", "seed", "live"]] = None

    @field_validator("request")
    @classmethod
    def request_not_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Request must not be blank")
        return value


class QuotaUsage(BaseModel):
    rpm_used: int = 0
    rpm_limit: int = 0
    rpd_used: int = 0
    rpd_limit: int = 0


class QuotaInfo(BaseModel):
    groq: QuotaUsage
    gemini: QuotaUsage


class TraceEntryResponse(BaseModel):
    step: int
    agent: str
    provider: str
    model: str
    message: str


class PlanResponse(BaseModel):
    session_id: str
    status: Literal["complete", "failed", "requirements_only", "in_progress"]
    raw_request: str
    trip_plan: dict[str, Any]
    trace: list[TraceEntryResponse]
    quota: QuotaInfo
    data_provenance: dict[str, str] = Field(default_factory=dict)
    warning: Optional[str] = None
    error: Optional[str] = None


class HealthResponse(BaseModel):
    status: Literal["ok"] = "ok"
