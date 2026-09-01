"""Layer 6 expression envelope and resistance policy."""

from dataclasses import dataclass
from typing import Optional, List


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


RESISTANCE_POLICY = {
    "identity_violation": "character_refusal",
    "intimacy_too_fast": "deflect",
    "accusation": "challenge",
    "contradiction": "challenge",
    "manipulation": "go_quiet",
    "boredom": "shift_topic",
    "disrespect": "shorten",
    "emotional_overload": "go_quiet",
}


def select_resistance(triggers: List[str]) -> Optional[str]:
    for t in triggers:
        if t in RESISTANCE_POLICY:
            return RESISTANCE_POLICY[t]
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
