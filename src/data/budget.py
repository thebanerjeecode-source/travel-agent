from __future__ import annotations

from typing import Optional

from src.context import TripContext
from src.data.base import DataSource, ProviderResult
from src.data.seeds import load_seed_json
from src.schemas import BudgetBreakdown, BudgetStatus, TravelStyle


class BudgetBenchmarksProvider:
    name = "budget_computed"

    def compute(self, context: TripContext) -> Optional[ProviderResult]:
        if not context.requirements:
            return None

        food_seed = load_seed_json("budget", "daily_food_usd")
        rules_seed = load_seed_json("budget", "allocation_rules")
        if not food_seed and not context.accommodation:
            return None

        req = context.requirements
        tier = req.travel_style.value

        lodging = 0.0
        for plan in context.accommodation:
            if plan.options:
                lodging += plan.options[0].price_per_night_usd * plan.nights

        transport = 0.0
        if context.transport:
            transport = sum(leg.estimated_cost_usd for leg in context.transport.inter_city)
            transport += 12.0 * req.duration_days  # local transit estimate

        food = 0.0
        city_nights = _nights_per_city(context)
        for city, nights in city_nights.items():
            daily = _daily_food_usd(city, tier, food_seed)
            food += daily * nights * req.party_size

        activities = 0.0
        for day in context.day_plans:
            for act in day.activities:
                activities += _activity_cost(act.name, context)

        estimated = lodging + transport + food + activities
        buffer = req.budget_usd - estimated
        status = BudgetStatus.WITHIN_BUDGET if estimated <= req.budget_usd else BudgetStatus.OVER_BUDGET

        suggestions: list[str] = []
        if status == BudgetStatus.OVER_BUDGET:
            suggestions = _savings_suggestions(lodging, transport, food, rules_seed)

        breakdown = BudgetBreakdown(
            budget_usd=req.budget_usd,
            estimated_total_usd=round(estimated, 2),
            breakdown={
                "lodging": round(lodging, 2),
                "transport": round(transport, 2),
                "food": round(food, 2),
                "activities": round(activities, 2),
                "buffer": round(buffer, 2),
            },
            status=status,
            savings_suggestions=suggestions,
        )

        return ProviderResult(
            data=breakdown,
            source=DataSource(
                domain="budget",
                provider=self.name,
                source="data/seeds/budget/ + agent outputs",
                source_type="computed",
                confidence="high" if context.accommodation and context.transport else "medium",
            ),
        )


def _nights_per_city(context: TripContext) -> dict[str, int]:
    if context.accommodation:
        return {a.city: a.nights for a in context.accommodation}
    nights: dict[str, int] = {}
    for day in context.day_plans:
        nights[day.city] = nights.get(day.city, 0) + 1
    return nights


def _daily_food_usd(city: str, tier: str, food_seed: dict | None) -> float:
    defaults = {"budget": 30, "mid-range": 55, "luxury": 100}
    if not food_seed:
        return defaults.get(tier, 55)
    city_data = food_seed.get(city) or food_seed.get(city.lower())
    if isinstance(city_data, dict):
        return float(city_data.get(tier, defaults.get(tier, 55)))
    return defaults.get(tier, 55)


def _activity_cost(activity_name: str, context: TripContext) -> float:
    name_lower = activity_name.lower()
    for research in context.destination_research:
        for attr in research.attractions:
            if attr.name.lower() in name_lower or name_lower in attr.name.lower():
                return attr.estimated_cost_usd
    return 0.0


def _savings_suggestions(
    lodging: float,
    transport: float,
    food: float,
    rules_seed: dict | None,
) -> list[str]:
    tips = []
    if lodging > 400:
        tips.append("Switch to a budget hotel or hostel to reduce lodging costs.")
    if transport > 300:
        tips.append("Book inter-city trains in advance or consider a rail pass.")
    if food > 600:
        tips.append("Mix convenience-store breakfasts with one splurge meal per day.")
    if rules_seed and rules_seed.get("default_savings"):
        tips.extend(rules_seed["default_savings"][:2])
    return tips[:4]
