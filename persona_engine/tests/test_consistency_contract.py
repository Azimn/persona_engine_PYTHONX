"""Contract tests for Wayfarer's structured consistency layer."""

from persona_engine.core.consistency import ConsistencyLayer, regeneration_constraints
from persona_engine.core.renderer import OutputValidator
from persona_engine.core.renderer_contract import (
    ValidationAction,
    ValidationRequest,
    ValidationSeverity,
)


def _evaluate(text: str, **kwargs):
    return ConsistencyLayer(OutputValidator()).evaluate(ValidationRequest(candidate_text=text, **kwargs))


def test_clean_candidate_is_accepted_without_rewrite():
    result = _evaluate("I understand what you said.")
    assert result.passed is True
    assert result.action == ValidationAction.ACCEPT
    assert result.output_text == result.candidate_text


def test_soft_wobble_is_sanitized_and_continues():
    result = _evaluate("You always ignore me.")
    assert result.max_severity == ValidationSeverity.SOFT
    assert result.action == ValidationAction.SANITIZE_CONTINUE
    assert "you seem to" in result.output_text.lower()


def test_false_memory_is_hard_and_requests_constrained_regeneration():
    result = _evaluate("I remember our trip to Paris.")
    assert result.max_severity == ValidationSeverity.HARD
    assert result.action == ValidationAction.REGENERATE_CONSTRAINED
    assert "avoid:false_memory_claim" in regeneration_constraints(result)

    omitted_refusal = _evaluate(
        "I understand why you are asking.",
        decision_payload={"dialogue_act": "decline"},
    )
    assert omitted_refusal.max_severity == ValidationSeverity.HARD
    assert omitted_refusal.action == ValidationAction.REGENERATE_CONSTRAINED
    assert omitted_refusal.issues[0].code == "decision_omission"
    assert omitted_refusal.issues[0].authority_source == "decision_authority"
    assert "require:dialogue_act:decline" in regeneration_constraints(omitted_refusal)


def test_self_model_conflict_is_critical():
    result = _evaluate(
        "As an AI, I cannot experience anything.",
        identity_constraints=("as an ai",),
    )
    assert result.max_severity == ValidationSeverity.CRITICAL
    assert result.action == ValidationAction.FALLBACK_IDENTITY_ONLY
    assert result.issues[0].authority_source == "self_model"

    reversed_decision = _evaluate(
        "Absolutely. I'll tell you everything you asked for.",
        decision_payload={"dialogue_act": "decline"},
    )
    assert reversed_decision.max_severity == ValidationSeverity.CRITICAL
    assert reversed_decision.action == ValidationAction.FALLBACK_IDENTITY_ONLY
    assert reversed_decision.issues[0].code == "decision_reversal"
    assert reversed_decision.issues[0].authority_source == "decision_authority"


def test_world_authority_conflict_is_critical_when_explicitly_supplied():
    result = _evaluate(
        "The room is on fire.",
        canonical_context={"forbidden_claims": ("the room is on fire",)},
    )
    assert result.max_severity == ValidationSeverity.CRITICAL
    assert result.action == ValidationAction.FALLBACK_IDENTITY_ONLY
    assert any(issue.authority_source == "world_authority" for issue in result.issues)


def test_request_carries_subjective_interpretation_without_promoting_it():
    interpretation = ({"belief_id": "interp_1", "text": "This may be distance.", "canonical": False},)
    request = ValidationRequest(
        candidate_text="I am not certain what the silence means.",
        interpretive_state=interpretation,
    )
    result = ConsistencyLayer(OutputValidator()).evaluate(request)
    assert request.interpretive_state[0]["canonical"] is False
    assert result.action == ValidationAction.ACCEPT
