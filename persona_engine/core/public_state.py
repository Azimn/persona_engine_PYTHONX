"""Public-facing organism status projection for UI consumers.

This module deliberately converts private numeric state into categorical public
signals before any UI receives it. The UI renders these values only; it does not
interpret raw private state or mutate organism state.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any


@dataclass(frozen=True)
class PublicStatus:
    """Categorical status safe for a semi-embodiment UI."""

    presence: str
    avatar_state: str
    posture: str
    orientation: str
    attention: str
    energy: str
    tension: str
    comfort: str
    sensory_load: str
    movement_need: str
    world: str
    light: str
    noise: str
    routine: str
    current_mode: str

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


def bucket(value: float, low_label: str = "low", mid_label: str = "moderate", high_label: str = "high") -> str:
    if value >= 0.70:
        return high_label
    if value >= 0.35:
        return mid_label
    return low_label


def inverted_bucket(value: float) -> str:
    if value >= 0.70:
        return "high"
    if value >= 0.35:
        return "limited"
    return "depleted"


def derive_avatar_state(body, relationship, affect_bucket: str, dominant_pressure: str | None = None) -> str:
    """Map private state into one safe avatar/status label."""

    recovery = getattr(body, "recovery_state", "stable")
    tension = getattr(body, "tension", 0.0)
    sensory_load = getattr(body, "sensory_load", 0.0)
    fatigue = getattr(body, "fatigue", 0.0)
    guardedness = getattr(relationship, "guardedness", 0.0)
    dominant = (dominant_pressure or "").lower()
    if recovery == "depleted" or fatigue > 0.75:
        return "tired"
    if sensory_load > 0.75:
        return "overloaded"
    if affect_bucket == "HIGH" or tension > 0.72:
        return "tense"
    if dominant in {"anger", "shame", "fear"} or guardedness > 0.68:
        return "guarded"
    if dominant in {"curiosity", "attachment"} and affect_bucket == "LOW":
        return "attentive"
    if recovery == "restless":
        return "restless"
    return "neutral"


def current_mode_from_state(body, relationship, affect_bucket: str) -> str:
    if getattr(body, "recovery_state", "stable") in {"depleted", "strained"}:
        return "recovering"
    if affect_bucket == "HIGH":
        return "withdrawn"
    if getattr(relationship, "tension", 0.0) > 0.55:
        return "watchful"
    if getattr(relationship, "trust", 0.0) > 0.65 and affect_bucket == "LOW":
        return "present"
    return "settled"


def public_status_from_engine(engine, affect_bucket: str | None = None, dominant_pressure: str | None = None) -> PublicStatus:
    """Project an engine instance into categorical UI status."""

    body = engine.body
    world = engine.world
    relationship = engine.relationship
    affect = affect_bucket or "LOW"
    dominant = dominant_pressure or (engine.pressures.top().name if engine.pressures.top() else "calm")
    return PublicStatus(
        presence="available" if world.user_presence in {"present", "active", "returned"} else "quiet",
        avatar_state=derive_avatar_state(body, relationship, affect, dominant),
        posture=str(body.posture),
        orientation=str(body.orientation),
        attention=str(body.attention_target),
        energy=bucket(body.energy, "low", "steady", "high"),
        tension=bucket(body.tension),
        comfort=bucket(body.comfort, "uncomfortable", "mixed", "comfortable"),
        sensory_load=bucket(body.sensory_load),
        movement_need=bucket(body.need_for_movement),
        world=str(world.zone),
        light=str(world.light_level),
        noise=str(world.noise_level),
        routine=str(world.routine_state),
        current_mode=current_mode_from_state(body, relationship, affect),
    )


def debug_snapshot_from_engine(engine) -> dict[str, Any]:
    """Private debug view for development. Not intended for public UI mode."""

    recent_events = engine.world_events.recent(20) if hasattr(engine, "world_events") else []
    recent_experiences = engine.experiences.recent(20) if hasattr(engine, "experiences") else []
    experiences_by_event: dict[str, list[dict[str, Any]]] = {}
    for experience in recent_experiences:
        experiences_by_event.setdefault(experience.world_event_id, []).append(experience.to_dict())
    return {
        "timestep": engine.timestep,
        "relationship": dict(vars(engine.relationship)),
        "pressures": {k: vars(v) for k, v in engine.pressures.pressures.items()},
        "body": engine.body.to_dict(),
        "world": engine.world.to_dict(),
        "intentions": [vars(i) for i in engine.intentions.intentions],
        "open_loops": [vars(l) for l in engine.intentions.open_loops],
        "symbols": [vars(s) for s in engine.symbols.symbols.values()],
        "habits": [vars(h) for h in engine.habits.habits.values()],
        "memory_count": len(engine.memory.memories),
        "life_inspector": {
            "state": engine.life_state.to_dict() if hasattr(engine, "life_state") else {},
            "catch_up": dict(getattr(engine, "last_catch_up_summary", {})),
            "objective_events": [event.to_dict() for event in recent_events],
            "subjective_experiences": [experience.to_dict() for experience in recent_experiences],
            "discrepancies": [
                {
                    "world_event_id": event.event_id,
                    "objective": event.outcome,
                    "subjective": [item["perceived_summary"] for item in experiences_by_event.get(event.event_id, [])],
                    "interpretations": [item["interpretation"] for item in experiences_by_event.get(event.event_id, [])],
                }
                for event in recent_events if experiences_by_event.get(event.event_id)
            ],
            "learning_artifacts": [item.to_dict() for item in getattr(engine, "capability_artifacts", []).artifacts]
            if hasattr(getattr(engine, "capability_artifacts", None), "artifacts") else [],
            "retrievals": list(getattr(engine, "_last_retrieved_memory_trace", [])),
        },
    }
