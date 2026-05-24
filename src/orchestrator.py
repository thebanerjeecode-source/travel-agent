from __future__ import annotations

import structlog

from src.agents import (
    AccommodationAgent,
    BudgetAnalystAgent,
    BaseAgent,
    DestinationResearchAgent,
    IntentParserAgent,
    ItineraryBuilderAgent,
    LogisticsAgent,
    ValidatorAgent,
)
from src.context import TripContext
from src.data.registry import build_data_registry
from src.llm.rate_limiter import RateLimiter
from src.llm.types import ModelProvider
from src.schemas import BudgetStatus, TripPlan

logger = structlog.get_logger()

# Phase 0: full stub pipeline (no API calls)
PHASE_STUB = 0
# Phase 1: live Intent Parser only; requirements-only output
PHASE_INTENT = 1
# Phase 2: Intent + planning agents (Groq); no budget/validation yet
PHASE_PLANNING = 2
# Phase 3: full pipeline with live budget + validator
PHASE_FULL = 3

MAX_AGENT_CALLS = 12
MAX_BUDGET_REVISIONS = 1
MAX_VALIDATION_REVISIONS = 1
GEMINI_RPD_WARN_RATIO = 0.8


class Orchestrator:
    def __init__(
        self,
        phase: int = PHASE_FULL,
        agents: list[BaseAgent] | None = None,
        data_mode: str | None = None,
    ) -> None:
        self.phase = phase
        use_stub = phase == PHASE_STUB
        self.data_registry = (
            build_data_registry(data_mode)
            if phase not in (PHASE_STUB, PHASE_INTENT)
            else None
        )
        data_kw = {"data_registry": self.data_registry}

        self.intent_agent = IntentParserAgent(use_stub=use_stub)
        self.planning_agents: list[BaseAgent] = [
            DestinationResearchAgent(use_stub=use_stub, **data_kw),
            ItineraryBuilderAgent(use_stub=use_stub),
            AccommodationAgent(use_stub=use_stub, **data_kw),
            LogisticsAgent(use_stub=use_stub, **data_kw),
        ]
        self.budget_agent = BudgetAnalystAgent(use_stub=use_stub, **data_kw)
        self.validator_agent = ValidatorAgent(use_stub=use_stub)
        self.review_agents: list[BaseAgent] = [
            self.budget_agent,
            self.validator_agent,
        ]
        self.downstream_agents: list[BaseAgent] = self.planning_agents + self.review_agents

        self._agent_by_name: dict[str, BaseAgent] = {
            "intent_parser": self.intent_agent,
            "destination_research": self.planning_agents[0],
            "itinerary_builder": self.planning_agents[1],
            "accommodation": self.planning_agents[2],
            "logistics": self.planning_agents[3],
            "budget_analyst": self.budget_agent,
            "validator": self.validator_agent,
        }

        if agents is not None:
            self.agents = agents
        elif phase == PHASE_STUB:
            self.agents = [self.intent_agent] + self.downstream_agents
        elif phase == PHASE_INTENT:
            self.agents = [self.intent_agent]
        elif phase == PHASE_PLANNING:
            self.agents = [self.intent_agent] + self.planning_agents
        else:
            self.agents = [self.intent_agent] + self.downstream_agents

    def run(self, raw_request: str) -> tuple[TripPlan, TripContext]:
        context = TripContext(raw_request=raw_request)

        if not raw_request.strip():
            context.status = "failed"
            context.error_message = (
                "Please describe your trip, e.g. "
                "'Plan a 5-day trip to Tokyo and Kyoto with a $3,000 budget.'"
            )
            return context.to_trip_plan(), context

        logger.info(
            "orchestrator_start",
            session_id=context.session_id,
            phase=self.phase,
            request=raw_request[:80],
        )

        if self.phase == PHASE_STUB:
            return self._run_full_stub(context)
        if self.phase == PHASE_INTENT:
            return self._run_intent_only(context)
        if self.phase == PHASE_PLANNING:
            return self._run_planning(context)

        return self._run_full(context)

    def _run_intent_only(self, context: TripContext) -> tuple[TripPlan, TripContext]:
        context = self.intent_agent.run(context, step=1)

        if context.status == "failed":
            logger.info("orchestrator_failed", reason=context.error_message)
            return context.to_trip_plan(), context

        context.status = "complete"
        trip_plan = context.to_trip_plan(requirements_only=True)

        logger.info(
            "orchestrator_complete",
            session_id=context.session_id,
            phase=PHASE_INTENT,
            destinations=context.requirements.destinations if context.requirements else [],
        )
        return trip_plan, context

    def _run_planning(self, context: TripContext) -> tuple[TripPlan, TripContext]:
        context = self.intent_agent.run(context, step=1)

        if context.status == "failed":
            logger.info("orchestrator_failed", reason=context.error_message)
            return context.to_trip_plan(), context

        step = 2
        for agent in self.planning_agents:
            context = agent.run(context, step)
            step += 1

        context.status = "complete"
        trip_plan = context.to_trip_plan()

        logger.info(
            "orchestrator_complete",
            session_id=context.session_id,
            phase=PHASE_PLANNING,
            days=len(context.day_plans),
            destinations=context.requirements.destinations if context.requirements else [],
        )
        return trip_plan, context

    def _run_full(self, context: TripContext) -> tuple[TripPlan, TripContext]:
        step = 1
        agent_calls = 0
        budget_revisions = 0
        validation_revisions = 0

        context = self.intent_agent.run(context, step)
        agent_calls += 1
        step += 1

        if context.status == "failed":
            logger.info("orchestrator_failed", reason=context.error_message)
            return context.to_trip_plan(), context

        for agent in self.planning_agents:
            if agent_calls >= MAX_AGENT_CALLS:
                break
            context = agent.run(context, step)
            agent_calls += 1
            step += 1

        while agent_calls < MAX_AGENT_CALLS:
            context = self.budget_agent.run(context, step)
            agent_calls += 1
            step += 1

            over_budget = (
                context.budget is not None
                and context.budget.status == BudgetStatus.OVER_BUDGET
            )
            if over_budget and budget_revisions < MAX_BUDGET_REVISIONS:
                budget_revisions += 1
                context.revision_count += 1
                context.revision_hints = list(context.budget.savings_suggestions)
                if agent_calls >= MAX_AGENT_CALLS:
                    break
                context = self.planning_agents[2].run(context, step)  # accommodation
                agent_calls += 1
                step += 1
                continue

            break

        if agent_calls < MAX_AGENT_CALLS:
            context = self.validator_agent.run(context, step)
            agent_calls += 1
            step += 1

        while (
            context.validation
            and not context.validation.passed
            and validation_revisions < MAX_VALIDATION_REVISIONS
            and agent_calls < MAX_AGENT_CALLS
        ):
            validation_revisions += 1
            context.revision_count += 1
            errors = [i for i in context.validation.issues if i.severity == "error"]
            context.revision_hints = [i.message for i in errors]

            target_name = "itinerary_builder"
            if errors and errors[0].suggested_agent:
                target_name = errors[0].suggested_agent

            target = self._agent_by_name.get(target_name, self.planning_agents[1])
            context = target.run(context, step)
            agent_calls += 1
            step += 1

            if target_name == "itinerary_builder" and agent_calls < MAX_AGENT_CALLS:
                context = self.planning_agents[3].run(context, step)  # logistics
                agent_calls += 1
                step += 1

            if agent_calls < MAX_AGENT_CALLS:
                context = self.budget_agent.run(context, step)
                agent_calls += 1
                step += 1

            if agent_calls < MAX_AGENT_CALLS:
                context = self.validator_agent.run(context, step)
                agent_calls += 1
                step += 1

        context.status = "complete"
        trip_plan = context.to_trip_plan()

        self._log_quota_warnings()

        logger.info(
            "orchestrator_complete",
            session_id=context.session_id,
            phase=PHASE_FULL,
            agents_run=agent_calls,
            validation_passed=trip_plan.validation_passed,
            budget_revisions=budget_revisions,
            validation_revisions=validation_revisions,
        )
        return trip_plan, context

    def _run_full_stub(self, context: TripContext) -> tuple[TripPlan, TripContext]:
        for step, agent in enumerate(self.agents, start=1):
            context = agent.run(context, step)

        context.status = "complete"
        trip_plan = context.to_trip_plan()

        logger.info(
            "orchestrator_complete",
            session_id=context.session_id,
            phase=PHASE_STUB,
            agents_run=len(self.agents),
            validation_passed=trip_plan.validation_passed,
        )
        return trip_plan, context

    def _log_quota_warnings(self) -> None:
        gemini = RateLimiter.get().usage(ModelProvider.GEMINI)
        if gemini.rpd_used >= gemini.rpd_limit * GEMINI_RPD_WARN_RATIO:
            logger.warning(
                "gemini_quota_high",
                usage=gemini.summary(),
                message=(
                    f"Gemini daily quota at {gemini.rpd_used}/{gemini.rpd_limit} RPD "
                    f"(≥{int(GEMINI_RPD_WARN_RATIO * 100)}%). Consider --stub or --planning-only."
                ),
            )
