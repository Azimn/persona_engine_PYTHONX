"""Expression constraints and deterministic performance planning."""

from dataclasses import asdict, dataclass
from typing import Any, Mapping, Optional, List


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


@dataclass(frozen=True)
class PerformancePlan:
    """How an already-selected behavior is made externally observable.

    This is performance evidence, not another action selector.  It contains no
    prose reasoning and cannot mutate organism or world state.
    """

    action_type: str
    utterance_required: bool
    source_decision_id: str | None
    reaction: str | None = None
    gesture: str | None = None
    facial_expression: str | None = None
    animation_directive: str | None = None
    delay_ms: int = 0
    voice_directive: str | None = None
    visibility: str = "observable"
    reasons: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


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


def build_performance_plan(
    decision_payload: Mapping[str, Any],
    resistance: str | None,
    ongoing_action: Mapping[str, Any] | None,
) -> PerformancePlan:
    """Realize the resolved decision without changing what was decided."""

    action = dict(ongoing_action or {})
    decision_id = str(action.get("decision_id")) if action.get("decision_id") else None
    visibility = str(action.get("visibility", "observable"))
    if resistance == "go_quiet":
        return PerformancePlan(
            action_type="silence",
            utterance_required=False,
            source_decision_id=decision_id,
            reaction="withheld response",
            delay_ms=900,
            visibility=visibility,
            reasons=("resolved resistance requires silence",),
        )
    if resistance:
        return PerformancePlan(
            action_type="speak",
            utterance_required=True,
            source_decision_id=decision_id,
            voice_directive=str(resistance),
            visibility=visibility,
            reasons=(f"resolved resistance requires {resistance}",),
        )

    ongoing_type = str(action.get("action_type", ""))
    interruptible = bool(action.get("interruptible", True))
    if ongoing_type == "silence" or (ongoing_type == "continue_activity" and not interruptible):
        return PerformancePlan(
            action_type="continue_activity" if ongoing_type == "continue_activity" else "silence",
            utterance_required=False,
            source_decision_id=decision_id,
            reaction="attention remains on the current activity",
            animation_directive="continue current activity",
            delay_ms=600,
            visibility=visibility,
            reasons=("ongoing intrinsic action is not interruptible",),
        )
    if ongoing_type == "gesture":
        return PerformancePlan(
            action_type="gesture",
            utterance_required=False,
            source_decision_id=decision_id,
            reaction="brief acknowledgement",
            gesture="acknowledge without speech",
            delay_ms=250,
            visibility=visibility,
            reasons=("ongoing intrinsic action permits nonverbal acknowledgement",),
        )

    dialogue_act = str(decision_payload.get("dialogue_act", "respond"))
    return PerformancePlan(
        action_type="speak",
        utterance_required=True,
        source_decision_id=decision_id,
        voice_directive=dialogue_act,
        visibility=visibility,
        reasons=(f"resolved dialogue act is {dialogue_act}",),
    )


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
