import pytest
from pydantic import ValidationError

from src.schemas import (
    AccommodationPlan,
    BudgetBreakdown,
    BudgetStatus,
    DayPlan,
    DestinationResearch,
    InterCityLeg,
    TransportPlan,
    TravelRequirements,
    TravelStyle,
    TripPlan,
    ValidationReport,
)
from src.stub_data import (
    stub_accommodation,
    stub_budget,
    stub_day_plans,
    stub_destination_research,
    stub_requirements,
    stub_transport,
    stub_validation,
)


class TestTravelRequirements:
    def test_valid_requirements(self):
        req = stub_requirements()
        assert req.duration_days == 5
        assert "Tokyo" in req.destinations
        assert req.budget_usd == 3000

    def test_rejects_empty_destinations(self):
        with pytest.raises(ValidationError):
            TravelRequirements(
                duration_days=5,
                destinations=[],
                budget_usd=1000,
            )


class TestDestinationResearch:
    def test_valid_destination(self):
        research = stub_destination_research()
        assert len(research) == 2
        assert research[0].city == "Tokyo"


class TestDayPlan:
    def test_valid_day_plans(self):
        plans = stub_day_plans()
        assert len(plans) == 5
        assert plans[0].day == 1


class TestTransportPlan:
    def test_inter_city_leg_aliases(self):
        transport = stub_transport()
        leg = transport.inter_city[0]
        assert leg.from_city == "Tokyo"
        assert leg.to_city == "Kyoto"

    def test_from_alias_in_model_validate(self):
        leg = InterCityLeg.model_validate(
            {
                "from": "Delhi",
                "to": "Jaipur",
                "mode": "train",
                "duration_hours": 4.5,
                "estimated_cost_usd": 20,
                "suggested_day": 2,
            }
        )
        assert leg.from_city == "Delhi"


class TestBudgetBreakdown:
    def test_valid_budget(self):
        budget = stub_budget()
        assert budget.status == BudgetStatus.WITHIN_BUDGET
        assert budget.estimated_total_usd <= budget.budget_usd


class TestTripPlan:
    def test_minimal_trip_plan(self):
        plan = TripPlan(summary="Test trip", validation_passed=True, status="complete")
        assert plan.summary == "Test trip"


class TestAllStubArtifactsValidate:
    @pytest.mark.parametrize(
        "factory",
        [
            stub_requirements,
            stub_destination_research,
            stub_day_plans,
            stub_accommodation,
            stub_transport,
            stub_budget,
            stub_validation,
        ],
    )
    def test_stub_factories_produce_valid_models(self, factory):
        result = factory()
        if isinstance(result, list):
            assert len(result) > 0
        else:
            assert result is not None
