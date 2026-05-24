from __future__ import annotations

from fastapi import APIRouter, Header, HTTPException, Response

from src.api.config import get_api_secret
from src.api.schemas import PlanRequest, PlanResponse
from src.api.service import create_plan, get_plan
from src.api.session_store import session_store
from src.render.markdown import render_trip_markdown

router = APIRouter(prefix="/api/v1/plans", tags=["plans"])


def _check_api_secret(x_api_secret: str | None) -> None:
    required = get_api_secret()
    if required and x_api_secret != required:
        raise HTTPException(status_code=401, detail="Invalid or missing API secret")


@router.post("", response_model=PlanResponse)
def post_plan(
    body: PlanRequest,
    x_api_secret: str | None = Header(default=None, alias="X-API-Secret"),
) -> PlanResponse:
    _check_api_secret(x_api_secret)
    return create_plan(body)


@router.get("/{session_id}", response_model=PlanResponse)
def fetch_plan(session_id: str) -> PlanResponse:
    response = get_plan(session_id)
    if response is None:
        raise HTTPException(status_code=404, detail="Plan not found")
    return response


@router.get("/{session_id}/markdown")
def fetch_plan_markdown(session_id: str) -> Response:
    stored = session_store.get(session_id)
    if stored is None:
        raise HTTPException(status_code=404, detail="Plan not found")
    content = render_trip_markdown(stored.trip_plan, stored.context)
    return Response(
        content=content,
        media_type="text/markdown; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="trip-{session_id[:8]}.md"'},
    )
