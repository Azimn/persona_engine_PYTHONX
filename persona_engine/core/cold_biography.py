"""Bounded read-through retrieval from canonical cold biography.

The archive is evidence, not an alternate memory authority. V1 is deliberately
narrow: only explicit recall requests may consult the current interlocutor's
canonical input history. Retrieved records are transient MemoryUnit candidates
and are never written back into resident memory automatically.
"""

from __future__ import annotations

import heapq
import re
from typing import Iterable

from .memory import KnowledgeSource, MemoryUnit, semantic_similarity

_RECALL_PATTERNS = (
    re.compile(r"\b(do you remember|remember when|what did i say|recall)\b", re.IGNORECASE),
    re.compile(r"\bwhat was\b.*\b(i told you|i said)\b", re.IGNORECASE),
)


def explicit_recall_request(text: str) -> bool:
    value = str(text or "")
    return any(pattern.search(value) for pattern in _RECALL_PATTERNS)


def _normalized(text: str) -> str:
    return " ".join(str(text or "").lower().split())


def retrieve_cold_biography(persistence, character_id: str, user_id: str, query: str, *, top_k: int = 4) -> list[MemoryUnit]:
    """Return a bounded set of transient candidates from canonical input history."""

    if top_k <= 0 or not explicit_recall_request(query):
        return []
    query_norm = _normalized(query)
    heap: list[tuple[float, int, str, MemoryUnit]] = []
    for event in persistence.iter_continuity_events(character_id, user_id, event_type="input"):
        payload = event.get("payload") or {}
        user_text = str(payload.get("user_text", "")).strip()
        if not user_text or _normalized(user_text) == query_norm:
            continue
        score = float(semantic_similarity(query, user_text))
        if score <= 0.0:
            continue
        event_uuid = str(event.get("event_uuid", ""))
        candidate = MemoryUnit(
            content=f"I heard you say: {user_text}",
            created_at=float(event.get("wall_time", 0.0) or 0.0),
            id=f"cold_{event_uuid}",
            source=KnowledgeSource.USER_TOLD,
            tags={"canonical_user_statement", "cold_biography"},
        )
        item = (score, int(event.get("sequence", 0) or 0), event_uuid, candidate)
        if len(heap) < top_k:
            heapq.heappush(heap, item)
        elif item[:3] > heap[0][:3]:
            heapq.heapreplace(heap, item)
    return [item[3] for item in sorted(heap, key=lambda item: item[:3], reverse=True)]


def merge_recall_candidates(query: str, live: Iterable[MemoryUnit], cold: Iterable[MemoryUnit], *, top_k: int = 4) -> list[MemoryUnit]:
    """Deduplicate by semantic content and rank explicit recall by relevance."""

    unique: dict[str, MemoryUnit] = {}
    for memory in [*list(live), *list(cold)]:
        key = _normalized(memory.content)
        if key not in unique or "cold_biography" not in memory.tags:
            unique[key] = memory
    ranked = sorted(
        unique.values(),
        key=lambda memory: (semantic_similarity(query, memory.content), memory.created_at, memory.id),
        reverse=True,
    )
    return ranked[:max(0, int(top_k))]
