"""Deterministic replay utilities for diagnostic and canonical event histories.

Wayfarer replay follows causal ownership. Exogenous canonical experiences are
re-applied through public character interfaces. Derived state-transition records
are verification evidence and are not applied a second time. Renderer prose is
never replayed as causal input.
"""

from __future__ import annotations

import json
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from ..agent import CharacterAgent
from .continuity import CONTINUITY_SCHEMA_VERSION, canonical_continuity_eligible, state_digest as hash_state


class ReplayContractError(ValueError):
    """Raised when a purported continuity bundle violates replay authority rules."""


@dataclass
class ReplayResult:
    """Summary of deterministic replay state."""

    turns_replayed: int
    final_digest: dict[str, Any]
    semantic_digest: str = ""
    events_seen: int = 0
    root_events_replayed: int = 0
    derived_events_skipped: int = 0
    unsupported_root_events: list[str] = field(default_factory=list)

    @property
    def complete(self) -> bool:
        return not self.unsupported_root_events


def state_digest(agent: CharacterAgent) -> dict[str, Any]:
    """Return a compact deterministic semantic projection of runtime state."""

    engine = agent.engine
    body = engine.body.to_dict()
    world = engine.world.to_dict()
    return {
        "identity": engine.identity.name,
        "relationship": dict(vars(engine.relationship)),
        "pressures": {name: round(p.magnitude, 6) for name, p in sorted(engine.pressures.pressures.items())},
        "beliefs": dict(engine.belief_ledger.values),
        "memory_count": len(engine.memory.memories),
        "open_loop_count": len(engine.intentions.open_loops),
        "symbol_count": len(engine.symbols.symbols),
        "habit_count": len(engine.habits.habits),
        "timestep": engine.timestep,
        "body": {
            "energy": round(float(body.get("energy", 0.0)), 6),
            "fatigue": round(float(body.get("fatigue", 0.0)), 6),
            "tension": round(float(body.get("tension", 0.0)), 6),
            "need_for_movement": round(float(body.get("need_for_movement", 0.0)), 6),
            "recovery": body.get("recovery"),
        },
        "world": {
            "time_of_day": world.get("time_of_day"),
            "location": world.get("location"),
            "user_presence": world.get("user_presence"),
            "noise_level": world.get("noise_level"),
            "light_level": world.get("light_level"),
        },
        "sensorium_count": len(engine.sensorium.observations),
    }


def semantic_digest(agent: CharacterAgent) -> str:
    """Hash the stable semantic projection, not volatile timestamps/UUIDs."""

    return hash_state(state_digest(agent))


def export_event_log(persistence, character_id: str, user_id: str) -> list[dict[str, Any]]:
    """Export legacy diagnostic event-log rows for compatibility tooling."""

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


def replay_from_events(cartridge_path: str, events: list[dict[str, Any]], user_id: str = "replay_user") -> ReplayResult:
    """Legacy replay of diagnostic input events through a new engine instance."""

    db_path = str(Path(tempfile.mkdtemp()) / "replay_state.db")
    agent = CharacterAgent(cartridge_path=cartridge_path, user_id=user_id, db_path=db_path)
    turns = 0
    for event in events:
        if event.get("event_type") != "input":
            continue
        payload = event.get("payload") or {}
        user_text = payload.get("user_text")
        if not isinstance(user_text, str):
            continue
        agent.say(user_text, server_truth=payload.get("server_truth"), visible_context=payload.get("visible_context"))
        turns += 1
    projection = state_digest(agent)
    return ReplayResult(turns_replayed=turns, final_digest=projection, semantic_digest=hash_state(projection), events_seen=len(events), root_events_replayed=turns)


def validate_continuity_bundle(bundle: dict[str, Any]) -> list[dict[str, Any]]:
    """Validate canonical sequence and authority before replaying anything."""

    if not isinstance(bundle, dict):
        raise ReplayContractError("continuity bundle must be an object")
    if str(bundle.get("schema_version")) != CONTINUITY_SCHEMA_VERSION:
        raise ReplayContractError("unsupported continuity schema_version")
    events = list(bundle.get("events") or [])
    if not all(isinstance(event, dict) for event in events):
        raise ReplayContractError("continuity events must be objects")
    events.sort(key=lambda event: int(event.get("sequence", -1)))
    expected = int(bundle.get("after_sequence", 0)) + 1
    for event in events:
        sequence = int(event.get("sequence", -1))
        if sequence != expected:
            raise ReplayContractError(f"non-contiguous canonical sequence: expected {expected}, got {sequence}")
        if event.get("canonicality") != "canonical_event":
            raise ReplayContractError(f"event {sequence} is not canonical")
        payload = event.get("payload")
        if not isinstance(payload, dict):
            raise ReplayContractError(f"event {sequence} payload must be an object")
        event_type = str(event.get("event_type", ""))
        if not canonical_continuity_eligible(event_type, payload):
            raise ReplayContractError(f"event {sequence} is not authority-eligible for continuity")
        expected += 1
    return events


_DERIVED_EVENT_TYPES = {
    "state_transition",
    "sensorium",
    "dream_consolidation",
}


def replay_from_continuity_bundle(
    cartridge_path: str,
    bundle: dict[str, Any],
    *,
    user_id: str = "replay_user",
) -> ReplayResult:
    """Replay supported exogenous canonical events through public interfaces.

    Current replay roots:
    - ``input`` / ``user_statement`` through ``CharacterAgent.say``;
    - bounded ``sensor_observation`` through audio/vision observation APIs.

    Derived canonical records are skipped because replaying the root event will
    regenerate those consequences. Accepted world-action resolutions and manual
    authorized facts remain explicitly unsupported roots until their host-level
    replay contract is defined; the result reports them rather than silently
    pretending replay was complete.
    """

    events = validate_continuity_bundle(bundle)
    db_path = str(Path(tempfile.mkdtemp()) / "continuity_replay.db")
    agent = CharacterAgent(cartridge_path=cartridge_path, user_id=user_id, db_path=db_path)
    turns = 0
    replayed = 0
    derived = 0
    unsupported: list[str] = []

    for event in events:
        event_type = str(event["event_type"])
        payload = event["payload"]
        if event_type in {"input", "user_statement"}:
            user_text = payload.get("user_text") or payload.get("text")
            if not isinstance(user_text, str):
                raise ReplayContractError(f"{event_type} event lacks replayable user text")
            agent.say(user_text, server_truth=payload.get("server_truth"), visible_context=payload.get("visible_context"))
            turns += 1
            replayed += 1
            continue
        if event_type == "sensor_observation":
            sensor_type = payload.get("sensor_type")
            observation = payload.get("observation")
            if not isinstance(observation, dict):
                raise ReplayContractError("sensor_observation lacks bounded observation payload")
            if sensor_type == "audio":
                agent.observe_audio(dict(observation))
            elif sensor_type == "vision":
                agent.observe_vision(dict(observation))
            else:
                raise ReplayContractError(f"unsupported sensor type: {sensor_type}")
            replayed += 1
            continue
        if event_type in _DERIVED_EVENT_TYPES:
            derived += 1
            continue
        if event_type not in unsupported:
            unsupported.append(event_type)

    projection = state_digest(agent)
    return ReplayResult(
        turns_replayed=turns,
        final_digest=projection,
        semantic_digest=hash_state(projection),
        events_seen=len(events),
        root_events_replayed=replayed,
        derived_events_skipped=derived,
        unsupported_root_events=unsupported,
    )
