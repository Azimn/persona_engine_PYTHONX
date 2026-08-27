"""Wayfarer canonicality firewall tests.

These tests encode the authority rule that explicit noncanonical markers and
structurally noncanonical event families cannot be promoted into canonical
memory truth by caller-supplied flags.
"""

from persona_engine.core.event_classifier import (
    EventClassifier,
    can_promote_to_canonical_memory,
)


def test_explicit_canonical_false_vetoes_default_canonical_event():
    assert can_promote_to_canonical_memory("input", {"canonical": False}) is False


def test_explicit_canonical_truth_false_vetoes_default_canonical_event():
    assert can_promote_to_canonical_memory("world_fact", {"canonical_truth": False}) is False


def test_response_noncanonical_marker_vetoes_default_canonical_event():
    assert can_promote_to_canonical_memory("input", {"response_is_canonical_truth": False}) is False


def test_interpretive_belief_cannot_be_elevated_by_true_flag():
    assert can_promote_to_canonical_memory("interpretive_belief", {"canonical_truth": True}) is False


def test_renderer_output_cannot_be_elevated_by_true_flag():
    assert can_promote_to_canonical_memory("renderer_output", {"canonical_truth": True}) is False


def test_private_cognition_cannot_be_elevated_by_true_flag():
    assert can_promote_to_canonical_memory("private_cognition", {"canonical_truth": True}) is False


def test_unknown_event_requires_explicit_true():
    assert can_promote_to_canonical_memory("future_event", {}) is False
    assert can_promote_to_canonical_memory("future_event", {"canonical_truth": True}) is True


def test_unknown_event_true_cannot_override_explicit_false():
    assert can_promote_to_canonical_memory(
        "future_event",
        {"canonical_truth": True, "canonical": False},
    ) is False


def test_interpretive_belief_classification_can_be_memorable_but_not_truth():
    result = EventClassifier().classify(
        "interpretive_belief",
        {"text": "I suspect distance", "canonical_truth": True},
        event_id="belief_1",
    )
    assert result.canonical_truth is False
    assert result.should_store is False
    assert result.memory_type == "interpretive"
