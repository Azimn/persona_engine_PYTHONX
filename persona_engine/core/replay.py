"""Deterministic event-log replay utilities.

Replay reprocesses canonical input events through the deterministic core and mock
renderer path. It is intended for debugging state transitions and future C99
port conformance, not for reproducing exact generated prose from an LLM.
"""

from __future__ import annotations

import json
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ..agent import CharacterAgent
from .audio_sensor import AudioObservation
from .vision_sensor import VisionObservation


def _normalized(value: Any) -> Any:
    if isinstance(value, float):
        return round(value, 6)
    if isinstance(value, dict):
        return {key: _normalized(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_normalized(item) for item in value]
    return value


@dataclass
class ReplayResult:
    """Summary of replayed deterministic state."""

    turns_replayed: int
    final_digest: dict[str, Any]
    events_replayed: int = 0


def state_digest(agent: CharacterAgent) -> dict[str, Any]:
    """Return a compact deterministic digest of inspectable runtime state."""
    engine = agent.engine
    life = engine.life_state
    return {
        "relationship": dict(vars(engine.relationship)),
        "pressures": {name: round(p.magnitude, 6) for name, p in sorted(engine.pressures.pressures.items())},
        "beliefs": dict(engine.belief_ledger.values),
        "memory_count": len(engine.memory.memories),
        "open_loop_count": len(engine.intentions.open_loops),
        "symbol_count": len(engine.symbols.symbols),
        "habit_count": len(engine.habits.habits),
        "timestep": engine.timestep,
        "life": {
            "current_activity": life.current_activity,
            "current_intention": life.current_intention,
            "attention_target": life.attention_target,
            "unresolved_concern": life.unresolved_concern,
            "activity_status": life.activity_status,
            "entropy": round(life.entropy, 6),
            "rng_counter": life.rng_counter,
            "events": [_normalized(event.to_dict()) for event in life.events],
        },
        "world_events": _normalized(engine.world_events.to_list()),
        "subjective_experiences": _normalized(engine.experiences.to_list()),
        "capability_artifacts": _normalized(engine.capability_artifacts.to_list()),
        "self_monitor": _normalized(engine._last_self_monitor.to_dict())
        if getattr(engine, "_last_self_monitor", None) else None,
        "action_decision": {
            "action_kind": engine._last_action_decision.action_kind,
            "intention_id": engine._last_action_decision.intention_id,
            "target": engine._last_action_decision.target,
            "communicative_function": engine._last_action_decision.communicative_function,
            "selected_regulation_id": engine._last_action_decision.selected_regulation_id,
        } if getattr(engine, "_last_action_decision", None) else None,
    }


def export_event_log(persistence, character_id: str, user_id: str) -> list[dict[str, Any]]:
    """Export all event-log rows for a character/user pair."""
    conn = persistence.conn
    rows = []
    try:
        cur = conn.execute(
            "SELECT id,timestep,event_type,payload,created_at FROM event_log WHERE character_id=? AND user_id=? ORDER BY id",
            (character_id, user_id),
        )
        for event_id, timestep, event_type, payload_text, created_at in cur.fetchall():
            try:
                payload = json.loads(payload_text)
            except json.JSONDecodeError:
                payload = {}
            rows.append({"id": event_id, "timestep": timestep, "event_type": event_type, "payload": payload, "created_at": created_at})
        return rows
    finally:
        conn.close()


def replay_events_into_agent(agent: CharacterAgent, events: list[dict[str, Any]]) -> ReplayResult:
    """Replay approved canonical events through normal agent channels."""

    turns = 0
    replayed = 0
    for event in sorted(events, key=lambda item: int(item.get("sequence", item.get("id", 0)))):
        event_type = event.get("event_type")
        payload = event.get("payload") or {}
        if event_type == "input":
            user_text = payload.get("user_text")
            if not isinstance(user_text, str):
                continue
            agent.say(
                user_text,
                server_truth=payload.get("submitted_server_truth", payload.get("server_truth")),
                visible_context=payload.get("submitted_visible_context", payload.get("visible_context")),
                event_time=payload.get("event_time"),
            )
            turns += 1
            replayed += 1
        elif event_type == "sensor_observation" and payload.get("sensor_type") == "audio":
            agent.observe_audio(AudioObservation(**dict(payload.get("observation") or {})))
            replayed += 1
        elif event_type == "sensor_observation" and payload.get("sensor_type") == "vision":
            agent.observe_vision(VisionObservation(**dict(payload.get("observation") or {})))
            replayed += 1
        elif event_type == "world_action_resolution":
            agent.propose_world_action(
                str(payload.get("action_type", "")),
                dict(payload.get("payload") or {}),
                event_time=payload.get("event_time"),
            )
            replayed += 1
    return ReplayResult(turns_replayed=turns, final_digest=state_digest(agent), events_replayed=replayed)


def replay_from_events(cartridge_path: str, events: list[dict[str, Any]], user_id: str = "replay_user") -> ReplayResult:
    """Replay canonical events through a new engine instance."""
    db_path = str(Path(tempfile.mkdtemp()) / "replay_state.db")
    agent = CharacterAgent(cartridge_path=cartridge_path, user_id=user_id, db_path=db_path)
    return replay_events_into_agent(agent, events)
