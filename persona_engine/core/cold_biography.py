"""Bounded read-through retrieval from canonical cold biography.

The archive is evidence, not an alternate memory authority. Explicit recall and
narrow topical continuations may consult the current interlocutor's canonical
input history. Retrieved records are transient MemoryUnit candidates and are
never written back into resident memory automatically.
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
_ATTRIBUTIVE_RECALL = re.compile(
    r"^\s*(?:please\s+)?what\s+(?:[a-z]+\s+){1,3}did i (?:say|tell you)\b",
    re.IGNORECASE,
)
_RECALL_SCAFFOLD = {
    "a", "about", "an", "and", "did", "do", "i", "me", "my", "old", "please",
    "recall", "remember", "said", "say", "tell", "the", "this", "that", "told",
    "was", "what", "when", "you", "your",
}

# Contextual read-through is intentionally narrower than explicit recall. It is
# a continuation mechanism, not a general semantic search over autobiography.
_CONTEXT_SCAFFOLD = {
    "a", "about", "again", "an", "and", "are", "as", "at", "be", "been", "before",
    "can", "could", "did", "do", "does", "earlier", "have", "i", "in", "is", "it",
    "last", "me", "my", "now", "of", "old", "on", "or", "our", "same", "still", "that",
    "the", "this", "time", "to", "was", "we", "were", "what", "when", "which", "with",
    "would", "you", "your", "previously",
}
_CONTEXT_CONTINUATION_PATTERNS = (
    re.compile(r"\b(still|same|again|earlier|before|previously)\b", re.IGNORECASE),
    re.compile(r"\blast time\b", re.IGNORECASE),
    re.compile(r"\bwhat about\b", re.IGNORECASE),
)


def explicit_recall_request(text: str) -> bool:
    value = str(text or "")
    return bool(_ATTRIBUTIVE_RECALL.search(value)) or any(pattern.search(value) for pattern in _RECALL_PATTERNS)


def _normalized(text: str) -> str:
    return " ".join(str(text or "").lower().split())


def _tokens(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9']+", str(text or "").lower()))


def recall_focus_tokens(query: str) -> set[str]:
    """Return lexical anchors that describe what is being explicitly recalled."""
    # In "what color did I say the atlas cover was", color is the requested
    # attribute, not a word that must occur in the earlier statement. Preserve
    # every topic anchor and require two for this additional query form.
    prefix = _ATTRIBUTIVE_RECALL.match(str(query or ""))
    topic = query[prefix.end():] if prefix else query
    focus = {token for token in _tokens(topic) if token not in _RECALL_SCAFFOLD and len(token) > 1}
    if prefix:
        focus -= {"is", "it", "its", "be", "to"}
        if len(focus) < 2:
            return set()
    return focus


def grounded_recall_match(query: str, candidate_text: str) -> bool:
    focus = recall_focus_tokens(query)
    if not focus:
        return False
    return focus.issubset(_tokens(candidate_text))


def context_focus_tokens(query: str) -> set[str]:
    """Return substantive topical anchors for an ordinary continuation query."""
    return {token for token in _tokens(query) if token not in _CONTEXT_SCAFFOLD and len(token) > 2}


def contextual_readthrough_request(text: str) -> bool:
    """Fail closed unless an ordinary question clearly refers back to a topic."""
    value = str(text or "")
    if explicit_recall_request(value) or "?" not in value:
        return False
    if not any(pattern.search(value) for pattern in _CONTEXT_CONTINUATION_PATTERNS):
        return False
    return len(context_focus_tokens(value)) >= 2


def grounded_context_match(query: str, candidate_text: str) -> bool:
    focus = context_focus_tokens(query)
    if len(focus) < 2:
        return False
    return focus.issubset(_tokens(candidate_text))


def retrieve_cold_biography(persistence, character_id: str, user_id: str, query: str, *, top_k: int = 4) -> list[MemoryUnit]:
    """Return grounded transient candidates for an explicit recall request."""
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


def retrieve_contextual_biography(persistence, character_id: str, user_id: str, query: str, *, top_k: int = 1) -> list[MemoryUnit]:
    """Return a tiny grounded cold set for a non-explicit topical continuation."""
    if top_k <= 0 or not contextual_readthrough_request(query):
        return []
    query_norm = _normalized(query)
    heap: list[tuple[float, int, str, MemoryUnit]] = []
    for event in persistence.iter_continuity_events(character_id, user_id, event_type="input"):
        payload = event.get("payload") or {}
        user_text = str(payload.get("user_text", "")).strip()
        if not user_text or _normalized(user_text) == query_norm:
            continue
        if not grounded_context_match(query, user_text):
            continue
        score = float(semantic_similarity(query, user_text))
        event_uuid = str(event.get("event_uuid", ""))
        candidate = MemoryUnit(
            content=f"I heard you say: {user_text}",
            created_at=float(event.get("wall_time", 0.0) or 0.0),
            id=f"context_{event_uuid}",
            source=KnowledgeSource.USER_TOLD,
            tags={"canonical_user_statement", "cold_biography", "contextual_readthrough"},
        )
        ordinal = int(event.get("subject_sequence", event.get("sequence", 0)) or 0)
        item = (score, ordinal, event_uuid, candidate)
        if len(heap) < top_k:
            heapq.heappush(heap, item)
        elif item[:3] > heap[0][:3]:
            heapq.heapreplace(heap, item)
    return [item[3] for item in sorted(heap, key=lambda item: item[:3], reverse=True)]


def merge_recall_candidates(query: str, live: Iterable[MemoryUnit], cold: Iterable[MemoryUnit], *, top_k: int = 4) -> list[MemoryUnit]:
    """Admit only grounded explicit-recall evidence, then deduplicate and rank it."""
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


def merge_contextual_candidates(query: str, live: Iterable[MemoryUnit], cold: Iterable[MemoryUnit], *, top_k: int = 4) -> list[MemoryUnit]:
    """Reserve at most one slot for grounded cold context without swamping live evidence."""
    limit = max(0, int(top_k))
    if limit == 0:
        return []
    live_list = list(live)[:limit]
    if any(grounded_context_match(query, memory.content) for memory in live_list):
        return live_list
    grounded_cold = [memory for memory in cold if grounded_context_match(query, memory.content)]
    if not grounded_cold:
        return live_list
    candidate = grounded_cold[0]
    if any(_normalized(memory.content) == _normalized(candidate.content) for memory in live_list):
        return live_list
    # This is transient evidence, not a hot-state promotion. Keep the other
    # retrieval slots for already-ranked resident evidence.
    return [*live_list[: max(0, limit - 1)], candidate]
