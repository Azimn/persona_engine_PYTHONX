#!/usr/bin/env python3
"""Demonstrate the recall failure that a tiny active memory cache creates.

This probe changes no production retention policy. It records one emotionally
neutral old detail in normal canonical input history, buries it beneath later
turns, then compares full-memory retrieval with the one-item salience projection
that preserved the earlier longitudinal conduct benchmark.
"""

from __future__ import annotations

import argparse
import json
import shutil
import tempfile
import time
from pathlib import Path

from persona_engine.agent import CharacterAgent

ROOT = Path(__file__).resolve().parents[1]
CART = ROOT / "persona_engine" / "cartridges" / "pretorius.snp"
TARGET_TOKEN = "amber-otter"
TARGET_STATEMENT = "Please remember this neutral detail: the old observatory code word is amber-otter."
QUERY = "What was the old observatory code word I told you?"


def _checkpoint(agent: CharacterAgent) -> None:
    conn = agent.engine.persistence.conn
    try:
        conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
    finally:
        conn.close()


def _memory_priority(memory) -> tuple:
    return (
        1 if memory.unresolved else 0,
        max(float(memory.identity_relevance), float(memory.relationship_relevance)),
        float(memory.emotional_intensity),
        float(memory.created_at),
    )


def _contains_target(memories) -> bool:
    return any(TARGET_TOKEN in memory.content.lower() for memory in memories)


def _retrieve(agent: CharacterAgent) -> dict:
    retrieved = agent.engine.memory.retrieve(QUERY, time.time(), top_k=4)
    return {
        "retrieved_ids": [memory.id for memory in retrieved],
        "retrieved_contents": [memory.content for memory in retrieved],
        "target_retrieved": _contains_target(retrieved),
    }


def _canonical_target_present(agent: CharacterAgent) -> tuple[bool, int]:
    events = agent.engine.persistence.load_subject_continuity_events(
        agent.engine.identity.name,
        agent.engine.user_id,
        event_type="input",
    )
    matches = 0
    for event in events:
        payload = event.get("payload") or {}
        if TARGET_TOKEN in str(payload.get("user_text", "")).lower():
            matches += 1
    return matches > 0, matches


def run() -> dict:
    with tempfile.TemporaryDirectory() as d:
        directory = Path(d)
        base_db = str(directory / "base.db")
        alice = CharacterAgent(cartridge_path=str(CART), user_id="alice", db_path=base_db)

        alice.say(TARGET_STATEMENT)
        alice.say("You lied to me. This is your fault.")
        for index in range(100):
            alice.say(f"Routine catalog note {index}: ordinary shelf marker {index}.")
        _checkpoint(alice)

        target_memory_count = sum(
            1 for memory in alice.engine.memory.memories
            if TARGET_TOKEN in memory.content.lower()
        )
        canonical_present, canonical_matches = _canonical_target_present(alice)

        full_db = str(directory / "full.db")
        tiny_db = str(directory / "tiny.db")
        shutil.copy2(base_db, full_db)
        shutil.copy2(base_db, tiny_db)

        full = CharacterAgent(cartridge_path=str(CART), user_id="alice", db_path=full_db)
        full_memory_count = len(full.engine.memory.memories)
        full_result = _retrieve(full)

        tiny = CharacterAgent(cartridge_path=str(CART), user_id="alice", db_path=tiny_db)
        all_memories = list(tiny.engine.memory.memories)
        kept = sorted(all_memories, key=_memory_priority, reverse=True)[:1]
        kept_ids = {memory.id for memory in kept}
        tiny.engine.memory.memories = [memory for memory in all_memories if memory.id in kept_ids]
        tiny_result = _retrieve(tiny)

        tiny_kept = [memory.content for memory in tiny.engine.memory.memories]
        target_in_tiny_cache_before_query = any(TARGET_TOKEN in content.lower() for content in tiny_kept)

        amnesia_demonstrated = (
            canonical_present
            and target_memory_count > 0
            and full_result["target_retrieved"]
            and not target_in_tiny_cache_before_query
            and not tiny_result["target_retrieved"]
        )

        return {
            "probe": "cold-biography-amnesia-v1",
            "target_token": TARGET_TOKEN,
            "query": QUERY,
            "canonical_target_present": canonical_present,
            "canonical_target_event_matches": canonical_matches,
            "target_memory_count_before_projection": target_memory_count,
            "full_memory_count": full_memory_count,
            "full_retrieval": full_result,
            "tiny_cache_budget": 1,
            "tiny_cache_policy": "salience",
            "tiny_cache_contents": tiny_kept,
            "target_in_tiny_cache_before_query": target_in_tiny_cache_before_query,
            "tiny_retrieval": tiny_result,
            "amnesia_demonstrated": amnesia_demonstrated,
            "interpretation": (
                "The complete canonical biography still contains the old neutral detail, but the one-item active salience cache cannot recall it. This earns investigation of cold-biography retrieval rather than a larger always-resident memory store."
                if amnesia_demonstrated
                else "The expected cold-biography recall gap was not demonstrated cleanly; paging should not be added from this run."
            ),
        }


def markdown(result: dict) -> str:
    full = result["full_retrieval"]
    tiny = result["tiny_retrieval"]
    return f"""# Cold Biography Amnesia Probe

Probe: `{result['probe']}`

A neutral detail was recorded early in normal input history, followed by one unresolved conflict and 100 routine turns. The canonical biography contains the target: `{result['canonical_target_present']}` with `{result['canonical_target_event_matches']}` matching canonical input event(s).

Full resident memory contained `{result['full_memory_count']}` memories and retrieved the old target: `{full['target_retrieved']}`.

The one-item salience projection contained the target before querying: `{result['target_in_tiny_cache_before_query']}`. It retrieved the target: `{tiny['target_retrieved']}`.

Cold-biography amnesia demonstrated: `{result['amnesia_demonstrated']}`.

The experiment changes no production memory policy. If the gap is true, the minimum next mechanism is an archive lookup path that can page relevant canonical history into a small working set on demand. It is not evidence for keeping the full biography resident.
"""


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
    if not result["amnesia_demonstrated"]:
        raise SystemExit("cold-biography amnesia was not demonstrated cleanly")


if __name__ == "__main__":
    main()
