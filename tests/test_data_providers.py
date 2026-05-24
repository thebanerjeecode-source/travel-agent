from src.context import TripContext
from src.data.base import DataMode
from src.data.registry import DataRegistry, build_data_registry
from src.schemas import TravelStyle
from src.stub_data import stub_accommodation, stub_day_plans, stub_requirements


class TestDataProviders:
    def test_seed_destination_tokyo(self):
        registry = build_data_registry(DataMode.SEED)
        result = registry.fetch_destination("Tokyo", ["food", "temples"])
        assert result is not None
        assert result.data.city == "Tokyo"
        assert len(result.data.attractions) >= 2
        assert result.source.source_type == "seed_file"

    def test_seed_accommodation_filters_by_tier(self):
        registry = build_data_registry(DataMode.SEED)
        result = registry.fetch_accommodation(
            city="Tokyo",
            nights=3,
            travel_style=TravelStyle.MID_RANGE,
            budget_usd=3000,
            duration_days=5,
        )
        assert result is not None
        assert result.data.nights == 3
        assert all(o.tier == "mid-range" for o in result.data.options)

    def test_seed_transport_tokyo_kyoto(self):
        registry = build_data_registry(DataMode.SEED)
        context = TripContext()
        context.requirements = stub_requirements()
        context.day_plans = stub_day_plans()
        result = registry.fetch_transport(context)
        assert result is not None
        assert len(result.data.inter_city) == 1
        assert result.data.inter_city[0].mode == "Shinkansen"

    def test_computed_budget_from_seeds(self):
        registry = build_data_registry(DataMode.SEED)
        context = TripContext()
        context.requirements = stub_requirements()
        context.day_plans = stub_day_plans()
        context.accommodation = stub_accommodation()
        context.transport = registry.fetch_transport(context).data  # type: ignore[union-attr]
        result = registry.compute_budget(context)
        assert result is not None
        assert result.data.estimated_total_usd > 0
        assert result.source.source_type == "computed"
        assert result.data.budget_usd == 3000

    def test_provenance_summary(self):
        registry = build_data_registry(DataMode.SEED)
        registry.fetch_destination("Tokyo", ["food"])
        registry.fetch_destination("Kyoto", ["temples"])
        summary = registry.provenance_summary()
        assert "destination" in summary

    def test_unknown_city_returns_none(self):
        registry = build_data_registry(DataMode.SEED)
        result = registry.fetch_destination("Jaipur", ["forts"])
        assert result is None
