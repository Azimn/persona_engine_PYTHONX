"""Stable JSON fixtures for later C99 conformance work."""

from __future__ import annotations

import json
from typing import Any


def autobiographical_fixture(engine, experience_id: str) -> dict[str, Any]:
    experience = next(
        item for item in engine.experiences.experiences if item.experience_id == experience_id
    )
    event = engine.world_events.fetch(experience.world_event_id)
    return {
        "schema_version": 1,
        "world_event": event.to_dict() if event else None,
        "subjective_experience": experience.to_dict(),
        "autobiographical_interpretations": [
            item.to_dict() for item in engine.autobiographical_interpretations.for_experience(experience_id)
        ],
        "deferred_reinterpretations": [
            item.to_dict() for item in engine.deferred_reinterpretations
            if item.experience_id == experience_id
        ],
        "self_monitor": engine._last_self_monitor.to_dict() if engine._last_self_monitor else None,
        "synthesis": engine._last_synthesis.to_dict() if engine._last_synthesis else None,
        "action_decision": engine._last_action_decision.to_dict() if engine._last_action_decision else None,
        "performance_plan": engine._last_performance_plan.to_dict() if engine._last_performance_plan else None,
    }


def fixture_bytes(engine, experience_id: str) -> bytes:
    return json.dumps(
        autobiographical_fixture(engine, experience_id), sort_keys=True,
        separators=(",", ":"), ensure_ascii=True,
    ).encode("ascii")
