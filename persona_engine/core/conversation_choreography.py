"""Deterministic conversational realization for an already-selected action."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import itertools
import json
import math
from typing import Any, Mapping, Sequence


RHETORICAL_STRATEGIES = frozenset({
    "direct", "qualify", "teach", "summarize", "acknowledge", "reflect",
    "repair", "clarify", "resume", "probe", "compare", "challenge",
    "reminisce", "speculate", "express_curiosity", "return_to_work",
    "withhold",
})
TRAJECTORY_PHASES = frozenset({"open", "deepen", "complicate", "resolve", "suspend", "return"})
ENERGY_BANDS = frozenset({"low", "medium", "high"})
RESPONSE_SPANS = frozenset({"fragment", "brief", "normal", "extended"})
ANSWER_SHAPES = frozenset({"none", "direct", "qualified", "staged"})
PACING_MODES = frozenset({"halting", "clipped", "measured", "expansive"})
DISCLOSURE_DEPTHS = frozenset({"minimal", "bounded", "personal"})
INITIATIVE_LEVELS = frozenset({"low", "medium", "high"})
ACTIVITY_RELATIONS = frozenset({"none", "continue", "pause", "resume", "leave"})
RESOLUTION_POLICIES = frozenset({"complete", "open", "defer"})
MEMORY_ROLES = frozenset({"none", "evidence", "analogy", "anecdote", "emotional_callback"})


def _clamp(value: float) -> float:
    value = float(value)
    if not math.isfinite(value):
        raise ValueError("choreography values must be finite")
    return max(0.0, min(1.0, value))


def _value(source: Any, key: str, default: Any = None) -> Any:
    if isinstance(source, Mapping):
        return source.get(key, default)
    return getattr(source, key, default)


@dataclass(frozen=True)
class ConversationChoreographyPlan:
    schema_version: int
    choreography_id: str
    decision_id: str
    actor_id: int
    rhetorical_strategy: str
    trajectory_phase: str
    conversational_energy: float
    energy_band: str
    response_span: str
    answer_shape: str
    pacing: str
    disclosure_depth: str
    initiative_level: str
    activity_relation: str
    resolution_policy: str
    memory_role: str
    selected_extension: str | None
    trajectory_signature: str
    reason_codes: tuple[str, ...]
    provenance_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        enums = (
            (self.rhetorical_strategy, RHETORICAL_STRATEGIES),
            (self.trajectory_phase, TRAJECTORY_PHASES),
            (self.energy_band, ENERGY_BANDS),
            (self.response_span, RESPONSE_SPANS),
            (self.answer_shape, ANSWER_SHAPES),
            (self.pacing, PACING_MODES),
            (self.disclosure_depth, DISCLOSURE_DEPTHS),
            (self.initiative_level, INITIATIVE_LEVELS),
            (self.activity_relation, ACTIVITY_RELATIONS),
            (self.resolution_policy, RESOLUTION_POLICIES),
            (self.memory_role, MEMORY_ROLES),
        )
        if any(value not in allowed for value, allowed in enums):
            raise ValueError("unsupported conversation choreography value")
        if not 0 < int(self.actor_id) <= 0xFFFFFFFF:
            raise ValueError("choreography actor_id must be a nonzero uint32")
        _clamp(self.conversational_energy)

    def to_dict(self) -> dict[str, Any]:
        return {
            **asdict(self),
            "record_authority": "deterministic_conversation_realization_record",
            "replay_authoritative": True,
        }

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "ConversationChoreographyPlan":
        raw = {key: value[key] for key in cls.__dataclass_fields__ if key in value}
        raw["reason_codes"] = tuple(raw.get("reason_codes", ()))
        raw["provenance_ids"] = tuple(raw.get("provenance_ids", ()))
        raw.setdefault("selected_extension", None)
        return cls(**raw)


class ConversationChoreographyPlanner:
    """Shape interaction without changing the canonical action or selected move."""

    def plan(
        self,
        *,
        decision: Any,
        candidate: Any,
        continuity: Any,
        body: Any,
        relationship: Any,
        dominant_pressure: float,
        self_monitor: Any,
        activity_transition: str | None,
        stable_seed: int,
    ) -> ConversationChoreographyPlan:
        action_kind = str(_value(decision, "action_kind", "silence"))
        obligation = str(_value(candidate, "obligation", "acknowledge"))
        extension = _value(candidate, "extension_move")
        topic = _value(continuity, "active_topic")
        topic_depth = int(_value(topic, "depth", 0))
        emotional_importance = _clamp(_value(topic, "emotional_importance", 0.0))
        initiative = _clamp(_value(continuity, "initiative_budget", 0.45))
        pressure = _clamp(dominant_pressure)
        fatigue = _clamp(_value(body, "fatigue", 0.0))
        body_energy = _clamp(_value(body, "energy", 0.5))
        familiarity = _clamp(_value(relationship, "familiarity", 0.0))
        perceived_confidence = _clamp(_value(self_monitor, "perceived_confidence", 0.6))
        energy = _clamp(
            0.22 + 0.34 * body_energy - 0.28 * fatigue + 0.12 * pressure
            + 0.12 * emotional_importance + 0.10 * initiative
            + 0.06 * familiarity + 0.04 * perceived_confidence
        )
        energy_band = "low" if energy < 0.38 else "high" if energy >= 0.68 else "medium"
        initiative_level = "low" if initiative < 0.34 else "high" if initiative >= 0.68 else "medium"
        phase = self._phase(topic_depth, _value(continuity, "last_transition_reason"), action_kind)
        strategy_options = self._strategy_options(action_kind, obligation, extension, topic_depth)
        span_options = self._span_options(action_kind, obligation, extension, energy_band)
        shape_options = self._shape_options(action_kind, obligation, perceived_confidence)
        recent = tuple(str(item) for item in _value(continuity, "recent_trajectory_signatures", ()))
        strategy, span, shape = self._least_repeated_shape(
            strategy_options, span_options, shape_options, phase, recent, stable_seed,
        )
        pacing = (
            "halting" if perceived_confidence < 0.38
            else "clipped" if energy_band == "low"
            else "expansive" if energy_band == "high" and span == "extended"
            else "measured"
        )
        has_memory = bool(_value(candidate, "source_memory_id"))
        disclosure = (
            "personal" if has_memory and familiarity >= 0.55 and perceived_confidence >= 0.45
            else "bounded" if has_memory or familiarity >= 0.25
            else "minimal"
        )
        memory_role = self._memory_role(extension, has_memory, emotional_importance)
        activity_relation = self._activity_relation(action_kind, activity_transition)
        resolution = self._resolution_policy(action_kind, phase, extension)
        signature = self._signature(strategy, phase, span, shape, activity_relation, resolution)
        reasons = (
            f"energy:{energy_band}", f"topic_depth:{topic_depth}",
            f"initiative:{initiative_level}", f"trajectory:{phase}",
            "shape:recent_trajectory_avoided" if signature not in recent else "shape:bounded_reuse",
        )
        canonical = {
            "decision_id": _value(decision, "decision_id"), "actor_id": int(_value(continuity, "actor_id")),
            "strategy": strategy, "phase": phase, "energy": round(energy, 6),
            "span": span, "shape": shape, "pacing": pacing, "disclosure": disclosure,
            "activity": activity_relation, "resolution": resolution, "memory_role": memory_role,
            "extension": extension, "signature": signature,
        }
        digest = hashlib.blake2b(
            json.dumps(canonical, sort_keys=True, separators=(",", ":")).encode("utf-8"),
            digest_size=8,
        ).hexdigest()
        candidate_id = str(_value(candidate, "candidate_id", "conversation:none"))
        return ConversationChoreographyPlan(
            schema_version=1,
            choreography_id=f"choreography_{digest}",
            decision_id=str(_value(decision, "decision_id")),
            actor_id=int(_value(continuity, "actor_id")),
            rhetorical_strategy=strategy,
            trajectory_phase=phase,
            conversational_energy=round(energy, 6),
            energy_band=energy_band,
            response_span=span,
            answer_shape=shape,
            pacing=pacing,
            disclosure_depth=disclosure,
            initiative_level=initiative_level,
            activity_relation=activity_relation,
            resolution_policy=resolution,
            memory_role=memory_role,
            selected_extension=str(extension) if extension else None,
            trajectory_signature=signature,
            reason_codes=reasons,
            provenance_ids=(str(_value(decision, "decision_id")), candidate_id),
        )

    @staticmethod
    def _phase(depth: int, transition: str | None, action_kind: str) -> str:
        if action_kind in {"delay", "withdraw", "silence"}:
            return "suspend"
        if transition == "completed" or depth >= 8:
            return "resolve"
        if transition in {"interrupted", "displaced"}:
            return "return"
        if depth <= 1:
            return "open"
        if depth <= 4:
            return "deepen"
        return "complicate"

    @staticmethod
    def _strategy_options(
        action_kind: str, obligation: str, extension: str | None, depth: int,
    ) -> tuple[str, ...]:
        if action_kind != "speak":
            return ("return_to_work",) if action_kind in {"continue_activity", "delay"} else ("withhold",)
        if extension:
            return ("return_to_work" if extension == "continue_working" else str(extension),)
        if obligation == "answer":
            return ("direct", "qualify", "teach", "summarize") if depth >= 2 else ("direct", "qualify")
        return {
            "acknowledge": ("acknowledge", "reflect", "summarize"),
            "repair": ("repair", "qualify"),
            "clarify": ("clarify",),
            "follow_up": ("resume", "summarize"),
        }.get(obligation, ("direct",))

    @staticmethod
    def _span_options(
        action_kind: str, obligation: str, extension: str | None, energy_band: str,
    ) -> tuple[str, ...]:
        if action_kind != "speak":
            return ("fragment",)
        if extension:
            return ("normal", "extended") if energy_band == "high" else ("normal",)
        if obligation in {"acknowledge", "clarify"}:
            return ("fragment", "brief") if energy_band == "low" else ("brief", "normal")
        if energy_band == "low":
            return ("brief",)
        return ("brief", "normal", "extended") if energy_band == "high" else ("brief", "normal")

    @staticmethod
    def _shape_options(
        action_kind: str, obligation: str, perceived_confidence: float,
    ) -> tuple[str, ...]:
        if action_kind != "speak":
            return ("none",)
        if obligation == "answer":
            return ("qualified", "staged") if perceived_confidence < 0.45 else ("direct", "qualified", "staged")
        if obligation in {"clarify", "follow_up"}:
            return ("staged",)
        return ("direct", "qualified")

    @classmethod
    def _least_repeated_shape(
        cls,
        strategies: Sequence[str],
        spans: Sequence[str],
        shapes: Sequence[str],
        phase: str,
        recent: Sequence[str],
        seed: int,
    ) -> tuple[str, str, str]:
        options = list(itertools.product(strategies, spans, shapes))
        ranked = []
        for strategy, span, shape in options:
            prefix = f"{strategy}|{phase}|{span}|{shape}|"
            count = sum(item.startswith(prefix) for item in recent)
            recency = next((index for index, item in enumerate(reversed(recent), 1) if item.startswith(prefix)), 99)
            digest = hashlib.blake2b(
                f"{seed}|{strategy}|{span}|{shape}".encode("utf-8"), digest_size=4,
            ).digest()
            ranked.append((count, -recency, int.from_bytes(digest, "big"), strategy, span, shape))
        ranked.sort()
        return ranked[0][3], ranked[0][4], ranked[0][5]

    @staticmethod
    def _memory_role(extension: str | None, has_memory: bool, importance: float) -> str:
        if not has_memory:
            return "none"
        if extension == "compare":
            return "analogy"
        if extension == "reminisce":
            return "emotional_callback" if importance >= 0.55 else "anecdote"
        return "evidence"

    @staticmethod
    def _activity_relation(action_kind: str, transition: str | None) -> str:
        if action_kind == "withdraw":
            return "leave"
        if transition == "resumed":
            return "resume"
        if transition == "paused" or action_kind == "delay":
            return "pause"
        if transition == "continued" or action_kind in {"continue_activity", "silence"}:
            return "continue"
        return "none"

    @staticmethod
    def _resolution_policy(action_kind: str, phase: str, extension: str | None) -> str:
        if action_kind in {"delay", "withdraw"} or phase == "suspend":
            return "defer"
        if extension or phase in {"open", "deepen", "complicate", "return"}:
            return "open"
        return "complete"

    @staticmethod
    def _signature(
        strategy: str, phase: str, span: str, shape: str,
        activity: str, resolution: str,
    ) -> str:
        return "|".join((strategy, phase, span, shape, activity, resolution))
