from __future__ import annotations

from src.api.schemas import PlanRequest, PlanResponse, QuotaInfo, QuotaUsage, TraceEntryResponse
from src.api.session_store import session_store
from src.llm.rate_limiter import RateLimitExceeded
from src.orchestrator import PHASE_INTENT, PHASE_PLANNING, PHASE_STUB, Orchestrator
from src.plan_output import build_plan_payload, gemini_rpd_warning, quota_snapshot


def _resolve_phase(body: PlanRequest) -> int | None:
    if body.dry_run:
        return PHASE_STUB
    if body.intent_only:
        return PHASE_INTENT
    if body.planning_only:
        return PHASE_PLANNING
    return None


def _to_response(trip_plan, context) -> PlanResponse:
    payload = build_plan_payload(trip_plan, context)
    status = trip_plan.status
    if status not in ("complete", "failed", "requirements_only", "in_progress"):
        status = "complete"

    return PlanResponse(
        session_id=context.session_id,
        status=status,  # type: ignore[arg-type]
        raw_request=context.raw_request,
        trip_plan=payload["trip_plan"],
        trace=[TraceEntryResponse(**entry) for entry in payload["trace"]],
        quota=QuotaInfo(
            groq=QuotaUsage(**payload["quota"]["groq"]),
            gemini=QuotaUsage(**payload["quota"]["gemini"]),
        ),
        data_provenance=payload.get("data_provenance", {}),
        warning=gemini_rpd_warning(),
        error=context.error_message if trip_plan.status == "failed" else None,
    )


def create_plan(body: PlanRequest) -> PlanResponse:
    phase = _resolve_phase(body)
    orchestrator = (
        Orchestrator(data_mode=body.data_mode)
        if phase is None
        else Orchestrator(phase=phase, data_mode=body.data_mode)
    )

    try:
        trip_plan, context = orchestrator.run(body.request)
    except RateLimitExceeded as exc:
        quota = quota_snapshot()
        return PlanResponse(
            session_id="",
            status="failed",
            raw_request=body.request,
            trip_plan={"summary": str(exc), "status": "failed"},
            trace=[],
            quota=QuotaInfo(
                groq=QuotaUsage(**quota["groq"]),
                gemini=QuotaUsage(**quota["gemini"]),
            ),
            error=str(exc),
            warning="Use dry_run=true for offline demo or try again tomorrow.",
        )

    response = _to_response(trip_plan, context)
    session_store.put(context.session_id, trip_plan, context)
    return response


def get_plan(session_id: str) -> PlanResponse | None:
    stored = session_store.get(session_id)
    if stored is None:
        return None
    return _to_response(stored.trip_plan, stored.context)
