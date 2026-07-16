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


def developmental_fixture(engine) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "world_events": engine.world_events.to_list(),
        "subjective_experiences": engine.experiences.to_list(),
        "autobiographical_interpretations": engine.autobiographical_interpretations.to_list(),
        "autobiographical_evidence_links": [item.to_dict() for item in engine.autobiographical_evidence_links],
        "interpretation_status_events": engine.interpretation_status_events.to_list(),
        "interpretation_use_outcomes": [item.to_dict() for item in engine.interpretation_use_outcomes],
        "memory_connections": engine.memory_connections.to_list(),
        "skills": engine.skills.to_list(),
        "relationship_expectations": engine.relationship_expectations.to_list(),
        "dyadic_rituals": engine.dyadic_rituals.to_list(),
        "development_episodes": engine.development_episodes.to_list(),
        "development_signals": list(engine.development_signals),
        "earned_traits": [vars(item) for item in engine.ledger.earned_traits.values()],
    }


def developmental_fixture_bytes(engine) -> bytes:
    return json.dumps(
        developmental_fixture(engine), sort_keys=True, separators=(",", ":"), ensure_ascii=True,
    ).encode("ascii")
