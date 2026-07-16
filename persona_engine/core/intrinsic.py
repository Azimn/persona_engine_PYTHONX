"""Bounded intrinsic motivation and situated action selection.

The engine supplies the mechanism; cartridges supply what a character wants
and the activities through which those wants can be pursued.  Selection is
deterministic, small, and produces an inspectable decision rather than prose.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
import hashlib
import math
from typing import Any, Mapping


ACTION_TYPES = frozenset({
    "speak",
    "gesture",
    "continue_activity",
    "observe",
    "silence",
    "world_action",
})


def _clamp(value: float) -> float:
    number = float(value)
    return max(0.0, min(1.0, number)) if math.isfinite(number) else 0.0


def _bounded_signed(value: float) -> float:
    number = float(value)
    return max(-1.0, min(1.0, number)) if math.isfinite(number) else 0.0


@dataclass(frozen=True)
class IntrinsicWant:
    want_id: str
    description: str
    baseline: float
    neglect_gain: float
    satisfaction: float

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "IntrinsicWant":
        return cls(
            want_id=str(data["id"]),
            description=str(data["description"]),
            baseline=_clamp(data["baseline"]),
            neglect_gain=_clamp(data["neglect_gain"]),
            satisfaction=_clamp(data["satisfaction"]),
        )


@dataclass(frozen=True)
class IntrinsicActivity:
    activity_id: str
    want_id: str
    description: str
    intention: str
    attention_target: str
    action_type: str
    target: str
    base_utility: float
    energy_cost: float
    novelty_weight: float
    interruptible: bool
    visibility: str
    performance_cue: str
    pressure_affinities: tuple[tuple[str, float], ...] = ()

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "IntrinsicActivity":
        affinities = data.get("pressure_affinities", {})
        return cls(
            activity_id=str(data["id"]),
            want_id=str(data["want_id"]),
            description=str(data["description"]),
            intention=str(data["intention"]),
            attention_target=str(data["attention_target"]),
            action_type=str(data["action_type"]),
            target=str(data.get("target", "immediate surroundings")),
            base_utility=_bounded_signed(data.get("base_utility", 0.0)),
            energy_cost=_clamp(data.get("energy_cost", 0.0)),
            novelty_weight=_clamp(data.get("novelty_weight", 0.0)),
            interruptible=bool(data.get("interruptible", True)),
            visibility=str(data.get("visibility", "observable")),
            performance_cue=str(data.get("performance_cue", "")),
            pressure_affinities=tuple(sorted((str(key), _bounded_signed(value)) for key, value in affinities.items())),
        )


@dataclass
class IntrinsicState:
    want_levels: dict[str, float] = field(default_factory=dict)
    neglect_ticks: dict[str, int] = field(default_factory=dict)
    last_selection_tick: int = -1
    selected_want_id: str | None = None
    selected_activity_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Mapping[str, Any] | None) -> "IntrinsicState":
        if not data:
            return cls()
        return cls(
            want_levels={str(k): _clamp(v) for k, v in dict(data.get("want_levels", {})).items()},
            neglect_ticks={str(k): max(0, int(v)) for k, v in dict(data.get("neglect_ticks", {})).items()},
            last_selection_tick=int(data.get("last_selection_tick", -1)),
            selected_want_id=data.get("selected_want_id"),
            selected_activity_id=data.get("selected_activity_id"),
        )


@dataclass(frozen=True)
class ActionDecision:
    decision_id: str
    tick: int
    want_id: str
    activity_id: str
    action_type: str
    target: str
    intention: str
    activity_description: str
    utility: float
    score_breakdown: tuple[tuple[str, float], ...]
    selection_reason: tuple[str, ...]
    visibility: str
    interruptible: bool
    performance_cue: str

    @property
    def requires_renderer(self) -> bool:
        return self.action_type == "speak"

    def to_dict(self) -> dict[str, Any]:
        raw = asdict(self)
        raw["requires_renderer"] = self.requires_renderer
        return raw

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "ActionDecision":
        fields = {key: data[key] for key in cls.__dataclass_fields__ if key in data}
        fields["score_breakdown"] = tuple(tuple(item) for item in fields.get("score_breakdown", ()))
        fields["selection_reason"] = tuple(fields.get("selection_reason", ()))
        return cls(**fields)


class IntrinsicMotivationEngine:
    """Select one authored activity from bounded existing organism state."""

    def __init__(self, wants: tuple[IntrinsicWant, ...] = (), activities: tuple[IntrinsicActivity, ...] = (),
                 selection_interval_ticks: int = 6):
        self.wants = tuple(sorted(wants, key=lambda item: item.want_id))
        self.activities = tuple(sorted(activities, key=lambda item: item.activity_id))
        self.selection_interval_ticks = max(1, int(selection_interval_ticks))

    @classmethod
    def from_cartridge(cls, data: Mapping[str, Any] | None) -> "IntrinsicMotivationEngine":
        raw = dict(data or {})
        return cls(
            wants=tuple(IntrinsicWant.from_dict(item) for item in raw.get("wants", [])),
            activities=tuple(IntrinsicActivity.from_dict(item) for item in raw.get("activities", [])),
            selection_interval_ticks=int(raw.get("selection_interval_ticks", 6)),
        )

    def initialize_state(self, state: IntrinsicState) -> None:
        for want in self.wants:
            state.want_levels.setdefault(want.want_id, want.baseline)
            state.neglect_ticks.setdefault(want.want_id, 0)

    def select(
        self,
        state: IntrinsicState,
        *,
        companion_id: str,
        tick: int,
        energy: float,
        restlessness: float,
        pressures: Mapping[str, float],
        force: bool = False,
    ) -> ActionDecision | None:
        self.initialize_state(state)
        if not self.activities:
            return None
        if not force and state.last_selection_tick >= 0 and tick - state.last_selection_tick < self.selection_interval_ticks:
            return None

        candidates: list[tuple[float, IntrinsicActivity, tuple[tuple[str, float], ...]]] = []
        wants_by_id = {item.want_id: item for item in self.wants}
        for activity in self.activities:
            want = wants_by_id[activity.want_id]
            level = state.want_levels[want.want_id]
            neglect = min(0.35, state.neglect_ticks[want.want_id] * want.neglect_gain)
            pressure = sum(_clamp(pressures.get(name, 0.0)) * weight for name, weight in activity.pressure_affinities)
            novelty = _clamp(restlessness) * activity.novelty_weight
            persistence = 0.08 if state.selected_activity_id == activity.activity_id else 0.0
            energy_penalty = max(0.0, activity.energy_cost - _clamp(energy)) * 0.70
            parts = (
                ("want", round(level, 6)),
                ("neglect", round(neglect, 6)),
                ("base_utility", round(activity.base_utility, 6)),
                ("pressure", round(pressure, 6)),
                ("novelty", round(novelty, 6)),
                ("persistence", round(persistence, 6)),
                ("energy_penalty", round(-energy_penalty, 6)),
            )
            score = sum(value for _, value in parts)
            candidates.append((score, activity, parts))

        score, selected, parts = sorted(candidates, key=lambda item: (-item[0], item[1].activity_id))[0]
        for want in self.wants:
            if want.want_id == selected.want_id:
                state.want_levels[want.want_id] = _clamp(state.want_levels[want.want_id] - want.satisfaction)
                state.neglect_ticks[want.want_id] = 0
            else:
                state.want_levels[want.want_id] = _clamp(state.want_levels[want.want_id] + want.neglect_gain)
                state.neglect_ticks[want.want_id] += 1
        state.last_selection_tick = int(tick)
        state.selected_want_id = selected.want_id
        state.selected_activity_id = selected.activity_id

        decision_key = f"{companion_id}:{tick}:{selected.want_id}:{selected.activity_id}"
        decision_id = "decision_" + hashlib.blake2b(decision_key.encode("utf-8"), digest_size=8).hexdigest()
        reason = ["highest bounded intrinsic utility"]
        if dict(parts)["neglect"] > 0:
            reason.append("neglected want gained priority")
        if dict(parts)["pressure"] > 0:
            reason.append("current pressure supported this activity")
        if dict(parts)["energy_penalty"] < 0:
            reason.append("low energy reduced an effortful activity")
        return ActionDecision(
            decision_id=decision_id,
            tick=int(tick),
            want_id=selected.want_id,
            activity_id=selected.activity_id,
            action_type=selected.action_type,
            target=selected.target,
            intention=selected.intention,
            activity_description=selected.description,
            utility=round(score, 6),
            score_breakdown=parts,
            selection_reason=tuple(reason),
            visibility=selected.visibility,
            interruptible=selected.interruptible,
            performance_cue=selected.performance_cue,
        )
