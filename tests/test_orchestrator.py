from src.agents import (
    AccommodationAgent,
    BudgetAnalystAgent,
    DestinationResearchAgent,
    IntentParserAgent,
    ItineraryBuilderAgent,
    LogisticsAgent,
    ValidatorAgent,
)
from src.orchestrator import PHASE_FULL, PHASE_INTENT, PHASE_PLANNING, PHASE_STUB, Orchestrator

JAPAN_REQUEST = (
    "Plan a 5-day trip to Japan. Tokyo + Kyoto. $3,000 budget. "
    "Love food and temples, hate crowds."
)


class TestOrchestratorStubPipeline:
    """Phase 0 — full stub pipeline, no API calls."""

    def test_runs_all_agents_end_to_end(self):
        orchestrator = Orchestrator(phase=PHASE_STUB)
        trip_plan, context = orchestrator.run(JAPAN_REQUEST)

        assert context.status == "complete"
        assert len(context.trace) == 7
        assert trip_plan.validation_passed is True
        assert len(trip_plan.day_by_day) == 5

    def test_trace_includes_provider_and_model(self):
        _, context = Orchestrator(phase=PHASE_STUB).run(JAPAN_REQUEST)

        groq_entry = context.trace[0]
        assert groq_entry.provider == "groq"
        assert groq_entry.model == "llama-3.3-70b-versatile"

        gemini_entry = next(e for e in context.trace if e.agent == "budget_analyst")
        assert gemini_entry.provider == "gemini"
        assert gemini_entry.model == "gemini-2.5-flash"

    def test_agent_order(self):
        _, context = Orchestrator(phase=PHASE_STUB).run(JAPAN_REQUEST)
        agents = [e.agent for e in context.trace]
        assert agents == [
            "intent_parser",
            "destination_research",
            "itinerary_builder",
            "accommodation",
            "logistics",
            "budget_analyst",
            "validator",
        ]

    def test_trip_plan_has_required_deliverables(self):
        trip_plan, _ = Orchestrator(phase=PHASE_STUB).run(JAPAN_REQUEST)

        assert trip_plan.summary
        assert trip_plan.requirements is not None
        assert len(trip_plan.neighborhoods_to_stay) >= 2
        assert trip_plan.logistics is not None
        assert len(trip_plan.logistics.inter_city) >= 1
        assert trip_plan.budget is not None

    def test_stores_raw_request(self):
        _, context = Orchestrator(phase=PHASE_STUB).run(JAPAN_REQUEST)
        assert context.raw_request == JAPAN_REQUEST


class TestOrchestratorPhase1:
    """Phase 1 — intent-only routing (stub intent to avoid API in tests)."""

    def _intent_only_orchestrator(self) -> Orchestrator:
        orchestrator = Orchestrator(phase=PHASE_INTENT)
        orchestrator.intent_agent = IntentParserAgent(use_stub=True)
        orchestrator.agents = [orchestrator.intent_agent]
        return orchestrator

    def test_intent_only_returns_requirements_only(self):
        trip_plan, context = self._intent_only_orchestrator().run(JAPAN_REQUEST)

        assert context.status == "complete"
        assert len(context.trace) == 1
        assert trip_plan.status == "requirements_only"
        assert trip_plan.requirements is not None
        assert trip_plan.requirements.duration_days == 5
        assert "Tokyo" in trip_plan.requirements.destinations

    def test_empty_request_fails(self):
        trip_plan, context = Orchestrator(phase=PHASE_INTENT).run("   ")

        assert context.status == "failed"
        assert trip_plan.status == "failed"
        assert trip_plan.summary


class TestOrchestratorPhase2:
    """Phase 2 — intent + planning agents (stub to avoid API in tests)."""

    def _planning_orchestrator(self) -> Orchestrator:
        orchestrator = Orchestrator(phase=PHASE_PLANNING)
        orchestrator.intent_agent = IntentParserAgent(use_stub=True)
        orchestrator.planning_agents = [
            DestinationResearchAgent(use_stub=True),
            ItineraryBuilderAgent(use_stub=True),
            AccommodationAgent(use_stub=True),
            LogisticsAgent(use_stub=True),
        ]
        orchestrator.agents = [orchestrator.intent_agent] + orchestrator.planning_agents
        return orchestrator

    def test_runs_five_agents(self):
        _, context = self._planning_orchestrator().run(JAPAN_REQUEST)

        assert context.status == "complete"
        assert len(context.trace) == 5
        assert [e.agent for e in context.trace] == [
            "intent_parser",
            "destination_research",
            "itinerary_builder",
            "accommodation",
            "logistics",
        ]

    def test_produces_day_by_day_plan(self):
        trip_plan, context = self._planning_orchestrator().run(JAPAN_REQUEST)

        assert trip_plan.status == "complete"
        assert len(trip_plan.day_by_day) == 5
        assert len(context.destination_research) == 2
        assert len(trip_plan.neighborhoods_to_stay) == 2
        assert trip_plan.logistics is not None
        assert len(trip_plan.logistics.inter_city) >= 1
        assert trip_plan.budget is None
        assert trip_plan.validation_passed is False

    def test_japan_exit_criteria(self):
        trip_plan, _ = self._planning_orchestrator().run(JAPAN_REQUEST)

        cities = {d.city for d in trip_plan.day_by_day}
        assert "Tokyo" in cities
        assert "Kyoto" in cities

        all_activities = " ".join(
            a.name for d in trip_plan.day_by_day for a in d.activities
        ).lower()
        assert "senso-ji" in all_activities or "fushimi" in all_activities

        shinkansen = trip_plan.logistics.inter_city[0]
        assert shinkansen.mode == "Shinkansen"
        assert shinkansen.from_city == "Tokyo"
        assert shinkansen.to_city == "Kyoto"


class TestOrchestratorPhase3:
    """Phase 3 — full pipeline with budget + validation (stub to avoid API)."""

    def _full_orchestrator(self) -> Orchestrator:
        orchestrator = Orchestrator(phase=PHASE_FULL)
        orchestrator.intent_agent = IntentParserAgent(use_stub=True)
        orchestrator.planning_agents = [
            DestinationResearchAgent(use_stub=True),
            ItineraryBuilderAgent(use_stub=True),
            AccommodationAgent(use_stub=True),
            LogisticsAgent(use_stub=True),
        ]
        orchestrator.budget_agent = BudgetAnalystAgent(use_stub=True)
        orchestrator.validator_agent = ValidatorAgent(use_stub=True)
        orchestrator.review_agents = [orchestrator.budget_agent, orchestrator.validator_agent]
        orchestrator._agent_by_name = {
            "intent_parser": orchestrator.intent_agent,
            "destination_research": orchestrator.planning_agents[0],
            "itinerary_builder": orchestrator.planning_agents[1],
            "accommodation": orchestrator.planning_agents[2],
            "logistics": orchestrator.planning_agents[3],
            "budget_analyst": orchestrator.budget_agent,
            "validator": orchestrator.validator_agent,
        }
        return orchestrator

    def test_runs_seven_agents(self):
        _, context = self._full_orchestrator().run(JAPAN_REQUEST)

        assert context.status == "complete"
        assert len(context.trace) == 7
        assert [e.agent for e in context.trace] == [
            "intent_parser",
            "destination_research",
            "itinerary_builder",
            "accommodation",
            "logistics",
            "budget_analyst",
            "validator",
        ]

    def test_produces_budget_and_validation(self):
        trip_plan, _ = self._full_orchestrator().run(JAPAN_REQUEST)

        assert trip_plan.status == "complete"
        assert trip_plan.budget is not None
        assert trip_plan.budget.status.value == "within_budget"
        assert trip_plan.validation_passed is True
        assert trip_plan.budget.estimated_total_usd <= trip_plan.budget.budget_usd
