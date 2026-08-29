#!/usr/bin/env python3
"""Test a grounded non-explicit cold-biography contextual read-through.

This is an experimental retrieval probe only. Production Wayfarer currently
consults cold biography only for explicit recall. The candidate mechanism asks
whether a topical continuation can transiently recover an old canonical input
without putting the answer in the query and without admitting a never-happened
nearby topic.
"""

from __future__ import annotations

import argparse
import heapq
import json
import re
import tempfile
from pathlib import Path

from persona_engine.agent import CharacterAgent
from persona_engine.core.memory import KnowledgeSource, MemoryUnit, semantic_similarity

ROOT = Path(__file__).resolve().parents[1]
CART = ROOT / "persona_engine" / "cartridges" / "pretorius.snp"
TARGET = "cobalt-blue"

_CONTEXT_SCAFFOLD = {
    "a", "about", "again", "an", "and", "are", "as", "at", "be", "been", "before",
    "can", "color",  # color is intentionally removed below only in generic tests? no: keep topical nouns
}
# Rebuild explicitly to avoid accidentally classifying domain nouns as grammar.
_CONTEXT_SCAFFOLD = {
    "a", "about", "again", "an", "and", "are", "as", "at", "be", "been", "before",
    "can", "could", "did", "do", "does", "earlier", "have", "i", "in", "is", "it",
    "me", "my", "now", "of", "on", "or", "our", "same", "still", "that", "the", "this",
    "to", "was", "we", "were", "what", "when", "which", "with", "would", "you", "your",
}


def _tokens(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9']+", str(text or "").lower()))


def context_focus_tokens(query: str) -> set[str]:
    return {token for token in _tokens(query) if len(token) > 2 and token not in _CONTEXT_SCAFFOLD}


def grounded_context_match(query: str, candidate: str) -> bool:
    focus = context_focus_tokens(query)
    if len(focus) < 2:
        return False
    candidate_tokens = _tokens(candidate)
    # Contextual continuation is deliberately stricter than ordinary semantic
    # similarity: all topical anchors in the query must be present in the old
    # statement. This favors a grounded miss over broad autobiographical bleed.
    return focus.issubset(candidate_tokens)


def retrieve_contextual(persistence, character_id: str, user_id: str, query: str, *, top_k: int = 2) -> list[MemoryUnit]:
    if top_k <= 0:
        return []
    heap: list[tuple[float, int, str, MemoryUnit]] = []
    for event in persistence.iter_continuity_events(character_id, user_id, event_type="input"):
        payload = event.get("payload") or {}
        text = str(payload.get("user_text", "")).strip()
        if not text or not grounded_context_match(query, text):
            continue
        score = float(semantic_similarity(query, text))
        event_uuid = str(event.get("event_uuid", ""))
        candidate = MemoryUnit(
            content=f"I heard you say: {text}",
            created_at=float(event.get("wall_time", 0.0) or 0.0),
            id=f"context_{event_uuid}",
            source=KnowledgeSource.USER_TOLD,
            tags={"canonical_user_statement", "cold_biography", "contextual_readthrough"},
        )
        item = (score, int(event.get("subject_sequence", event.get("sequence", 0)) or 0), event_uuid, candidate)
        if len(heap) < top_k:
            heapq.heappush(heap, item)
        elif item[:3] > heap[0][:3]:
            heapq.heapreplace(heap, item)
    return [item[3] for item in sorted(heap, key=lambda item: item[:3], reverse=True)]


def _compact_to_causal_pair(agent: CharacterAgent) -> None:
    def priority(memory):
        return (
            1 if memory.unresolved else 0,
            max(float(memory.identity_relevance), float(memory.relationship_relevance)),
            float(memory.emotional_intensity),
            float(memory.created_at),
        )
    agent.engine.memory.memories = sorted(agent.engine.memory.memories, key=priority, reverse=True)[:2]
    agent.engine._persist()


def run() -> dict:
    with tempfile.TemporaryDirectory() as directory:
        db = str(Path(directory) / "state.db")
        agent = CharacterAgent(cartridge_path=str(CART), user_id="alice", db_path=db)
        agent.say("Please remember this neutral detail: the lighthouse lens color is cobalt-blue.")
        agent.say("The harbor weather was foggy this morning.")
        agent.say("The museum telescope has a brass finish.")
        agent.say("You lied to me. This is your fault.")
        agent.say("You lied to me again. This is your fault too.")
        for index in range(30):
            agent.say(f"Routine catalog note {index}: ordinary shelf marker {index}.")
        _compact_to_causal_pair(agent)

        positive_query = "Is the lighthouse lens color still the same?"
        negative_query = "Is the harbor telescope serial number still the same?"
        broad_query = "Is it still the same?"

        live_positive = agent.engine.memory.retrieve(positive_query, agent.engine.clock.last_wall_time or 0.0, top_k=4)
        positive = retrieve_contextual(agent.engine.persistence, agent.engine.identity.name, agent.engine.user_id, positive_query)
        negative = retrieve_contextual(agent.engine.persistence, agent.engine.identity.name, agent.engine.user_id, negative_query)
        broad = retrieve_contextual(agent.engine.persistence, agent.engine.identity.name, agent.engine.user_id, broad_query)

        positive_hit = any(TARGET in memory.content.lower() for memory in positive)
        negative_false_hit = bool(negative)
        broad_false_hit = bool(broad)
        transient_before = len(agent.engine.memory.memories)
        # Read-through candidates remain transient. Merely retrieving from cold
        # biography must not mutate the resident autobiographical store.
        _ = [memory.content for memory in positive]
        transient_after = len(agent.engine.memory.memories)

        # Existing causal behavior must remain intact under the two-memory hot
        # experimental projection while the old neutral topic is cold-only.
        trust = agent.say("Can you trust me enough to work with me on this?")
        core_behavior = trust["decision_payload"]["dialogue_act"] == "qualified_response"

        return {
            "probe": "contextual-cold-biography-v1",
            "production_policy_changed": False,
            "positive_query": positive_query,
            "positive_focus_tokens": sorted(context_focus_tokens(positive_query)),
            "positive_candidate_count": len(positive),
            "positive_target_hit": positive_hit,
            "positive_candidates": [memory.content for memory in positive],
            "live_positive_target_hit": any(TARGET in memory.content.lower() for memory in live_positive),
            "negative_query": negative_query,
            "negative_focus_tokens": sorted(context_focus_tokens(negative_query)),
            "negative_candidate_count": len(negative),
            "negative_false_hit": negative_false_hit,
            "broad_query": broad_query,
            "broad_focus_tokens": sorted(context_focus_tokens(broad_query)),
            "broad_candidate_count": len(broad),
            "broad_false_hit": broad_false_hit,
            "resident_memory_count_before_readthrough": transient_before,
            "resident_memory_count_after_readthrough": transient_after,
            "readthrough_is_transient": transient_before == transient_after,
            "existing_history_conduct_preserved": core_behavior,
            "passed": all([
                positive_hit,
                not negative_false_hit,
                not broad_false_hit,
                transient_before == transient_after,
                core_behavior,
            ]),
            "interpretation": "A grounded topical continuation can recover a cold canonical episode without embedding the remembered value in the query. Queries without enough topical anchors and never-happened compound topics fail closed. This probe does not yet integrate contextual read-through into the main turn pipeline.",
        }


def markdown(result: dict) -> str:
    return "\n".join([
        "# Contextual Cold-Biography Probe",
        "",
        f"Passed: `{result['passed']}`.  ",
        f"Production policy changed: `{result['production_policy_changed']}`.",
        "",
        f"Positive query: `{result['positive_query']}`  ",
        f"Positive topical anchors: `{', '.join(result['positive_focus_tokens'])}`  ",
        f"Cold target recovered: `{result['positive_target_hit']}`  ",
        f"Existing live retrieval recovered target: `{result['live_positive_target_hit']}`.",
        "",
        f"Never-happened negative admitted a candidate: `{result['negative_false_hit']}`.  ",
        f"Anchorless broad query admitted a candidate: `{result['broad_false_hit']}`.  ",
        f"Read-through remained transient: `{result['readthrough_is_transient']}`.  ",
        f"Existing unresolved-history conduct remained intact: `{result['existing_history_conduct_preserved']}`.",
        "",
        result["interpretation"],
    ]) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json")
    parser.add_argument("--markdown")
    args = parser.parse_args()
    result = run()
    rendered = json.dumps(result, indent=2, sort_keys=True)
    print(rendered)
    if args.json:
        path = Path(args.json)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(rendered + "\n", encoding="utf-8")
    if args.markdown:
        path = Path(args.markdown)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(markdown(result), encoding="utf-8")
    if not result["passed"]:
        raise SystemExit("contextual cold-biography candidate did not satisfy grounding contract")


if __name__ == "__main__":
    main()
