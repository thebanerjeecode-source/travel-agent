from src.agents.intent_normalizer import IntentParserLLMOutput, normalize_requirements
from src.schemas import AssumedField, TravelStyle


class TestNormalizeRequirements:
    def test_full_parse(self):
        parsed = IntentParserLLMOutput(
            duration_days=5,
            destinations=["Tokyo", "Kyoto"],
            budget_usd=3000,
            interests=["food", "temples"],
            dislikes=["crowds"],
        )
        req = normalize_requirements(parsed)
        assert req is not None
        assert req.duration_days == 5
        assert req.budget_usd == 3000

    def test_missing_budget_adds_assumption(self):
        parsed = IntentParserLLMOutput(
            duration_days=3,
            destinations=["Bangkok"],
        )
        req = normalize_requirements(parsed)
        assert req is not None
        assert req.budget_usd > 0
        assert any(a.field == "budget_usd" for a in req.assumptions)

    def test_empty_destinations_returns_none(self):
        parsed = IntentParserLLMOutput(destinations=[])
        assert normalize_requirements(parsed) is None

    def test_missing_duration_defaults_to_five(self):
        parsed = IntentParserLLMOutput(destinations=["Paris"], budget_usd=2000)
        req = normalize_requirements(parsed)
        assert req is not None
        assert req.duration_days == 5
