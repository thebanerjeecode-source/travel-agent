"""Phase 5 end-to-end tests — stub/dry-run pipeline and CLI."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from src.orchestrator import PHASE_STUB, Orchestrator

ROOT = Path(__file__).resolve().parent.parent

JAPAN_REQUEST = (
    "Plan a 5-day trip to Japan. Tokyo + Kyoto. $3,000 budget. "
    "Love food and temples, hate crowds."
)
JAIPUR_REQUEST = (
    "Plan a 4-day trip to Jaipur. $1,200 budget. "
    "Love forts and street food, hate crowds."
)
EUROPE_REQUEST = "10 days in Europe. Paris and Rome. $5,000. Art and history."


def _run_cli(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-m", "src.main", *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )


@pytest.mark.e2e
class TestE2EScenarios:
    """Canonical scenarios via stub orchestrator (no API)."""

    def test_japan_deliverables(self):
        trip_plan, _ = Orchestrator(phase=PHASE_STUB).run(JAPAN_REQUEST)

        assert trip_plan.status == "complete"
        assert len(trip_plan.day_by_day) == 5
        assert len(trip_plan.neighborhoods_to_stay) >= 2
        assert trip_plan.logistics is not None
        assert trip_plan.budget is not None
        assert trip_plan.validation_passed is True

    def test_jaipur_stub_runs(self):
        trip_plan, _ = Orchestrator(phase=PHASE_STUB).run(JAIPUR_REQUEST)

        assert trip_plan.status == "complete"
        assert trip_plan.day_by_day
        assert trip_plan.budget is not None

    def test_europe_stub_runs(self):
        trip_plan, _ = Orchestrator(phase=PHASE_STUB).run(EUROPE_REQUEST)

        assert trip_plan.status == "complete"
        assert trip_plan.day_by_day
        assert trip_plan.summary


@pytest.mark.e2e
class TestCLI:
    def test_dry_run_readable_output(self):
        result = _run_cli("--dry-run", JAPAN_REQUEST, "-m", "none")

        assert result.returncode == 0
        assert "DAY-BY-DAY ITINERARY" in result.stdout
        assert "BUDGET" in result.stdout
        assert "Validation passed" in result.stdout

    def test_json_flag(self):
        result = _run_cli("--dry-run", "--json", "3 days in Bangkok. $1,200.", "-m", "none")

        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert "day_by_day" in data
        assert "summary" in data

    def test_trace_flag(self):
        result = _run_cli("--dry-run", "--trace", "3 days in Bangkok. $1,200.", "-m", "none")

        assert result.returncode == 0
        assert "Execution Trace" in result.stderr
        assert "intent_parser" in result.stderr
        assert "budget_analyst" in result.stderr

    def test_empty_request_fails(self):
        result = _run_cli("--dry-run", "   ", "-m", "none")

        assert result.returncode == 1
        assert "Could not process" in result.stdout or "describe" in result.stdout.lower()

    def test_help_shows_usage(self):
        result = subprocess.run(
            [sys.executable, "-m", "src.main", "--help"],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0
        assert "plan" in result.stdout.lower() or "travel" in result.stdout.lower()

    def test_example_script_japan(self):
        script = ROOT / "examples" / "japan_5day.sh"
        assert script.exists()
        result = subprocess.run(["bash", str(script)], cwd=ROOT, capture_output=True, text=True)
        assert result.returncode == 0
        assert (ROOT / "output" / "japan_5day.md").exists()


@pytest.mark.e2e
class TestProblemStatementDeliverables:
    def test_all_deliverables_in_stub_plan(self):
        trip_plan, _ = Orchestrator(phase=PHASE_STUB).run(JAPAN_REQUEST)

        assert trip_plan.day_by_day
        assert all(d.day and d.city and d.activities is not None for d in trip_plan.day_by_day)
        assert trip_plan.neighborhoods_to_stay
        assert all(s.recommended_neighborhood and s.reason for s in trip_plan.neighborhoods_to_stay)
        assert trip_plan.logistics and trip_plan.logistics.inter_city
        assert trip_plan.budget and trip_plan.budget.breakdown
        assert trip_plan.validation_passed

        activities = " ".join(
            a.name for d in trip_plan.day_by_day for a in d.activities
        ).lower()
        assert "senso-ji" in activities or "fushimi" in activities or "temple" in activities
