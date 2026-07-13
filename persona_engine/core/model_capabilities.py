"""Character-agnostic renderer capability profiles and model-family hints."""

from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class ModelCapabilities:
    supports_thinking: bool | None
    recommended_thinking: str
    private_cognition_json_reliability: str
    context_size: int | None
    practical_timeout_seconds: float
    recommended_token_budget: int
    final_answer_behavior: str
    profile_source: str = "model_family_hint"

    def to_dict(self) -> dict:
        return asdict(self)


OFFLINE_CAPABILITIES = ModelCapabilities(
    supports_thinking=False,
    recommended_thinking="off",
    private_cognition_json_reliability="not_applicable",
    context_size=None,
    practical_timeout_seconds=1.0,
    recommended_token_budget=256,
    final_answer_behavior="deterministic_template",
    profile_source="built_in",
)

UNKNOWN_CAPABILITIES = ModelCapabilities(
    supports_thinking=None,
    recommended_thinking="auto",
    private_cognition_json_reliability="unknown",
    context_size=None,
    practical_timeout_seconds=60.0,
    recommended_token_budget=256,
    final_answer_behavior="unknown",
    profile_source="default",
)


def capabilities_for_model(model_name: str, provider: str = "ollama") -> ModelCapabilities:
    """Return conservative capability hints without loading or calling a model."""

    if provider == "offline":
        return OFFLINE_CAPABILITIES

    name = model_name.lower()
    if "qwen3" in name:
        return ModelCapabilities(True, "auto", "medium", 32768, 120.0, 512, "thinking_then_content")
    if "ornith" in name:
        return ModelCapabilities(True, "auto", "unknown", 32768, 120.0, 512, "thinking_then_content")
    if "minimax-m2" in name:
        return ModelCapabilities(True, "auto", "medium", 32768, 120.0, 512, "thinking_then_content")
    if "gemma4" in name:
        return ModelCapabilities(False, "off", "medium", 32768, 90.0, 384, "content_only")
    if "gemma3" in name:
        return ModelCapabilities(False, "off", "medium", 32768, 60.0, 256, "content_only")
    if "mistral" in name:
        return ModelCapabilities(False, "off", "medium", 32768, 60.0, 256, "content_only")
    return UNKNOWN_CAPABILITIES
