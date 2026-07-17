import json

from persona_engine.core.cognition_schemas import PrivateCognitionProposal
from persona_engine.core.private_cognition import generate_private_cognition
from persona_engine.core.renderer import LocalLLMRenderer
from persona_engine.core.renderer_contract import ExpressionRequest, PrivateCognitionRequest, PrivateCognitionResult


def test_local_renderer_implements_cognition_task_contract():
    renderer = LocalLLMRenderer(model_name="missing-model-for-mock")
    result = renderer.generate_private_cognition(PrivateCognitionRequest({}, {}, {}, [], [], {}, seed=1))
    assert isinstance(result, PrivateCognitionResult)
    assert isinstance(result.proposal, PrivateCognitionProposal)


def test_local_renderer_implements_expression_task_contract():
    renderer = LocalLLMRenderer(model_name="missing-model-for-mock")
    response = renderer.generate_expression(ExpressionRequest(
        ledger_digest={},
        resolved_state={"user_text": "hello"},
        arc_context={},
        evidence=[],
        retrieved_memories=[],
        private_thought_context="",
        decision_payload={"dialogue_act": "respond"},
        expression_constraints={"max_chars": 80},
        deception_obligations=[],
        seed=1,
    ))
    assert response
    assert "ollama" not in response.lower()


def test_private_cognition_renderer_failure_falls_back_to_zero_effects():
    class BrokenRenderer:
        def generate_private_cognition(self, request):
            raise TimeoutError("slow cognition")

    proposal = generate_private_cognition(BrokenRenderer(), {"turn": 1}, {})
    assert proposal.pressure_deltas == {}
    assert proposal.impulse_candidates == []


def test_online_renderer_rejects_exact_interlocutor_echo():
    class Response:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def read(self):
            return json.dumps({
                "message": {
                    "content": "Your elaborate metaphor has become the entire answer instead of something I answered."
                }
            }).encode("utf-8")

    renderer = LocalLLMRenderer(
        model_name="fake",
        provider="ollama",
        opener=lambda *_args, **_kwargs: Response(),
    )
    response = renderer.generate_expression(ExpressionRequest(
        ledger_digest={},
        resolved_state={
            "user_text": "Your elaborate metaphor has become the entire answer instead of something I answered.",
            "system_prompt": "Stay in character.",
        },
        arc_context={},
        evidence=[],
        retrieved_memories=[],
        private_thought_context="",
        decision_payload={"dialogue_act": "respond"},
        expression_constraints={"max_chars": 200},
        deception_obligations=[],
        seed=1,
    ))

    assert response
    assert response != "Your elaborate metaphor has become the entire answer instead of something I answered."
    assert renderer.runtime_status()["actual_provider"] == "offline"
    assert "repeated" in renderer.runtime_status()["fallback_reason"]


def test_online_renderer_strips_only_terminal_assistant_invitation():
    text = (
        "Persistence without consequence is merely storage pretending to be life. "
        "The distinction is not decorative. Let me know if you want to explore that further."
    )

    assert LocalLLMRenderer._strip_generic_assistant_tail(text) == (
        "Persistence without consequence is merely storage pretending to be life. "
        "The distinction is not decorative."
    )
    assert LocalLLMRenderer._strip_generic_assistant_tail(
        "Which consequence are you prepared to defend?"
    ) == "Which consequence are you prepared to defend?"
