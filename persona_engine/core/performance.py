"""Performance realization for an already-resolved canonical action."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
from typing import Any, Mapping

from .action import ActionDecision


@dataclass(frozen=True)
class PerformanceAct:
    channel: str
    function: str
    target: str
    intensity: float
    onset: str
    duration: str
    voluntary: bool
    suppressible: bool
    leakage_source_id: str | None = None


@dataclass(frozen=True)
class PerformancePlan:
    schema_version: int
    plan_id: str
    decision_id: str
    communicative_goal: str | None
    literal_content_requirement: str | None
    withheld_content_ids: tuple[str, ...]
    social_stance: str
    certainty: float
    directness: float
    turn_intention: str
    acts: tuple[PerformanceAct, ...]
    completion_conditions: tuple[str, ...]
    failure_conditions: tuple[str, ...]
    provenance_ids: tuple[str, ...]

    @property
    def requires_language_renderer(self) -> bool:
        return any(act.channel == "speech" and act.function != "none" for act in self.acts)

    def to_dict(self) -> dict[str, Any]:
        raw = asdict(self)
        raw["requires_language_renderer"] = self.requires_language_renderer
        return raw

    def to_public_dict(self) -> dict[str, Any]:
        return {
            "plan_id": self.plan_id,
            "decision_id": self.decision_id,
            "acts": [asdict(item) for item in self.acts if item.channel != "private"],
            "turn_intention": self.turn_intention,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "PerformancePlan":
        values = {key: data[key] for key in cls.__dataclass_fields__ if key in data}
        values["acts"] = tuple(PerformanceAct(**item) for item in values.get("acts", ()))
        for field in ("withheld_content_ids", "completion_conditions", "failure_conditions", "provenance_ids"):
            values[field] = tuple(values.get(field, ()))
        return cls(**values)


@dataclass(frozen=True)
class PerformanceProfile:
    default_stance: str = "character_consistent"
    nonverbal_intensity: float = 0.45


class PerformancePlanner:
    """Map one action to channels without changing its cognitive ownership."""

    def plan(
        self,
        *,
        decision: ActionDecision,
        relationship,
        pressures,
        capacity: float,
        self_monitor=None,
        concealment_mode: str = "none",
        interruption: Mapping[str, Any] | None = None,
        performance_profile: PerformanceProfile | None = None,
    ) -> PerformancePlan:
        profile = performance_profile or PerformanceProfile()
        guardedness = max(0.0, min(1.0, float(getattr(relationship, "guardedness", 0.5))))
        directness = max(0.15, min(1.0, 0.85 - guardedness * 0.35))
        intensity = max(0.1, min(1.0, profile.nonverbal_intensity + (1.0 - capacity) * 0.2))
        act = self._act_for(decision, intensity)
        literal = decision.communicative_function if decision.action_kind == "speak" else None
        withheld = ("unselected_private_state",) if concealment_mode != "none" else ()
        canonical = {
            "decision_id": decision.decision_id,
            "action_kind": decision.action_kind,
            "function": act.function,
            "capacity": round(float(capacity), 6),
            "concealment": concealment_mode,
        }
        digest = hashlib.blake2b(
            json.dumps(canonical, sort_keys=True).encode("utf-8"), digest_size=8,
        ).hexdigest()
        return PerformancePlan(
            schema_version=1,
            plan_id=f"performance_{digest}",
            decision_id=decision.decision_id,
            communicative_goal=decision.communicative_function,
            literal_content_requirement=literal,
            withheld_content_ids=withheld,
            social_stance=profile.default_stance,
            certainty=decision.confidence,
            directness=round(directness, 6),
            turn_intention=decision.intention_id or decision.action_kind,
            acts=(act,),
            completion_conditions=(decision.expected_effect,),
            failure_conditions=("performance does not match canonical action",),
            provenance_ids=(decision.decision_id, decision.synthesis_id),
        )

    @staticmethod
    def _act_for(decision: ActionDecision, intensity: float) -> PerformanceAct:
        mapping = {
            "speak": ("speech", decision.communicative_function or "respond", "immediate", "brief"),
            "gesture": ("gesture", decision.communicative_function or "acknowledge", "immediate", "brief"),
            "observe": ("gaze", "inspect", "immediate", "sustained"),
            "continue_activity": ("activity", "continue", "immediate", "sustained"),
            "delay": ("timing", "delay", "delayed", "brief"),
            "silence": ("speech", "none", "immediate", "sustained"),
            "world_action": ("action", "perform", "immediate", "bounded"),
            "withdraw": ("movement", "withdraw", "immediate", "sustained"),
        }
        channel, function, onset, duration = mapping[decision.action_kind]
        return PerformanceAct(
            channel=channel,
            function=function,
            target=decision.target,
            intensity=round(intensity, 6),
            onset=onset,
            duration=duration,
            voluntary=True,
            suppressible=decision.action_kind not in {"world_action"},
        )
