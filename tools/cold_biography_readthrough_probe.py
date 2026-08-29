#!/usr/bin/env python3
"""Verify one-item hot memory can recall a neutral fact from cold biography."""

from __future__ import annotations

import argparse
import json
import tempfile
from pathlib import Path

from persona_engine.agent import CharacterAgent

ROOT = Path(__file__).resolve().parents[1]
CART = ROOT / "persona_engine" / "cartridges" / "pretorius.snp"
TARGET = "amber-otter"
QUERY = "Do you remember the old observatory code word I told you?"


def _priority(memory):
    return (1 if memory.unresolved else 0, max(float(memory.identity_relevance), float(memory.relationship_relevance)), float(memory.emotional_intensity), float(memory.created_at))


def run() -> dict:
    with tempfile.TemporaryDirectory() as d:
        db = str(Path(d) / "state.db")
        agent = CharacterAgent(cartridge_path=str(CART), user_id="alice", db_path=db)
        agent.say("Please remember this neutral detail: the old observatory code word is amber-otter.")
        agent.say("You lied to me. This is your fault.")
        for index in range(100):
            agent.say(f"Routine catalog note {index}: ordinary shelf marker {index}.")

        restarted = CharacterAgent(cartridge_path=str(CART), user_id="alice", db_path=db)
        memories = list(restarted.engine.memory.memories)
        restarted.engine.memory.memories = sorted(memories, key=_priority, reverse=True)[:1]
        target_resident_before = any(TARGET in memory.content.lower() for memory in restarted.engine.memory.memories)
        hot_count_before = len(restarted.engine.memory.memories)
        result = restarted.say(QUERY)
        cold_hits = [item for item in result["retrieved_memory_trace"] if "cold_biography" in item["tags"]]
        target_cold_hit = any(TARGET in item["content"].lower() for item in cold_hits)
        target_resident_after = any(TARGET in memory.content.lower() for memory in restarted.engine.memory.memories)
        canonical = restarted.engine.persistence.load_continuity_events(restarted.engine.identity.name, restarted.engine.user_id)
        canonical_target = any(TARGET in str((event.get("payload") or {}).get("user_text", "")).lower() for event in canonical if event.get("event_type") == "input")
        passed = canonical_target and not target_resident_before and target_cold_hit and TARGET in result["response"].lower() and not target_resident_after
        return {
            "probe": "cold-biography-readthrough-v1",
            "passed": passed,
            "canonical_target_present": canonical_target,
            "hot_memory_count_before_recall": hot_count_before,
            "target_resident_before_recall": target_resident_before,
            "cold_trace_target_hit": target_cold_hit,
            "response": result["response"],
            "target_in_response": TARGET in result["response"].lower(),
            "target_resident_after_recall": target_resident_after,
            "retrieved_memory_trace": result["retrieved_memory_trace"],
            "interpretation": "A one-item resident cache can answer an explicit old neutral recall by transiently reading canonical cold biography, without promoting the archived fact back into hot memory." if passed else "Read-through did not satisfy the bounded recall contract.",
        }


def markdown(result: dict) -> str:
    return f"""# Cold Biography Read-Through Probe

Probe: `{{result['probe']}}`  
Passed: `{{result['passed']}}`

Canonical target present: `{{result['canonical_target_present']}}`  
Hot memory count before recall: `{{result['hot_memory_count_before_recall']}}`  
Target resident before recall: `{{result['target_resident_before_recall']}}`  
Cold trace found target: `{{result['cold_trace_target_hit']}}`  
Target appeared in rendered answer: `{{result['target_in_response']}}`  
Target resident after recall: `{{result['target_resident_after_recall']}}`

Response: `{{result['response']}}`

The archive candidate is transient evidence for the current turn. It does not become a belief, trait, commitment or resident memory merely because it was retrieved.
"""


def main():
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
        path = Path(args.markdown); path.parent.mkdir(parents=True, exist_ok=True); path.write_text(markdown(result), encoding="utf-8")
    if not result["passed"]:
        raise SystemExit("cold biography read-through contract failed")


if __name__ == "__main__":
    main()
