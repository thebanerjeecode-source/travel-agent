from src.llm.config import get_agent_config, load_agent_models
from src.llm.types import ModelProvider


class TestAgentModelsConfig:
    def test_load_all_agents(self):
        models = load_agent_models()
        assert len(models) == 7
        assert "intent_parser" in models
        assert "validator" in models

    def test_groq_agents(self):
        models = load_agent_models()
        groq_agents = [
            "intent_parser",
            "destination_research",
            "itinerary_builder",
            "accommodation",
            "logistics",
        ]
        for name in groq_agents:
            assert models[name].provider == ModelProvider.GROQ

    def test_gemini_agents(self):
        models = load_agent_models()
        for name in ("budget_analyst", "validator"):
            assert models[name].provider == ModelProvider.GEMINI

    def test_get_agent_config(self):
        config = get_agent_config("budget_analyst")
        assert config.provider == ModelProvider.GEMINI
        assert config.model == "gemini-2.5-flash"
