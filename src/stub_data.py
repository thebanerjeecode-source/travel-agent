"""Placeholder stub data for Phase 0 pipeline (Japan canonical example)."""

from src.schemas import (
    AccommodationOption,
    AccommodationPlan,
    Activity,
    Attraction,
    BudgetBreakdown,
    BudgetStatus,
    DayPlan,
    DestinationResearch,
    InterCityLeg,
    Neighborhood,
    TransportPlan,
    TravelRequirements,
    TravelStyle,
    ValidationReport,
)


def stub_requirements() -> TravelRequirements:
    return TravelRequirements(
        duration_days=5,
        destinations=["Tokyo", "Kyoto"],
        budget_usd=3000,
        interests=["food", "temples"],
        dislikes=["crowds"],
        travel_style=TravelStyle.MID_RANGE,
        party_size=1,
    )


def stub_destination_research() -> list[DestinationResearch]:
    return [
        DestinationResearch(
            city="Tokyo",
            neighborhoods=[
                Neighborhood(name="Shinjuku", fit_score=0.85, reason="Transit hub, food variety"),
            ],
            attractions=[
                Attraction(
                    name="Senso-ji",
                    category="temple",
                    crowd_level="high",
                    best_time="early morning",
                ),
                Attraction(name="Tsukiji Outer Market", category="food", crowd_level="medium"),
            ],
            food_highlights=["Ramen in Shinjuku", "Tsukiji Outer Market"],
        ),
        DestinationResearch(
            city="Kyoto",
            neighborhoods=[
                Neighborhood(name="Higashiyama", fit_score=0.9, reason="Temples, walkable, traditional"),
            ],
            attractions=[
                Attraction(
                    name="Fushimi Inari",
                    category="temple",
                    crowd_level="high",
                    best_time="early morning",
                ),
            ],
            food_highlights=["Nishiki Market", "kaiseki in Gion"],
        ),
    ]


def stub_day_plans() -> list[DayPlan]:
    return [
        DayPlan(
            day=1,
            city="Tokyo",
            theme="Arrival & Shibuya",
            activities=[
                Activity(time="afternoon", name="Shibuya Crossing", duration_hours=1),
                Activity(time="evening", name="Ramen in Shinjuku", duration_hours=2),
            ],
        ),
        DayPlan(
            day=2,
            city="Tokyo",
            theme="Temples & markets",
            activities=[
                Activity(time="early morning", name="Senso-ji", duration_hours=2),
                Activity(time="afternoon", name="Tsukiji Outer Market", duration_hours=2),
            ],
        ),
        DayPlan(day=3, city="Tokyo", theme="Explore Tokyo", activities=[]),
        DayPlan(
            day=4,
            city="Kyoto",
            theme="Travel to Kyoto & Fushimi Inari",
            activities=[
                Activity(time="early morning", name="Fushimi Inari", duration_hours=3),
            ],
        ),
        DayPlan(
            day=5,
            city="Kyoto",
            theme="Kyoto temples & departure",
            activities=[
                Activity(time="morning", name="Kiyomizu-dera", duration_hours=2),
            ],
        ),
    ]


def stub_accommodation() -> list[AccommodationPlan]:
    return [
        AccommodationPlan(
            city="Tokyo",
            nights=3,
            recommended_neighborhood="Shinjuku",
            reason="Central transit hub, good food, fits mid-range budget",
            options=[
                AccommodationOption(
                    name="Hotel Gracery Shinjuku",
                    price_per_night_usd=120,
                    tier="mid-range",
                ),
            ],
        ),
        AccommodationPlan(
            city="Kyoto",
            nights=2,
            recommended_neighborhood="Higashiyama",
            reason="Walkable temple district, traditional atmosphere",
            options=[
                AccommodationOption(
                    name="Hotel The Celestine Kyoto Gion",
                    price_per_night_usd=110,
                    tier="mid-range",
                ),
            ],
        ),
    ]


def stub_transport() -> TransportPlan:
    return TransportPlan(
        inter_city=[
            InterCityLeg(
                **{
                    "from": "Tokyo",
                    "to": "Kyoto",
                    "mode": "Shinkansen",
                    "duration_hours": 2.5,
                    "estimated_cost_usd": 120,
                    "suggested_day": 4,
                }
            )
        ],
        local_transit_notes="Get a Suica/PASMO card in Tokyo; Kyoto bus day pass recommended",
    )


def stub_budget() -> BudgetBreakdown:
    return BudgetBreakdown(
        budget_usd=3000,
        estimated_total_usd=2750,
        breakdown={
            "lodging": 580,
            "transport": 350,
            "food": 900,
            "activities": 340,
            "buffer": 580,
        },
        status=BudgetStatus.WITHIN_BUDGET,
        savings_suggestions=[],
    )


def stub_validation() -> ValidationReport:
    return ValidationReport(passed=True, issues=[])
