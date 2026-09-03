from persona_engine.agent import CharacterAgent
from persona_engine.core.ensemble_renderer import EnsembleLLMRenderer


class FakeEngine:
    def __init__(self):
        self.renderer = None

    def set_renderer(self, renderer):
        self.renderer = renderer

    def renderer_status(self):
        return self.renderer.runtime_status()


def test_public_agent_can_enable_ensemble_renderer_without_touching_engine_internals():
    agent = object.__new__(CharacterAgent)
    agent.engine = FakeEngine()

    status = agent.use_ensemble_renderer(
        "qwen-test",
        candidate_count=4,
        thinking_mode="off",
    )

    assert isinstance(agent.engine.renderer, EnsembleLLMRenderer)
    assert status["model_name"] == "qwen-test"
    assert status["candidate_count"] == 4
    assert status["prevalidation"] is True
    assert status["authored_landmarks"] is True


def test_public_set_renderer_remains_generic():
    agent = object.__new__(CharacterAgent)
    agent.engine = FakeEngine()
    renderer = EnsembleLLMRenderer(model_name="fake", provider="offline", candidate_count=1)

    status = agent.set_renderer(renderer)

    assert agent.engine.renderer is renderer
    assert status["realization_mode"].startswith("ensemble-candidate-realization")
