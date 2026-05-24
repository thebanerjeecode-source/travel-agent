from __future__ import annotations

from typing import Optional

from src.data.base import DataSource, ProviderResult
from src.data.seeds import load_category_file
from src.schemas import DayPlan, InterCityLeg, TransportPlan


def _city_transition_day(day_plans: list[DayPlan], to_city: str) -> int:
    for day in day_plans:
        if day.city.lower() == to_city.lower():
            return day.day
    return 1


def _ordered_cities(day_plans: list[DayPlan], cities: list[str]) -> list[str]:
    if day_plans:
        seen: list[str] = []
        for day in sorted(day_plans, key=lambda d: d.day):
            if not seen or seen[-1].lower() != day.city.lower():
                seen.append(day.city)
        return seen
    return cities


class SeedTransportProvider:
    name = "transport_seed"

    def fetch(self, *, day_plans: list[DayPlan], cities: list[str]) -> Optional[ProviderResult]:
        routes_seed = load_category_file("transport", "routes.json")
        local_seed = load_category_file("transport", "local_transit.json") or {}

        if not routes_seed:
            return None

        ordered = _ordered_cities(day_plans, cities)
        inter_city: list[InterCityLeg] = []
        routes = routes_seed.get("routes", [])

        for i in range(len(ordered) - 1):
            from_city, to_city = ordered[i], ordered[i + 1]
            match = next(
                (
                    r
                    for r in routes
                    if r["from"].lower() == from_city.lower() and r["to"].lower() == to_city.lower()
                ),
                None,
            )
            if match:
                inter_city.append(
                    InterCityLeg(
                        **{
                            "from": match["from"],
                            "to": match["to"],
                            "mode": match["mode"],
                            "duration_hours": float(match.get("duration_hours", match.get("duration", 0))),
                            "estimated_cost_usd": float(match.get("cost_usd", match.get("estimated_cost_usd", 0))),
                            "suggested_day": _city_transition_day(day_plans, to_city),
                        }
                    )
                )

        notes_parts = []
        for city in ordered:
            tips = local_seed.get(city) or local_seed.get(city.lower())
            if isinstance(tips, str):
                notes_parts.append(tips)

        transport = TransportPlan(
            inter_city=inter_city,
            local_transit_notes=" ".join(n for n in notes_parts if n).strip(),
        )

        if not inter_city and not transport.local_transit_notes:
            return None

        return ProviderResult(
            data=transport,
            source=DataSource(
                domain="transport",
                provider=self.name,
                source="data/seeds/transport/routes.json",
                source_type="seed_file",
                confidence="medium",
            ),
        )
