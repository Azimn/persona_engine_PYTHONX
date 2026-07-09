"""Deterministic event classification before memory formation.

The classifier borrows the useful MindSculpt-style idea that not every event is
just undifferentiated text. It assigns memory type, relevance, and promotion
eligibility while preserving the existing memory firewall.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

CANONICAL_EVENT_TYPES = {
    "user_statement", "input", "world_fact", "sensorium", "belief", "interpretive_belief",
    "manual_authorized_fact", "dream_consolidation", "state_transition",
}
NONCANONICAL_EVENT_TYPES = {"speech", "renderer_output", "ui_state", "avatar_state", "voice_plan", "mock_response"}


@dataclass
class MemoryClassification:
    memory_type: str
    importance: float
    emotional_impact: float
    identity_relevance: float
    relationship_relevance: float
    somatic_relevance: float
    symbolic_relevance: float
    should_store: bool
    should_create_open_loop: bool
    should_create_symbol: bool
    tags: list[str] = field(default_factory=list)
    source_event_ids: list[str] = field(default_factory=list)
    canonical_truth: bool = False


def can_promote_to_canonical_memory(event_type: str, payload: dict[str, Any] | None = None) -> bool:
    """Return whether an event may become canonical memory truth."""
    event_type = str(event_type)
    payload = payload or {}
    if event_type in NONCANONICAL_EVENT_TYPES:
        return False
    if payload.get("response_is_canonical_truth") is False:
        return False
    if event_type in CANONICAL_EVENT_TYPES:
        return True
    return bool(payload.get("canonical_truth") is True)


class EventClassifier:
    """Character-agnostic event classifier."""

    def classify(self, event_type: str, payload: dict[str, Any] | None = None, event_id: str | int | None = None) -> MemoryClassification:
        payload = payload or {}
        text = " ".join(str(v).lower() for v in payload.values() if isinstance(v, (str, int, float)))
        canonical = can_promote_to_canonical_memory(event_type, payload)
        memory_type = self._memory_type(event_type, payload, text)
        importance = 0.25
        emotional = 0.0
        identity = 0.0
        relationship = 0.0
        somatic = 0.0
        symbolic = 0.0
        tags = [memory_type, str(event_type)]
        if any(w in text for w in ["accuse", "lied", "blame", "fault", "identity", "rewrite"]):
            emotional += 0.35
            relationship += 0.25
            identity += 0.25
            tags.append("conflict")
        if any(w in text for w in ["sorry", "apologize", "repair", "care", "trust"]):
            emotional += 0.20
            relationship += 0.35
            tags.append("repair")
        if event_type in {"sensorium", "world_fact"} or "sensor" in text:
            somatic += 0.35
            importance += 0.15
        if event_type in {"belief", "interpretive_belief"}:
            relationship += 0.20
            emotional += 0.25
            tags.append("interpretive")
        if event_type in {"symbol", "validated_symbol"} or any(w in text for w in ["promise", "nickname", "ritual"]):
            symbolic += 0.50
            tags.append("symbolic")
        importance = max(0.0, min(1.0, importance + emotional * 0.35 + identity * 0.35 + relationship * 0.25 + somatic * 0.20 + symbolic * 0.25))
        return MemoryClassification(
            memory_type=memory_type,
            importance=importance,
            emotional_impact=max(0.0, min(1.0, emotional)),
            identity_relevance=max(0.0, min(1.0, identity)),
            relationship_relevance=max(0.0, min(1.0, relationship)),
            somatic_relevance=max(0.0, min(1.0, somatic)),
            symbolic_relevance=max(0.0, min(1.0, symbolic)),
            should_store=canonical and importance >= 0.20,
            should_create_open_loop=emotional > 0.45 or identity > 0.4,
            should_create_symbol=symbolic > 0.45,
            tags=tags,
            source_event_ids=[str(event_id)] if event_id is not None else [],
            canonical_truth=canonical,
        )

    def _memory_type(self, event_type: str, payload: dict[str, Any], text: str) -> str:
        if event_type in {"sensorium", "world_fact"}:
            if any(k in payload for k in ["body", "sensor", "audio", "vision"]):
                return "somatic"
            return "environmental"
        if event_type in {"belief", "interpretive_belief"}:
            return "interpretive"
        if event_type in {"speech", "renderer_output"}:
            return "speech"
        if event_type in {"input", "user_statement"}:
            return "relational" if any(w in text for w in ["sorry", "care", "trust", "lie", "fault"]) else "episodic"
        if event_type in {"dream_consolidation"}:
            return "semantic"
        return "episodic"
