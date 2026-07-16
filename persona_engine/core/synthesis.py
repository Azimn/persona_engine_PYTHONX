"""Bounded synthesis of existing engine influences before situated action."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
from typing import Iterable


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


def derive_integration_capacity(
    *,
    energy: float,
    fatigue: float,
    sensory_load: float,
    dominant_pressure: float,
    unresolved_conflict: float,
    open_loop_count: int,
    interruption_load: float,
    recent_failure: float,
) -> float:
    """Derive current cognitive organization from existing bounded state."""

    capacity = (
        0.32
        + 0.40 * _clamp(energy)
        + 0.20 * (1.0 - _clamp(fatigue))
        - 0.15 * _clamp(sensory_load)
        - 0.25 * _clamp(dominant_pressure)
        - 0.10 * _clamp(unresolved_conflict)
        - 0.08 * min(1.0, max(0, int(open_loop_count)) / 4.0)
        - 0.07 * _clamp(interruption_load)
        - 0.08 * _clamp(recent_failure)
    )
    return round(_clamp(capacity), 6)


def field_width_for_capacity(capacity: float) -> int:
    capacity = _clamp(capacity)
    if capacity >= 0.75:
        return 6
    if capacity >= 0.50:
        return 4
    if capacity >= 0.25:
        return 2
    return 1


@dataclass(frozen=True)
class SynthesisInfluence:
    influence_id: str
    kind: str
    label: str
    strength: float
    immediate: bool = False
    emotional_congruence: float = 0.0
    contradictory: bool = False
    reality_support: float = 0.0

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class SynthesisResult:
    synthesis_id: str
    integration_capacity: float
    field_width: int
    considered_influences: tuple[SynthesisInfluence, ...]
    selected_intention_id: str | None
    selected_habit_id: str | None
    selected_intrinsic_proposal_id: str | None
    selected_regulation_candidate_id: str | None
    selected_social_hypothesis_ids: tuple[str, ...]
    selected_skill_id: str | None
    inhibited_influences: tuple[SynthesisInfluence, ...]
    unresolved_conflicts: tuple[str, ...]
    reality_support: float
    selection_reason: tuple[str, ...]

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class ActionCompletion:
    intention_id: str | None
    attempted_action: str
    world_event_id: str
    outcome_status: str
    execution_quality: float
    expected_outcome: str
    actual_outcome: str
    discrepancy: str
    synthesis_reference: str | None
    subjective_interpretation_reference: str | None

    def to_dict(self) -> dict:
        return asdict(self)


def _rank(influence: SynthesisInfluence, capacity: float) -> float:
    strain = 1.0 - capacity
    score = _clamp(influence.strength)
    if influence.immediate:
        score += 0.24 * strain
    if influence.kind == "pressure":
        score += 0.20 * strain
    if influence.kind == "habit":
        score += 0.22 * strain
    if influence.kind == "memory":
        score += 0.16 * strain * _clamp(influence.emotional_congruence)
    if influence.kind in {"intention", "goal"} and not influence.immediate:
        score -= 0.14 * strain
    if influence.contradictory:
        if capacity < 0.50:
            score -= 0.38 * strain
        else:
            score += 0.06 * capacity
    if influence.kind == "regulation":
        label = influence.label
        if capacity < 0.35 and label in {"continue_habitually", "withdraw", "double_down"}:
            score += 0.12 * strain
        elif capacity < 0.50 and label in {"delay", "pause", "ask_clarification"}:
            score += 0.06
        elif capacity >= 0.65 and label in {"self_correct", "defer_judgment"}:
            score += 0.04
    if influence.kind == "autobiographical_meaning":
        score += 0.10 * _clamp(influence.emotional_congruence)
        if influence.contradictory:
            if capacity >= 0.60:
                score += 0.05 * capacity
            else:
                score -= 0.10 * (1.0 - capacity)
    return round(score, 6)


def synthesize(influences: Iterable[SynthesisInfluence], integration_capacity: float) -> SynthesisResult:
    """Select a bounded field from already-computed structured influences."""

    capacity = _clamp(integration_capacity)
    width = field_width_for_capacity(capacity)
    bounded = tuple(influences)[:32]
    ranked = sorted(bounded, key=lambda item: (-_rank(item, capacity), item.kind, item.influence_id))
    considered_items: list[SynthesisInfluence] = []
    regulation_selected = False
    for item in ranked:
        if len(considered_items) >= width:
            break
        if item.kind == "regulation":
            if regulation_selected:
                continue
            regulation_selected = True
        considered_items.append(item)
    considered = tuple(considered_items)
    considered_ids = {item.influence_id for item in considered}
    inhibited = tuple(item for item in ranked if item.influence_id not in considered_ids)
    intentions = [item for item in considered if item.kind == "intention"]
    habits = [item for item in considered if item.kind == "habit"]
    intrinsic = [item for item in considered if item.kind == "intrinsic_proposal"]
    regulation = [item for item in considered if item.kind == "regulation"]
    social = [item for item in considered if item.kind == "social_model"]
    skills = [item for item in considered if item.kind == "skill"]
    conflicts = tuple(
        item.influence_id for item in bounded
        if item.kind in {"open_loop", "relationship_conflict"} or item.contradictory
    )
    support_values = [item.reality_support for item in considered if item.reality_support > 0.0]
    reality_support = round(sum(support_values) / len(support_values), 6) if support_values else 0.0
    reasons = [f"field_width:{width}"]
    if capacity < 0.50:
        reasons.append("capacity:narrow")
    if habits:
        reasons.append("habit:available")
    if any(item.kind == "pressure" for item in considered):
        reasons.append("pressure:dominant")
    if any(item.contradictory for item in inhibited):
        reasons.append("contradiction:inhibited")
    autobiographical = [item for item in considered if item.kind == "autobiographical_meaning"]
    if autobiographical:
        reasons.extend(f"autobiographical:{item.influence_id.removeprefix('autobiographical:')}" for item in autobiographical)
    canonical = {
        "capacity": round(capacity, 6),
        "width": width,
        "considered": [item.influence_id for item in considered],
        "inhibited": [item.influence_id for item in inhibited],
        "selected_regulation": regulation[0].influence_id.removeprefix("regulation:") if regulation else None,
    }
    digest = hashlib.blake2b(json.dumps(canonical, sort_keys=True).encode("utf-8"), digest_size=8).hexdigest()
    return SynthesisResult(
        synthesis_id=f"synthesis_{digest}",
        integration_capacity=round(capacity, 6),
        field_width=width,
        considered_influences=considered,
        selected_intention_id=intentions[0].influence_id.removeprefix("intention:") if intentions else None,
        selected_habit_id=habits[0].influence_id.removeprefix("habit:") if habits else None,
        selected_intrinsic_proposal_id=(
            intrinsic[0].influence_id.removeprefix("intrinsic:") if intrinsic else None
        ),
        selected_regulation_candidate_id=(
            regulation[0].influence_id.removeprefix("regulation:") if regulation else None
        ),
        selected_social_hypothesis_ids=tuple(
            item.influence_id.removeprefix("social:") for item in social
        ),
        selected_skill_id=skills[0].influence_id.removeprefix("skill:") if skills else None,
        inhibited_influences=inhibited,
        unresolved_conflicts=conflicts,
        reality_support=reality_support,
        selection_reason=tuple(reasons),
    )
