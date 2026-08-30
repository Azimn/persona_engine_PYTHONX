#!/usr/bin/env python3
"""One-time repository patch for the validated contextual cold-biography seam."""

from pathlib import Path

COLD_CONTENT = r'''"""Bounded read-through retrieval from canonical cold biography.

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
)


def explicit_recall_request(text: str) -> bool:
    value = str(text or "")
    return any(pattern.search(value) for pattern in _RECALL_PATTERNS)


def _normalized(text: str) -> str:
    return " ".join(str(text or "").lower().split())


def _tokens(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9']+", str(text or "").lower()))


def recall_focus_tokens(query: str) -> set[str]:
    """Return lexical anchors that describe what is being explicitly recalled."""
    return {token for token in _tokens(query) if token not in _RECALL_SCAFFOLD and len(token) > 1}


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
'''


def replace_once(path: str, old: str, new: str, label: str) -> None:
    target = Path(path)
    text = target.read_text(encoding="utf-8")
    if old not in text:
        raise SystemExit(f"{label} seam not found")
    target.write_text(text.replace(old, new, 1), encoding="utf-8")


def main() -> None:
    Path("persona_engine/core/cold_biography.py").write_text(COLD_CONTENT, encoding="utf-8")

    replace_once(
        "persona_engine/core/engine.py",
        "from .cold_biography import explicit_recall_request, merge_recall_candidates, retrieve_cold_biography\n",
        """from .cold_biography import (\n    contextual_readthrough_request,\n    explicit_recall_request,\n    merge_contextual_candidates,\n    merge_recall_candidates,\n    retrieve_cold_biography,\n    retrieve_contextual_biography,\n)\n""",
        "engine import",
    )
    replace_once(
        "persona_engine/core/engine.py",
        """        retrieved = self.memory.retrieve(user_text, now, top_k=4, emotional_state_match=affect_match)\n        if explicit_recall_request(user_text):\n            cold_candidates = retrieve_cold_biography(\n                self.persistence,\n                self.identity.name,\n                self.user_id,\n                user_text,\n                top_k=4,\n            )\n            retrieved = merge_recall_candidates(user_text, retrieved, cold_candidates, top_k=4)\n""",
        """        retrieved = self.memory.retrieve(user_text, now, top_k=4, emotional_state_match=affect_match)\n        if explicit_recall_request(user_text):\n            cold_candidates = retrieve_cold_biography(\n                self.persistence,\n                self.identity.name,\n                self.user_id,\n                user_text,\n                top_k=4,\n            )\n            retrieved = merge_recall_candidates(user_text, retrieved, cold_candidates, top_k=4)\n        elif contextual_readthrough_request(user_text):\n            contextual_candidates = retrieve_contextual_biography(\n                self.persistence,\n                self.identity.name,\n                self.user_id,\n                user_text,\n                top_k=1,\n            )\n            retrieved = merge_contextual_candidates(user_text, retrieved, contextual_candidates, top_k=4)\n""",
        "engine retrieval",
    )

    replace_once(
        "persona_engine/core/offline_template_renderer.py",
        """        identity = str(digest.get(\"identity\", \"\")).strip()\n        memories = [str(getattr(memory, \"content\", memory)) for memory in (request.retrieved_memories or [])]\n        context = {\n            \"user_text\": str(resolved.get(\"user_text\", \"\")),\n            \"system_text\": str(resolved.get(\"system_prompt\", \"\")),\n            \"decision_payload\": dict(request.decision_payload or {}),\n            \"memories\": memories,\n            \"evidence\": list(request.evidence or []),\n            \"ledger_digest\": dict(digest),\n            \"identity\": identity,\n        }\n""",
        """        identity = str(digest.get(\"identity\", \"\")).strip()\n        memory_units = list(request.retrieved_memories or [])\n        memories = [str(getattr(memory, \"content\", memory)) for memory in memory_units]\n        contextual_memory = any(\n            \"contextual_readthrough\" in set(getattr(memory, \"tags\", set()) or set())\n            for memory in memory_units\n        )\n        context = {\n            \"user_text\": str(resolved.get(\"user_text\", \"\")),\n            \"system_text\": str(resolved.get(\"system_prompt\", \"\")),\n            \"decision_payload\": dict(request.decision_payload or {}),\n            \"memories\": memories,\n            \"contextual_memory\": contextual_memory,\n            \"evidence\": list(request.evidence or []),\n            \"ledger_digest\": dict(digest),\n            \"identity\": identity,\n        }\n""",
        "offline renderer request",
    )
    replace_once(
        "persona_engine/core/offline_template_renderer.py",
        """        group = self._classify(user_text, system_text, context.get(\"decision_payload\", {}))\n        topic = self._extract_topic(user_text)\n""",
        """        group = self._classify(user_text, system_text, context.get(\"decision_payload\", {}))\n        if group == \"question\" and bool(context.get(\"contextual_memory\")):\n            # Grounded cold continuation is already authorized evidence. Expose\n            # it rather than hiding successful recollection behind a generic reply.\n            group = \"memory\"\n        topic = self._extract_topic(user_text)\n""",
        "offline renderer classify",
    )

    tests = Path("persona_engine/tests/test_cold_biography.py")
    text = tests.read_text(encoding="utf-8")
    old_import = "from persona_engine.core.cold_biography import grounded_recall_match, recall_focus_tokens\n"
    new_import = """from persona_engine.core.cold_biography import (\n    context_focus_tokens,\n    contextual_readthrough_request,\n    grounded_context_match,\n    grounded_recall_match,\n    recall_focus_tokens,\n)\n"""
    if old_import not in text:
        raise SystemExit("cold biography test import seam not found")
    text = text.replace(old_import, new_import, 1)
    addition = r'''


def _project_two(agent: CharacterAgent) -> None:
    memories = list(agent.engine.memory.memories)
    agent.engine.memory.memories = sorted(memories, key=_priority, reverse=True)[:2]


def test_contextual_readthrough_requires_continuation_and_multiple_grounded_anchors():
    query = "Is the old observatory code word still the same?"
    assert contextual_readthrough_request(query) is True
    assert context_focus_tokens(query) == {"observatory", "code", "word"}
    assert grounded_context_match(
        query,
        "Please remember this neutral detail: the old observatory code word is amber-otter.",
    ) is True
    assert grounded_context_match(
        "Is the brass telescope serial number still the same?",
        "Please remember this neutral detail: the old observatory code word is amber-otter.",
    ) is False
    assert contextual_readthrough_request("Is it still the same?") is False
    assert contextual_readthrough_request("What is the old observatory code word?") is False


def test_contextual_cold_readthrough_changes_observable_answer_without_rehydrating_hot_memory():
    with tempfile.TemporaryDirectory() as d:
        db = os.path.join(d, "state.db")
        _make_history(db)
        agent = CharacterAgent(cartridge_path=str(CART), user_id="alice", db_path=db)
        _project_two(agent)
        assert all(TARGET not in memory.content.lower() for memory in agent.engine.memory.memories)

        result = agent.say("Is the old observatory code word still the same?")

        assert TARGET in result["response"].lower()
        assert any(
            TARGET in item["content"].lower()
            and "cold_biography" in item["tags"]
            and "contextual_readthrough" in item["tags"]
            for item in result["retrieved_memory_trace"]
        )
        assert all(TARGET not in memory.content.lower() for memory in agent.engine.memory.memories)


def test_contextual_cold_readthrough_fails_closed_for_never_happened_and_anchorless_topics():
    with tempfile.TemporaryDirectory() as d:
        db = os.path.join(d, "state.db")
        _make_history(db)
        agent = CharacterAgent(cartridge_path=str(CART), user_id="alice", db_path=db)
        _project_two(agent)

        negative = agent.say("Is the brass telescope serial number still the same?")
        broad = agent.say("Is it still the same?")

        assert not any("contextual_readthrough" in item["tags"] for item in negative["retrieved_memory_trace"])
        assert not any("contextual_readthrough" in item["tags"] for item in broad["retrieved_memory_trace"])
        assert TARGET not in negative["response"].lower()
        assert TARGET not in broad["response"].lower()


def test_contextual_cold_readthrough_does_not_cross_interlocutor_boundary():
    with tempfile.TemporaryDirectory() as d:
        db = os.path.join(d, "state.db")
        _make_history(db, "alice")
        bob = CharacterAgent(cartridge_path=str(CART), user_id="bob", db_path=db)
        result = bob.say("Is the old observatory code word still the same?")
        assert TARGET not in result["response"].lower()
        assert not any("contextual_readthrough" in item["tags"] for item in result["retrieved_memory_trace"])
'''
    if "test_contextual_cold_readthrough_changes_observable_answer_without_rehydrating_hot_memory" in text:
        raise SystemExit("contextual integration tests already present")
    tests.write_text(text + addition, encoding="utf-8")


if __name__ == "__main__":
    main()
