"""Experimental character-owned attention over existing memory records.

This is a smaller alternative to personality-conditioned memory rewriting. The
lived memory remains unchanged. A typed author-owned profile may add a bounded
retrieval bonus for explicit semantic tags that some trusted upstream authority
has already attached to the memory.

The module does not infer tags, parse natural-language personality statements,
mutate MemoryUnit, or create a second memory store.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable

from .memory import MemoryUnit, activation, semantic_similarity


MAX_ATTENTION_BONUS = 1.0


@dataclass(frozen=True)
class MemoryAttentionProfile:
    tag_weights: dict[str, float]
    max_abs_bonus: float = MAX_ATTENTION_BONUS

    @classmethod
    def from_mapping(cls, data: dict[str, Any] | None) -> "MemoryAttentionProfile":
        raw = data or {}
        weights = raw.get("tag_weights", raw)
        normalized: dict[str, float] = {}
        if isinstance(weights, dict):
            for key, value in weights.items():
                try:
                    numeric = float(value)
                except (TypeError, ValueError):
                    continue
                normalized[str(key)] = max(-MAX_ATTENTION_BONUS, min(MAX_ATTENTION_BONUS, numeric))
        try:
            cap = abs(float(raw.get("max_abs_bonus", MAX_ATTENTION_BONUS))) if isinstance(raw, dict) else MAX_ATTENTION_BONUS
        except (TypeError, ValueError):
            cap = MAX_ATTENTION_BONUS
        return cls(tag_weights=normalized, max_abs_bonus=min(MAX_ATTENTION_BONUS, cap))

    def bonus_for(self, memory: MemoryUnit) -> tuple[float, tuple[str, ...]]:
        matches = tuple(sorted(tag for tag in memory.tags if tag in self.tag_weights))
        raw_bonus = sum(self.tag_weights[tag] for tag in matches)
        cap = max(0.0, min(MAX_ATTENTION_BONUS, float(self.max_abs_bonus)))
        bonus = max(-cap, min(cap, raw_bonus))
        return bonus, matches


@dataclass(frozen=True)
class MemoryAttentionScore:
    memory: MemoryUnit
    base_score: float
    attention_bonus: float
    total_score: float
    matched_tags: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "memory_id": self.memory.id,
            "base_score": round(float(self.base_score), 6),
            "attention_bonus": round(float(self.attention_bonus), 6),
            "total_score": round(float(self.total_score), 6),
            "matched_tags": list(self.matched_tags),
        }


def rank_with_memory_attention(
    memories: Iterable[MemoryUnit],
    query: str,
    now: float,
    profile: MemoryAttentionProfile | None = None,
    *,
    emotional_state_match: float = 0.0,
) -> list[MemoryAttentionScore]:
    """Pure deterministic ranking with an optional bounded subject attention bonus.

    The function intentionally does not record rehearsal/recall, alter salience,
    add tags, or write state. Integration with MemoryStore retrieval would be a
    separate experiment if this mechanism earns production use.
    """

    active_profile = profile or MemoryAttentionProfile(tag_weights={})
    scored: list[MemoryAttentionScore] = []
    for memory in memories:
        sem = semantic_similarity(query, memory.content)
        base = activation(memory, now, sem, emotional_state_match)
        bonus, matches = active_profile.bonus_for(memory)
        scored.append(MemoryAttentionScore(
            memory=memory,
            base_score=base,
            attention_bonus=bonus,
            total_score=base + bonus,
            matched_tags=matches,
        ))
    scored.sort(key=lambda item: item.total_score, reverse=True)
    return scored
