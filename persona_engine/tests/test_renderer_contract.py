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
