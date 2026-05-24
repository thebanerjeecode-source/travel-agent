from __future__ import annotations

from src.context import TripContext
from src.schemas import DayPlan, TripPlan


def _title_from_plan(trip_plan: TripPlan) -> str:
    if trip_plan.requirements and trip_plan.requirements.destinations:
        cities = trip_plan.requirements.destinations
        if len(cities) == 1:
            return f"{cities[0]} Trip Itinerary"
        region = cities[0] if _looks_like_country_trip(cities) else " & ".join(cities)
        if len(cities) >= 2 and _is_japan_trip(cities):
            return "Japan Trip Itinerary"
        return f"{region} Trip Itinerary"
    return "Trip Itinerary"


def _looks_like_country_trip(cities: list[str]) -> bool:
    return len(cities) > 2


def _is_japan_trip(cities: list[str]) -> bool:
    japan_cities = {"tokyo", "kyoto", "osaka", "nara", "hiroshima", "sapporo"}
    return all(c.lower() in japan_cities or c.lower() == "japan" for c in cities)


def _format_activities(day: DayPlan) -> str:
    if not day.activities:
        return "_No activities scheduled yet._"
    parts = []
    for act in day.activities:
        label = act.time.replace("_", " ").capitalize() if act.time else "Activity"
        parts.append(f"{label}: {act.name} ({act.duration_hours:g}h)")
    return ", ".join(parts)


def _logistics_for_day(day: DayPlan, trip_plan: TripPlan) -> str | None:
    if not trip_plan.logistics:
        return None
    legs = []
    for leg in trip_plan.logistics.inter_city:
        if leg.suggested_day == day.day:
            legs.append(
                f"Take the {leg.mode} from {leg.from_city} to {leg.to_city} "
                f"(~{leg.duration_hours:g}h, ~${leg.estimated_cost_usd:,.0f})"
            )
    if legs:
        return " ".join(legs)
    if day.day == 1 and trip_plan.logistics.local_transit_notes:
        return trip_plan.logistics.local_transit_notes
    return None


def _crowd_tips(day: DayPlan, trip_plan: TripPlan) -> str | None:
    dislikes = []
    if trip_plan.requirements:
        dislikes = [d.lower() for d in trip_plan.requirements.dislikes]
    if "crowd" not in " ".join(dislikes):
        return None

    tips = []
    crowded_spots = {"shibuya", "senso-ji", "fushimi inari", "kiyomizu", "tsukiji", "market"}
    for act in day.activities:
        name_lower = act.name.lower()
        if any(spot in name_lower for spot in crowded_spots):
            if "early" in act.time.lower() or "morning" in act.time.lower():
                label = act.name if name_lower.startswith("visit ") else f"Visit {act.name}"
                tips.append(f"{label} early to avoid peak crowds.")
            elif "shibuya" in name_lower:
                tips.append("Avoid Shibuya Crossing during evening rush hour.")
            elif "market" in name_lower:
                tips.append("Visit the market on a weekday morning for fewer crowds.")
            else:
                tips.append(f"Schedule {act.name} at off-peak hours.")
    if not tips:
        tips.append("Prefer early mornings or late afternoons for popular sights.")
    return " ".join(dict.fromkeys(tips))


def render_trip_markdown(trip_plan: TripPlan, context: TripContext) -> str:
    lines: list[str] = []
    title = _title_from_plan(trip_plan)
    lines.append(f"# {title}")
    lines.append("")
    lines.append(f"`{context.session_id}`")
    lines.append("")

    if trip_plan.status == "failed":
        lines.append("## Error")
        lines.append("")
        lines.append(trip_plan.summary)
        return "\n".join(lines) + "\n"

    if trip_plan.status == "requirements_only" and trip_plan.requirements:
        req = trip_plan.requirements
        lines.append("## Trip brief")
        lines.append("")
        lines.append(f"**Summary:** {trip_plan.summary}")
        lines.append("")
        lines.append(f"- **Duration:** {req.duration_days} days")
        lines.append(f"- **Destinations:** {', '.join(req.destinations)}")
        lines.append(f"- **Budget:** ${req.budget_usd:,.0f} USD")
        lines.append(f"- **Travel style:** {req.travel_style.value}")
        lines.append(f"- **Party size:** {req.party_size}")
        if req.interests:
            lines.append(f"- **Interests:** {', '.join(req.interests)}")
        if req.dislikes:
            lines.append(f"- **Dislikes:** {', '.join(req.dislikes)}")
        if req.assumptions:
            lines.append("")
            lines.append("**Assumptions:**")
            for assumption in req.assumptions:
                lines.append(f"- {assumption.reason}")
        lines.append("")
        lines.append("## Original request")
        lines.append("")
        lines.append(f"> {context.raw_request}")
        lines.append("")
        lines.append("---")
        lines.append("")
        lines.append(
            "_Phase 1 complete — requirements parsed. "
            "Day-by-day itinerary, lodging, and logistics will appear here after Phase 2._"
        )
        return "\n".join(lines) + "\n"

    if trip_plan.day_by_day:
        lines.append("## Day-by-day itinerary")
        lines.append("")
        for day in trip_plan.day_by_day:
            lines.append(f"### Day {day.day} — {day.city}: {day.theme}")
            lines.append("")
            lines.append(f"**Activities:** {_format_activities(day)}")
            logistics = _logistics_for_day(day, trip_plan)
            if logistics:
                lines.append("")
                lines.append(f"**Logistics:** {logistics}")
            crowd = _crowd_tips(day, trip_plan)
            if crowd:
                lines.append("")
                lines.append(f"**Crowd tips:** {crowd}")
            lines.append("")

    if trip_plan.neighborhoods_to_stay:
        lines.append("## Where to stay")
        lines.append("")
        for stay in trip_plan.neighborhoods_to_stay:
            lines.append(
                f"- **{stay.city}** ({stay.nights} nights) — "
                f"{stay.recommended_neighborhood}: {stay.reason}"
            )
            for option in stay.options:
                lines.append(
                    f"  - {option.name} (~${option.price_per_night_usd:,.0f}/night, {option.tier})"
                )
        lines.append("")

    if trip_plan.logistics and trip_plan.logistics.local_transit_notes:
        lines.append("## Local transit")
        lines.append("")
        lines.append(trip_plan.logistics.local_transit_notes)
        lines.append("")

    if trip_plan.budget:
        b = trip_plan.budget
        lines.append("## Budget")
        lines.append("")
        lines.append(
            f"**Estimated total:** ${b.estimated_total_usd:,.0f} / ${b.budget_usd:,.0f} "
            f"({b.status.value.replace('_', ' ')})"
        )
        if b.breakdown:
            lines.append("")
            for key, value in b.breakdown.items():
                lines.append(f"- **{key.replace('_', ' ').title()}:** ${value:,.0f}")
        lines.append("")

    if trip_plan.validation_passed:
        lines.append("---")
        lines.append("")
        lines.append("✅ **Validation passed** — plan matches your request.")
        lines.append("")
    elif trip_plan.day_by_day and not trip_plan.budget:
        lines.append("---")
        lines.append("")
        lines.append(
            "_Budget breakdown and validation will be added in Phase 3._"
        )
        lines.append("")

    if trip_plan.data_provenance:
        lines.append("## Data sources")
        lines.append("")
        for domain, source in trip_plan.data_provenance.items():
            lines.append(f"- **{domain.title()}:** {source}")
        lines.append("")

    return "\n".join(lines) + "\n"
