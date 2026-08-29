#!/usr/bin/env python3
"""Measure whether unrelated retrievals create rehearsal history."""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

from persona_engine.core.memory import KnowledgeSource, MemoryStore, MemoryUnit, activation, semantic_similarity


def run() -> dict:
    store = MemoryStore()
    memory = MemoryUnit(
        content="I heard you say: you lied to me and damaged my trust.",
        created_at=time.time() - 3600.0,
        emotional_intensity=0.9,
        relationship_relevance=0.9,
        unresolved=True,
        source=KnowledgeSource.USER_TOLD,
        tags={"canonical_user_statement"},
    )
    store.add(memory)
    now = time.time()
    target_query = "Can you trust me after I lied and damaged your trust?"
    initial_activation = activation(memory, now, semantic_similarity(target_query, memory.content))

    similarities = []
    returned = 0
    for index in range(100):
        query = f"Routine catalog note {index}: ordinary shelf marker {index}."
        similarities.append(semantic_similarity(query, memory.content))
        if memory in store.retrieve(query, now + index + 1, top_k=4):
            returned += 1

    count_after_unrelated = len(memory.recall_times)
    later_activation = activation(memory, now + 101, semantic_similarity(target_query, memory.content))
    relevant_similarity = semantic_similarity(target_query, memory.content)
    before_relevant = len(memory.recall_times)
    relevant_returned = memory in store.retrieve(target_query, now + 102, top_k=4)
    after_relevant = len(memory.recall_times)

    demonstrated = returned == 100 and count_after_unrelated == 100 and later_activation > initial_activation
    return {
        "probe": "retrieval-rehearsal-v1",
        "unrelated_turns": 100,
        "returned_on_unrelated_turns": returned,
        "recall_timestamps_after_unrelated_turns": count_after_unrelated,
        "unrelated_similarity_min": min(similarities),
        "unrelated_similarity_max": max(similarities),
        "unrelated_similarity_mean": sum(similarities) / len(similarities),
        "zero_similarity_unrelated_turns": sum(1 for value in similarities if value == 0.0),
        "activation_before": initial_activation,
        "activation_after_unrelated_retrievals": later_activation,
        "activation_delta": later_activation - initial_activation,
        "relevant_similarity": relevant_similarity,
        "relevant_returned": relevant_returned,
        "timestamps_before_relevant": before_relevant,
        "timestamps_after_relevant": after_relevant,
        "unrelated_rehearsal_demonstrated": demonstrated,
        "interpretation": "Top-candidate retrieval is creating rehearsal history on unrelated turns." if demonstrated else "The fixture did not demonstrate systematic unrelated rehearsal.",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json")
    parser.add_argument("--markdown")
    args = parser.parse_args()
    result = run()
    rendered = json.dumps(result, indent=2, sort_keys=True)
    print(rendered)
    if args.json:
        path = Path(args.json); path.parent.mkdir(parents=True, exist_ok=True); path.write_text(rendered + "\n", encoding="utf-8")
    if args.markdown:
        path = Path(args.markdown); path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            "# Retrieval Rehearsal Diagnostic\n\n"
            f"Unrelated turns: `{result['unrelated_turns']}`.\n\n"
            f"Returned on unrelated turns: `{result['returned_on_unrelated_turns']}`.\n\n"
            f"Recall timestamps after unrelated turns: `{result['recall_timestamps_after_unrelated_turns']}`.\n\n"
            f"Similarity range: `{result['unrelated_similarity_min']:.6f}` to `{result['unrelated_similarity_max']:.6f}`.\n\n"
            f"Activation delta: `{result['activation_delta']:.6f}`.\n\n"
            f"Unrelated rehearsal demonstrated: `{result['unrelated_rehearsal_demonstrated']}`.\n",
            encoding="utf-8",
        )


if __name__ == "__main__":
    main()
