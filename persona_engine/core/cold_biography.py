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

# Recall scaffolding describes the retrieval act rather than the remembered
# subject. It must not be allowed to ground an autobiographical match by itself.
_RECALL_SCAFFOLD = {
    "a", "about", "an", "and", "did", "do", "i", "me", "my", "old", "please",
    "recall", "remember", "said", "say", "tell", "the", "this", "that", "told",
    "was", "what", "when", "you", "your",
}


def explicit_recall_request(text: str) -> bool:
    value = str(text or "")
    return any(pattern.search(value) for pattern in _RECALL_PATTERNS)


def _normalized(text: str) -> str:
    return " ".join(str(text or "").lower().split())


def _tokens(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9']+", str(text or "").lower()))


def recall_focus_tokens(query: str) -> set[str]:
    """Return lexical anchors that describe what is being recalled.

    V1 intentionally prefers a grounded miss over a semantically plausible false
    memory. Every remaining topical query token must occur in a candidate before
    semantic similarity is allowed to rank it. If the question provides no
    topical anchor, cold recall fails closed until a richer index is justified.
    """

    return {token for token in _tokens(query) if token not in _RECALL_SCAFFOLD and len(token) > 1}


def grounded_recall_match(query: str, candidate_text: str) -> bool:
    focus = recall_focus_tokens(query)
    if not focus:
        return False
    return focus.issubset(_tokens(candidate_text))


def retrieve_cold_biography(persistence, character_id: str, user_id: str, query: str, *, top_k: int = 4) -> list[MemoryUnit]:
    """Return a bounded set of grounded transient candidates from canonical input history."""

    if top_k <= 0 or not explicit_recall_request(query):
        return []
    query_norm = _normalized(query)
    heap: list[tuple[float, int, str, MemoryUnit]] = []
    for event in persistence.iter_continuity_events(character_id, user_id, event_type="input"):
        payload = event.get("payload") or {}
        user_text = str(payload.get("user_text", "")).strip()
        if not user_text or _normalized(user_text) == query_norm:
            continue
        if not grounded_recall_match(query, user_text):
            continue
        score = float(semantic_similarity(query, user_text))
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
    """Admit only grounded recall evidence, then deduplicate and rank it."""

    unique: dict[str, MemoryUnit] = {}
    for memory in [*list(live), *list(cold)]:
        if not grounded_recall_match(query, memory.content):
            continue
        key = _normalized(memory.content)
        if key not in unique or "cold_biography" not in memory.tags:
            unique[key] = memory
    ranked = sorted(
        unique.values(),
        key=lambda memory: (semantic_similarity(query, memory.content), memory.created_at, memory.id),
        reverse=True,
    )
    return ranked[:max(0, int(top_k))]
