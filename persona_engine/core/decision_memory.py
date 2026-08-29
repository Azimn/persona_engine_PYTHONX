"""Bounded memory evidence for current conduct selection.

This module is intentionally small. It does not create a new memory store,
relationship model, or belief authority. It answers one narrow longitudinal
question: when the current interaction asks for trust, commitment, or
cooperation, is there retrieved unresolved relationship history that should
qualify the character's conduct?

Memory is evidence, not authority. Stronger identity, world, host, and explicit
resistance gates remain outside this module and continue to win.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Iterable

from .memory import MemoryUnit


_SENSITIVE_PHRASES = (
    "trust me",
    "believe me",
    "rely on me",
    "count on me",
    "promise me",
    "make a promise",
    "commit to",
    "join me",
    "join us",
    "help me",
    "help us",
    "cooperate",
    "work with me",
    "work with us",
)


@dataclass(frozen=True)
class HistoryDecisionEvidence:
    active: bool = False
    strength: float = 0.0
    memory_ids: tuple[str, ...] = ()
    reason: str = "none"

    def to_dict(self) -> dict:
        return asdict(self)


def evaluate_history_for_decision(
    user_text: str,
    retrieved_memories: Iterable[MemoryUnit],
    relationship,
) -> HistoryDecisionEvidence:
    """Return bounded contextual caution from already retrieved lived history.

    Activation requires all of the following:
    1. the current request concerns trust/commitment/cooperation,
    2. the relationship still carries unresolved conflict,
    3. at least one retrieved memory is unresolved and relationship-relevant.

    This prevents old, already-repaired conflict from permanently shadowing
    future conduct merely because an immutable episode still exists in memory.
    """

    lowered = str(user_text or "").lower()
    if not any(phrase in lowered for phrase in _SENSITIVE_PHRASES):
        return HistoryDecisionEvidence()

    unresolved_conflict = float(getattr(relationship, "unresolved_conflict", 0.0) or 0.0)
    if unresolved_conflict <= 0.0:
        return HistoryDecisionEvidence()

    candidates = [
        memory
        for memory in retrieved_memories
        if bool(getattr(memory, "unresolved", False))
        and float(getattr(memory, "relationship_relevance", 0.0) or 0.0) >= 0.40
    ]
    if not candidates:
        return HistoryDecisionEvidence()

    scored = sorted(
        (
            min(
                1.0,
                max(0.0, float(memory.emotional_intensity))
                * max(0.0, float(memory.relationship_relevance))
                + min(0.25, unresolved_conflict * 0.25),
            ),
            memory,
        )
        for memory in candidates
    , key=lambda item: (item[0], float(item[1].created_at), str(item[1].id)))
    strength = scored[-1][0]
    if strength < 0.30:
        return HistoryDecisionEvidence()

    # Keep only a tiny deterministic provenance set. Count must not amplify the
    # signal, and equal-strength candidates must never require comparing
    # MemoryUnit objects directly.
    selected = tuple(memory.id for _, memory in scored[-2:])
    return HistoryDecisionEvidence(
        active=True,
        strength=round(strength, 3),
        memory_ids=selected,
        reason="unresolved_relationship_history",
    )
