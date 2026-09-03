from persona_engine.core.ensemble_renderer import EnsembleLLMRenderer, ENSEMBLE_REALIZATION_VERSION
from persona_engine.core.renderer_contract import ExpressionRequest


class FakeEnsembleRenderer(EnsembleLLMRenderer):
    def __init__(self, outputs, **kwargs):
        super().__init__(model_name="fake", provider="ollama", **kwargs)
        self.outputs = list(outputs)
        self.calls = []

    def _ollama_chat(self, messages, seed):
        self.calls.append(seed)
        index = len(self.calls) - 1
        return self.outputs[index]


def request(seed=10):
    return ExpressionRequest(
        ledger_digest={"identity": "Pretorius"},
        resolved_state={
            "user_text": "What do you think?",
            "experience_context": {},
        },
        arc_context={},
        evidence=[],
        retrieved_memories=[],
        private_thought_context="",
        decision_payload={"dialogue_act": "respond"},
        expression_constraints={"max_chars": 200},
        deception_obligations=[],
        seed=seed,
    )


def test_ensemble_renderer_generates_multiple_candidates_and_selects_one():
    renderer = FakeEnsembleRenderer(
        ["First wording.", "Second wording.", "Third wording."],
        candidate_count=3,
    )
    output = renderer.generate_expression(request())
    assert output == "First wording."
    assert len(renderer.calls) == 3
    status = renderer.runtime_status()
    assert status["realization_mode"] == ENSEMBLE_REALIZATION_VERSION
    assert status["last_ensemble_trace"]["generated_candidate_count"] == 3


def test_ensemble_renderer_avoids_recent_exact_repetition():
    renderer = FakeEnsembleRenderer(
        ["First wording.", "Second wording.", "Third wording."],
        candidate_count=3,
    )
    renderer.remember_surface("First wording.")
    output = renderer.generate_expression(request())
    assert output != "First wording."
    assert output in {"Second wording.", "Third wording."}


def test_ensemble_renderer_keeps_same_resolved_request_for_all_candidates():
    renderer = FakeEnsembleRenderer(
        ["One.", "Two.", "Three."],
        candidate_count=3,
        candidate_seed_stride=100,
    )
    renderer.generate_expression(request(seed=7))
    assert renderer.calls == [7, 107, 207]


def test_ensemble_renderer_falls_back_only_when_all_model_candidates_fail():
    renderer = FakeEnsembleRenderer(["", "", ""], candidate_count=3)
    output = renderer.generate_expression(request())
    assert output
    status = renderer.runtime_status()
    assert status["actual_provider"] == "offline"
    assert status["last_ensemble_trace"]["mode"] == "offline_fallback"
