from __future__ import annotations

from src.context import TripContext
from src.render.markdown import (
    _crowd_tips,
    _format_activities,
    _logistics_for_day,
    _title_from_plan,
)
from src.schemas import TripPlan


def _line(char: str = "─", width: int = 60) -> str:
    return char * width


def render_trip_terminal(trip_plan: TripPlan, context: TripContext) -> str:
    """Plain-text trip plan for terminal output (non-technical readers)."""
    lines: list[str] = []
    title = _title_from_plan(trip_plan)

    lines.append(_line("═"))
    lines.append(title.center(60))
    lines.append(_line("═"))
    lines.append("")

    if trip_plan.status == "failed":
        lines.append("Could not process your request:")
        lines.append(f"  {trip_plan.summary}")
        lines.append("")
        lines.append("Try something like:")
        lines.append('  "Plan a 5-day trip to Tokyo and Kyoto with a $3,000 budget."')
        return "\n".join(lines) + "\n"

    if trip_plan.requirements:
        req = trip_plan.requirements
        lines.append(f"Summary: {trip_plan.summary}")
        lines.append(f"  {req.duration_days} days  ·  {', '.join(req.destinations)}  ·  ${req.budget_usd:,.0f} budget")
        if req.interests:
            lines.append(f"  Interests: {', '.join(req.interests)}")
        if req.dislikes:
            lines.append(f"  Avoid: {', '.join(req.dislikes)}")
        lines.append("")

    if trip_plan.status == "requirements_only":
        lines.append("Trip brief parsed. Run without --intent-only for full itinerary.")
        if trip_plan.requirements and trip_plan.requirements.assumptions:
            lines.append("")
            lines.append("Assumptions:")
            for a in trip_plan.requirements.assumptions:
                lines.append(f"  • {a.reason}")
        return "\n".join(lines) + "\n"

    if trip_plan.day_by_day:
        lines.append(_line())
        lines.append("DAY-BY-DAY ITINERARY")
        lines.append(_line())
        for day in trip_plan.day_by_day:
            lines.append("")
            lines.append(f"Day {day.day} — {day.city}: {day.theme}")
            lines.append(f"  Activities: {_format_activities(day).replace('_', '')}")
            logistics = _logistics_for_day(day, trip_plan)
            if logistics:
                lines.append(f"  Logistics: {logistics}")
            crowd = _crowd_tips(day, trip_plan)
            if crowd:
                lines.append(f"  Crowd tips: {crowd}")

    if trip_plan.neighborhoods_to_stay:
        lines.append("")
        lines.append(_line())
        lines.append("WHERE TO STAY")
        lines.append(_line())
        for stay in trip_plan.neighborhoods_to_stay:
            lines.append(f"\n  {stay.city} ({stay.nights} nights) — {stay.recommended_neighborhood}")
            lines.append(f"  {stay.reason}")
            for opt in stay.options:
                lines.append(f"    • {opt.name} (~${opt.price_per_night_usd:,.0f}/night, {opt.tier})")

    if trip_plan.logistics and trip_plan.logistics.local_transit_notes:
        lines.append("")
        lines.append(_line())
        lines.append("LOCAL TRANSIT")
        lines.append(_line())
        lines.append(f"  {trip_plan.logistics.local_transit_notes}")

    if trip_plan.budget:
        b = trip_plan.budget
        lines.append("")
        lines.append(_line())
        lines.append("BUDGET")
        lines.append(_line())
        status = b.status.value.replace("_", " ")
        lines.append(f"  Estimated: ${b.estimated_total_usd:,.0f} / ${b.budget_usd:,.0f} ({status})")
        if b.breakdown:
            for key, value in b.breakdown.items():
                lines.append(f"    {key.replace('_', ' ').title():12} ${value:,.0f}")
        if b.savings_suggestions:
            lines.append("  Savings tips:")
            for tip in b.savings_suggestions:
                lines.append(f"    • {tip}")

    lines.append("")
    if trip_plan.validation_passed:
        lines.append("✓ Validation passed — plan matches your request.")
    elif trip_plan.day_by_day and not trip_plan.budget:
        lines.append("○ Budget and validation pending (use full pipeline).")

    if trip_plan.data_provenance:
        lines.append("")
        lines.append(f"Data: {', '.join(f'{k}={v}' for k, v in trip_plan.data_provenance.items())}")

    lines.append("")
    lines.append(f"Run ID: {context.session_id}")
    lines.append("")
    return "\n".join(lines)
