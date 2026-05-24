from src.context import TripContext
from src.stub_data import stub_budget, stub_day_plans, stub_requirements


class TestTripContext:
    def test_add_trace(self):
        ctx = TripContext(raw_request="test")
        ctx.add_trace(1, "intent_parser", "groq", "llama-3.3-70b-versatile", "parsed request")
        assert len(ctx.trace) == 1
        assert ctx.trace[0].provider == "groq"
        assert ctx.trace[0].model == "llama-3.3-70b-versatile"

    def test_to_trip_plan(self):
        ctx = TripContext(raw_request="Japan trip")
        ctx.requirements = stub_requirements()
        ctx.day_plans = stub_day_plans()
        ctx.budget = stub_budget()

        plan = ctx.to_trip_plan()
        assert "Tokyo" in plan.summary
        assert len(plan.day_by_day) == 5
        assert plan.budget is not None

    def test_session_id_generated(self):
        ctx1 = TripContext()
        ctx2 = TripContext()
        assert ctx1.session_id != ctx2.session_id
