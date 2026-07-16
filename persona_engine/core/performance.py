"""Performance realization for an already-resolved canonical action."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
from typing import Any, Mapping

from .action import ActionDecision


TENDENCY_FIELDS = frozenset({
    "social_stance", "directness_delta", "certainty_delta", "nonverbal_intensity",
    "gaze_mode", "face_control", "gesture_mode", "turn_mode", "response_latency",
    "concealment_bias", "leakage_threshold", "supplementary_channels",
})
TENDENCY_ENUMS = {
    "social_stance": frozenset({"neutral", "guarded", "precise", "warm", "open", "reserved", "animated"}),
    "gaze_mode": frozenset({"target", "averted", "interlocutor", "alternating", "steady"}),
    "face_control": frozenset({"neutral", "tight", "controlled", "open", "expressive"}),
    "gesture_mode": frozenset({"none", "minimal", "restrained", "animated", "warm"}),
    "turn_mode": frozenset({"clipped", "measured", "fluid", "expansive", "quiet"}),
    "response_latency": frozenset({"immediate", "brief", "delayed", "variable"}),
    "concealment_bias": frozenset({"none", "low", "moderate", "high"}),
}
ALLOWED_CHANNELS = frozenset({"voice", "gaze", "face", "gesture", "timing", "posture", "activity", "movement"})


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
    activity_transition: str | None = None
    activity_label: str | None = None
    conversation_choreography_id: str | None = None

    @property
    def requires_language_renderer(self) -> bool:
        return any(act.channel == "speech" and act.function != "none" for act in self.acts)

    def to_dict(self) -> dict[str, Any]:
        raw = asdict(self)
        raw["requires_language_renderer"] = self.requires_language_renderer
        raw["record_authority"] = "deterministic_performance_record"
        raw["replay_authoritative"] = True
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
        values.setdefault("activity_transition", None)
        values.setdefault("activity_label", None)
        values.setdefault("conversation_choreography_id", None)
        return cls(**values)


@dataclass(frozen=True)
class PerformanceProfile:
    tendency_id: str = "default"
    social_stance: str = "neutral"
    directness_delta: float = 0.0
    certainty_delta: float = 0.0
    nonverbal_intensity: float = 0.45
    gaze_mode: str = "interlocutor"
    face_control: str = "neutral"
    gesture_mode: str = "minimal"
    turn_mode: str = "measured"
    response_latency: str = "brief"
    concealment_bias: str = "none"
    leakage_threshold: float = 0.5
    supplementary_channels: tuple[str, ...] = ("voice", "gaze", "face", "timing")

    @classmethod
    def from_cartridge_tendency(
        cls,
        tendencies: Mapping[str, Any] | None,
        tendency_id: str | None,
    ) -> "PerformanceProfile":
        if not tendency_id:
            return cls()
        source = dict(tendencies or {})
        if tendency_id not in source:
            raise ValueError(f"unknown tendency id: {tendency_id}")
        raw = dict(source[tendency_id])
        unknown = sorted(set(raw) - TENDENCY_FIELDS)
        if unknown:
            raise ValueError(f"unknown field: {unknown[0]}")
        for field, allowed in TENDENCY_ENUMS.items():
            if field in raw and str(raw[field]) not in allowed:
                raise ValueError(f"unsupported {field}: {raw[field]}")
        for field in ("directness_delta", "certainty_delta"):
            value = float(raw.get(field, 0.0))
            if not -1.0 <= value <= 1.0:
                raise ValueError(f"{field} must be within [-1, 1]")
        for field in ("nonverbal_intensity", "leakage_threshold"):
            value = float(raw.get(field, getattr(cls(), field)))
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{field} must be within [0, 1]")
        channels = tuple(str(item) for item in raw.get("supplementary_channels", cls().supplementary_channels))
        if any(item not in ALLOWED_CHANNELS for item in channels):
            raise ValueError("supplementary_channels contains unsupported channel")
        return cls(
            tendency_id=str(tendency_id),
            social_stance=str(raw.get("social_stance", "neutral")),
            directness_delta=float(raw.get("directness_delta", 0.0)),
            certainty_delta=float(raw.get("certainty_delta", 0.0)),
            nonverbal_intensity=float(raw.get("nonverbal_intensity", 0.45)),
            gaze_mode=str(raw.get("gaze_mode", "interlocutor")),
            face_control=str(raw.get("face_control", "neutral")),
            gesture_mode=str(raw.get("gesture_mode", "minimal")),
            turn_mode=str(raw.get("turn_mode", "measured")),
            response_latency=str(raw.get("response_latency", "brief")),
            concealment_bias=str(raw.get("concealment_bias", "none")),
            leakage_threshold=float(raw.get("leakage_threshold", 0.5)),
            supplementary_channels=channels,
        )


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
        activity_transition: str | None = None,
        activity_label: str | None = None,
        conversation_choreography=None,
    ) -> PerformancePlan:
        profile = performance_profile or PerformanceProfile()
        guardedness = max(0.0, min(1.0, float(getattr(relationship, "guardedness", 0.5))))
        directness = max(0.0, min(1.0, 0.85 - guardedness * 0.35 + profile.directness_delta))
        certainty = max(0.0, min(1.0, decision.confidence + profile.certainty_delta))
        perceived_confidence = float(getattr(self_monitor, "perceived_confidence", certainty))
        noticed_conflicts = tuple(getattr(self_monitor, "noticed_conflict_ids", ()))
        selected_regulation = (
            self_monitor.candidate(decision.selected_regulation_id)
            if self_monitor is not None and decision.selected_regulation_id else None
        )
        if perceived_confidence < 0.45:
            certainty = max(0.0, certainty - (0.45 - perceived_confidence) * 0.45)
        if selected_regulation and selected_regulation.kind == "double_down":
            directness = min(1.0, directness + 0.18)
            certainty = min(1.0, certainty + 0.08)
        elif selected_regulation and selected_regulation.kind == "conceal_uncertainty":
            directness = min(1.0, directness + 0.06)
        choreography_energy = float(
            getattr(conversation_choreography, "conversational_energy", 0.5)
        )
        if conversation_choreography is not None:
            if getattr(conversation_choreography, "answer_shape", "none") == "direct":
                directness = min(1.0, directness + 0.08)
            elif getattr(conversation_choreography, "answer_shape", "none") == "qualified":
                directness = max(0.0, directness - 0.05)
        intensity = max(
            0.1,
            min(
                1.0,
                profile.nonverbal_intensity
                + (1.0 - capacity) * 0.2
                + (choreography_energy - 0.5) * 0.18,
            ),
        )
        acts = self._acts_for(decision, intensity, profile)
        if activity_transition in {"continued", "paused", "resumed", "completed", "failed", "abandoned", "changed"}:
            if any(item.channel == "activity" for item in acts):
                acts = tuple(
                    PerformanceAct(
                        **{
                            **asdict(item),
                            "function": activity_transition,
                            "target": str(activity_label or decision.target)[:120],
                        }
                    ) if item.channel == "activity" else item
                    for item in acts
                )
            else:
                acts = (*acts, PerformanceAct(
                    channel="activity", function=activity_transition,
                    target=str(activity_label or decision.target)[:120], intensity=round(intensity, 6),
                    onset="immediate", duration="sustained", voluntary=True, suppressible=True,
                ))
        if conversation_choreography is not None:
            pacing = str(getattr(conversation_choreography, "pacing", "measured"))
            acts = tuple(
                PerformanceAct(**{**asdict(item), "function": pacing})
                if item.channel == "timing" else item
                for item in acts
            )
        acts = self._apply_self_monitor_acts(
            acts, decision, profile, perceived_confidence, noticed_conflicts,
            selected_regulation.kind if selected_regulation else None,
        )
        literal = (
            decision.communicative_function
            if any(item.channel == "speech" for item in acts)
            else None
        )
        withheld = ("unselected_private_state",) if concealment_mode != "none" else ()
        canonical = {
            "decision_id": decision.decision_id,
            "action_kind": decision.action_kind,
            "acts": [(act.channel, act.function) for act in acts],
            "capacity": round(float(capacity), 6),
            "concealment": concealment_mode,
            "activity_transition": activity_transition,
            "activity_label": str(activity_label)[:120] if activity_label else None,
            "conversation_choreography_id": getattr(
                conversation_choreography, "choreography_id", None,
            ),
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
            social_stance=profile.social_stance,
            certainty=round(certainty, 6),
            directness=round(directness, 6),
            turn_intention=decision.intention_id or decision.action_kind,
            acts=acts,
            completion_conditions=(decision.expected_effect,),
            failure_conditions=("performance does not match canonical action",),
            provenance_ids=tuple(filter(None, (
                decision.decision_id,
                decision.synthesis_id,
                getattr(conversation_choreography, "choreography_id", None),
            ))),
            activity_transition=activity_transition,
            activity_label=str(activity_label)[:120] if activity_label else None,
            conversation_choreography_id=getattr(
                conversation_choreography, "choreography_id", None,
            ),
        )

    @staticmethod
    def _apply_self_monitor_acts(
        acts: tuple[PerformanceAct, ...],
        decision: ActionDecision,
        profile: PerformanceProfile,
        perceived_confidence: float,
        noticed_conflicts: tuple[str, ...],
        regulation_kind: str | None,
    ) -> tuple[PerformanceAct, ...]:
        updated = list(acts)
        existing = {item.channel for item in updated}

        def add(channel: str, function: str, intensity: float = 0.45) -> None:
            if channel in existing:
                return
            updated.append(PerformanceAct(
                channel=channel, function=function, target=decision.target,
                intensity=max(0.0, min(1.0, intensity)), onset="immediate",
                duration="brief", voluntary=True, suppressible=True,
            ))
            existing.add(channel)

        def replace(channel: str, function: str, intensity: float) -> None:
            nonlocal updated
            updated = [
                PerformanceAct(
                    **{
                        **asdict(item),
                        "function": function,
                        "intensity": max(float(item.intensity), intensity),
                    }
                ) if item.channel == channel else item
                for item in updated
            ]
            if channel not in existing:
                add(channel, function, intensity)

        if decision.action_kind == "speak":
            if perceived_confidence < 0.45:
                replace("timing", "hesitate", 0.40 + (0.45 - perceived_confidence))
            elif noticed_conflicts:
                replace("timing", "brief_pause", 0.45)
            if regulation_kind == "self_correct":
                updated = [
                    PerformanceAct(
                        **{**asdict(item), "function": "gaze_reset"}
                    ) if item.channel == "gaze" else item
                    for item in updated
                ]
                replace("timing", "brief_pause", 0.55)
            elif regulation_kind == "conceal_uncertainty":
                updated = [
                    PerformanceAct(**{**asdict(item), "function": "controlled"})
                    if item.channel == "face" else item for item in updated
                ]
            elif regulation_kind == "double_down":
                updated = [
                    PerformanceAct(**{**asdict(item), "function": "controlled"})
                    if item.channel == "face" else item for item in updated
                ]
        return tuple(updated)

    @staticmethod
    def _acts_for(
        decision: ActionDecision,
        intensity: float,
        profile: PerformanceProfile,
    ) -> tuple[PerformanceAct, ...]:
        acts: list[PerformanceAct] = []

        def add(channel: str, function: str, onset: str = "immediate", duration: str = "brief") -> None:
            acts.append(PerformanceAct(
                channel=channel, function=function, target=decision.target,
                intensity=round(intensity, 6), onset=onset, duration=duration,
                voluntary=True, suppressible=decision.action_kind != "world_action",
            ))

        if decision.action_kind == "speak":
            add("speech", decision.communicative_function or "respond")
            if "voice" in profile.supplementary_channels:
                add("voice", profile.turn_mode)
        elif decision.action_kind == "gesture":
            add("gesture", profile.gesture_mode if profile.gesture_mode != "none" else "acknowledge")
        elif decision.action_kind == "observe":
            add("gaze", profile.gaze_mode, duration="sustained")
            add("posture", "orient_to_target", duration="sustained")
            if "movement" in profile.supplementary_channels:
                add("movement", "approach_for_observation")
        elif decision.action_kind == "continue_activity":
            add("activity", "continue", duration="sustained")
            add("posture", "task_engaged", duration="sustained")
        elif decision.action_kind == "delay":
            add("timing", "delay", onset="delayed")
            add("activity", "preserve_current_intention", duration="sustained")
        elif decision.action_kind == "silence":
            add("activity", "continue", duration="sustained")
        elif decision.action_kind == "world_action":
            add("action", "perform", duration="bounded")
            if decision.communicative_function:
                add("speech", decision.communicative_function)
                if "voice" in profile.supplementary_channels:
                    add("voice", profile.turn_mode)
        elif decision.action_kind == "withdraw":
            add("movement", "withdraw", duration="sustained")

        existing = {act.channel for act in acts}
        supplemental = {
            "gaze": profile.gaze_mode,
            "face": profile.face_control,
            "gesture": profile.gesture_mode,
            "timing": profile.response_latency,
            "posture": "task_engaged",
            "activity": "continue",
        }
        for channel in profile.supplementary_channels:
            function = supplemental.get(channel)
            if function and channel not in existing and not (channel == "gesture" and function == "none"):
                add(channel, function, onset="delayed" if profile.response_latency == "delayed" else "immediate")
                existing.add(channel)
        return tuple(acts)
