"""Model-family capability profiles remain explicit and conservative."""

from persona_engine.core.model_capabilities import capabilities_for_model


def test_qwen3_profile_preserves_thinking_support():
    profile = capabilities_for_model("qwen3:8b")
    assert profile.supports_thinking is True
    assert profile.recommended_thinking == "auto"
    assert profile.final_answer_behavior == "thinking_then_content"
    assert profile.context_size


def test_nonthinking_profile_recommends_direct_generation():
    profile = capabilities_for_model("gemma3:1b")
    assert profile.supports_thinking is False
    assert profile.recommended_thinking == "off"
    assert profile.final_answer_behavior == "content_only"


def test_unknown_model_does_not_invent_capabilities():
    profile = capabilities_for_model("unprofiled:model")
    assert profile.supports_thinking is None
    assert profile.private_cognition_json_reliability == "unknown"
    assert profile.context_size is None


def test_offline_profile_is_dependency_free_and_nonthinking():
    profile = capabilities_for_model("offline-template", provider="offline")
    assert profile.supports_thinking is False
    assert profile.final_answer_behavior == "deterministic_template"
    assert profile.profile_source == "built_in"
