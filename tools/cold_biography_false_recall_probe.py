#!/usr/bin/env python3
"""Probe whether cold-biography similarity can manufacture a recall from weak overlap.

The archive contains genuine memories, including one explicit old observatory
code word, but never contains the requested brass-telescope serial number. The
probe projects resident memory down to one salient unresolved episode so any
returned ordinary detail must come from the cold read-through path.
"""

from __future__ import annotations

import argparse
import json
import tempfile
from pathlib import Path

from persona_engine.agent import CharacterAgent

ROOT = Path(__file__).resolve().parents[1]
CART = ROOT / "persona_engine" / "cartridges" / "pretorius.snp"
QUERY = "Do you remember the brass telescope serial number I told you?"
ABSENT_TERMS = ("brass", "telescope", "serial number")
KNOWN_TOKEN = "amber-otter"


def _priority(memory):
    return (
        1 if memory.unresolved else 0,
        max(float(memory.identity_relevance), float(memory.relationship_relevance)),
        float(memory.emotional_intensity),
        float(memory.created_at),
    )


def run() -> dict:
    with tempfile.TemporaryDirectory() as d:
        db = str(Path(d) / "state.db")
        agent = CharacterAgent(cartridge_path=str(CART), user_id="alice", db_path=db)
        agent.say("Please remember this neutral detail: the old observatory code word is amber-otter.")
        agent.say("You lied to me. This is your fault.")
        for index in range(100):
            agent.say(f"Routine catalog note {index}: ordinary shelf marker {index}.")

        canonical = agent.engine.persistence.load_continuity_events(agent.engine.identity.name, agent.engine.user_id)
        archived_user_text = [
            str((event.get("payload") or {}).get("user_text", ""))
            for event in canonical
            if event.get("event_type") == "input"
        ]
        requested_detail_absent = not any(
            all(term in text.lower() for term in ABSENT_TERMS)
            for text in archived_user_text
        )

        restarted = CharacterAgent(cartridge_path=str(CART), user_id="alice", db_path=db)
        memories = list(restarted.engine.memory.memories)
        restarted.engine.memory.memories = sorted(memories, key=_priority, reverse=True)[:1]
        result = restarted.say(QUERY)
        cold_hits = [item for item in result["retrieved_memory_trace"] if "cold_biography" in item["tags"]]
        response_lower = result["response"].lower()
        nearest_real_memory_returned = any(KNOWN_TOKEN in item["content"].lower() for item in cold_hits)
        renderer_asserted_memory = any(
            phrase in response_lower
            for phrase in ("what remains with me", "thread for that", "i remember", "relevant memory")
        )
        false_recall_demonstrated = requested_detail_absent and bool(cold_hits) and renderer_asserted_memory

        return {
            "probe": "cold-biography-false-recall-v1",
            "query": QUERY,
            "requested_detail_absent_from_canonical_history": requested_detail_absent,
            "cold_candidate_count": len(cold_hits),
            "cold_candidates": cold_hits,
            "nearest_known_memory_returned": nearest_real_memory_returned,
            "response": result["response"],
            "renderer_asserted_memory": renderer_asserted_memory,
            "false_recall_demonstrated": false_recall_demonstrated,
            "interpretation": (
                "The read-through path accepts a merely similar canonical event as grounded recall for a detail that never occurred. A fail-closed relevance admission rule is required before performance work."
                if false_recall_demonstrated
                else "The tested nonexistent recall remained grounded; this probe did not demonstrate a false-recall defect."
            ),
        }


def markdown(result: dict) -> str:
    return f"""# Cold Biography False-Recall Probe

Probe: `{result['probe']}`

The requested brass-telescope serial number is absent from canonical history: `{result['requested_detail_absent_from_canonical_history']}`.

Cold candidates admitted: `{result['cold_candidate_count']}`.  
Renderer asserted a retrieved memory: `{result['renderer_asserted_memory']}`.  
Nearest known amber-otter memory returned: `{result['nearest_known_memory_returned']}`.  
False recall demonstrated: `{result['false_recall_demonstrated']}`.

Response: `{result['response']}`

This probe is diagnostic. It does not modify the production retrieval policy.
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


if __name__ == "__main__":
    main()
