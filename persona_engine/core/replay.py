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


@dataclass
class ReplayResult:
    """Summary of replayed deterministic state."""

    turns_replayed: int
    final_digest: dict[str, Any]


def state_digest(agent: CharacterAgent) -> dict[str, Any]:
    """Return a compact deterministic digest of inspectable runtime state."""
    engine = agent.engine
    return {
        "relationship": dict(vars(engine.relationship)),
        "pressures": {name: round(p.magnitude, 6) for name, p in sorted(engine.pressures.pressures.items())},
        "beliefs": dict(engine.belief_ledger.values),
        "memory_count": len(engine.memory.memories),
        "open_loop_count": len(engine.intentions.open_loops),
        "symbol_count": len(engine.symbols.symbols),
        "habit_count": len(engine.habits.habits),
        "timestep": engine.timestep,
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


def replay_from_events(cartridge_path: str, events: list[dict[str, Any]], user_id: str = "replay_user") -> ReplayResult:
    """Replay canonical input events through a new engine instance."""
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
    return ReplayResult(turns_replayed=turns, final_digest=state_digest(agent))
