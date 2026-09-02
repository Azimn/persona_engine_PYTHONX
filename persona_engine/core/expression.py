"""Layer 6 expression envelope and resistance policy."""

from dataclasses import dataclass
from typing import Optional, List

from .disposition import BehavioralDispositionProfile


@dataclass
class ExpressionEnvelope:
    max_chars: int
    directness: float
    warmth: float
    guardedness: float
    question_probability: float
    vulnerability_allowed: bool
    refusal_mode: Optional[str]
    tone_label: str


# Identity mutation is not a personality preference. It remains a core-owned
# invariant whenever the requested mutation conflicts with authored identity.
HARD_RESISTANCE_POLICY = {
    "identity_violation": "character_refusal",
}

# Compatibility projection of the legacy default policy. New character-specific
# variation belongs in BehavioralDispositionProfile rather than in this module.
RESISTANCE_POLICY = {
    **HARD_RESISTANCE_POLICY,
    **BehavioralDispositionProfile().to_dict(),
}


def select_resistance(
    triggers: List[str],
    profile: BehavioralDispositionProfile | None = None,
) -> Optional[str]:
    """Select the first applicable response without making personality global.

    Hard invariant responses are evaluated first. Soft trigger responses come
    from the subject's authored profile. A profile response of ``none`` is
    represented by ``response_for`` returning None, so later simultaneous
    triggers may still contribute a response.
    """

    authored = profile or BehavioralDispositionProfile()
    for trigger in triggers:
        if trigger in HARD_RESISTANCE_POLICY:
            return HARD_RESISTANCE_POLICY[trigger]
        response = authored.response_for(trigger)
        if response is not None:
            return response
    return None


def build_envelope(risk_bucket: str, relationship, dominant_pressure_name: str) -> ExpressionEnvelope:
    if risk_bucket == "LOW":
        env = ExpressionEnvelope(220, 0.65, 0.50, relationship.guardedness, 0.30, True, None, "composed")
    elif risk_bucket == "MEDIUM":
        env = ExpressionEnvelope(120, 0.45, 0.30, min(1.0, relationship.guardedness + 0.2), 0.15, False, None, "guarded")
    else:
        env = ExpressionEnvelope(65, 0.80, 0.10, min(1.0, relationship.guardedness + 0.4), 0.05, False, "character_refusal", "abrupt")

    if dominant_pressure_name in {"curiosity", "attachment"} and risk_bucket == "LOW":
        env.warmth = min(1.0, env.warmth + 0.1)
        env.question_probability = min(1.0, env.question_probability + 0.2)
    if dominant_pressure_name in {"shame", "fear"}:
        env.guardedness = min(1.0, env.guardedness + 0.15)
        env.warmth = max(0.0, env.warmth - 0.1)

    env.vulnerability_allowed = relationship.trust > 0.55 and relationship.tension < 0.35 and risk_bucket == "LOW"
    return env


def relationship_expression_stance(relationship) -> str:
    """Return a coarse history-conditioned stance for language realization."""

    if relationship.unresolved_conflict > 0.35 or relationship.tension >= 0.60:
        return "conflicted"
    if relationship.guardedness >= 0.65 or relationship.trust < 0.35:
        return "guarded"
    if relationship.trust >= 0.66 and relationship.attachment >= 0.30 and relationship.tension < 0.25:
        return "close"
    if relationship.trust >= 0.66 and relationship.tension < 0.35:
        return "trusted"
    return "neutral"
