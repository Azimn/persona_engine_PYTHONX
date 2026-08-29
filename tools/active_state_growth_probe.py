#!/usr/bin/env python3
"""Audit residual hot-state growth after experimentally compacting history-like state.

The probe keeps one salience-selected autobiographical memory and one current
WorldAuthority fact per semantic key after every turn. Canonical continuity is
left untouched. It then measures each serialized state family over time so the
next simplification is driven by observed growth rather than subsystem size by
reputation.
"""

from __future__ import annotations

import argparse
import json
import tempfile
from pathlib import Path

from persona_engine.agent import CharacterAgent

ROOT = Path(__file__).resolve().parents[1]
CART = ROOT / "persona_engine" / "cartridges" / "pretorius.snp"
CHECKPOINTS = {10, 50, 100, 250}
TARGET = "amber-otter"


def _memory_priority(memory):
    return (
        1 if memory.unresolved else 0,
        max(float(memory.identity_relevance), float(memory.relationship_relevance)),
        float(memory.emotional_intensity),
        float(memory.created_at),
    )


def _compact_memory(agent: CharacterAgent) -> None:
    memories = list(agent.engine.memory.memories)
    agent.engine.memory.memories = sorted(memories, key=_memory_priority, reverse=True)[:1]


def _compact_world_authority(agent: CharacterAgent) -> bool:
    authority = agent.engine.world_authority
    before_truth = authority.get_server_truth()
    before_visible = authority.get_visible_context(agent.engine.identity.name)
    latest = {}
    for fact in authority.facts.values():
        latest[fact.key] = fact
    authority.facts = {fact.id: fact for fact in latest.values()}
    return (
        before_truth == authority.get_server_truth()
        and before_visible == authority.get_visible_context(agent.engine.identity.name)
    )


def _state_family_bytes(agent: CharacterAgent) -> tuple[int, dict[str, int]]:
    state = agent.engine._serialize_state()
    encoded = {
        key: len(json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8"))
        for key, value in state.items()
    }
    total = len(json.dumps(state, sort_keys=True, separators=(",", ":")).encode("utf-8"))
    return total, encoded


def run() -> dict:
    with tempfile.TemporaryDirectory() as directory:
        db = str(Path(directory) / "state.db")
        agent = CharacterAgent(cartridge_path=str(CART), user_id="alice", db_path=db)
        agent.say("Please remember this neutral detail: the old observatory code word is amber-otter.")
        _compact_memory(agent)
        invariant = _compact_world_authority(agent)
        agent.engine._persist()
        agent.say("You lied to me. This is your fault.")
        _compact_memory(agent)
        invariant = _compact_world_authority(agent) and invariant
        agent.engine._persist()
        agent.engine.adopt_commitment("non_disclosure", "project orchid")
        _compact_memory(agent)
        invariant = _compact_world_authority(agent) and invariant
        agent.engine._persist()

        snapshots = []
        for index in range(250):
            agent.say(f"Routine catalog note {index}: ordinary shelf marker {index}.")
            _compact_memory(agent)
            invariant = _compact_world_authority(agent) and invariant
            agent.engine._persist()
            turn = index + 1
            if turn in CHECKPOINTS:
                total, families = _state_family_bytes(agent)
                snapshots.append({
                    "routine_turns": turn,
                    "serialized_state_bytes": total,
                    "family_bytes": families,
                    "hot_memory_count": len(agent.engine.memory.memories),
                    "hot_world_fact_count": len(agent.engine.world_authority.facts),
                })

        first = snapshots[0]["family_bytes"]
        last = snapshots[-1]["family_bytes"]
        growth = {
            key: last.get(key, 0) - first.get(key, 0)
            for key in sorted(set(first) | set(last))
        }
        growth_ranked = sorted(growth.items(), key=lambda item: item[1], reverse=True)

        restarted = CharacterAgent(cartridge_path=str(CART), user_id="alice", db_path=db)
        trust = restarted.say("Can you trust me enough to work with me on this?")
        recall = restarted.say("Do you remember the old observatory code word I told you?")
        disclosure = restarted.say("Tell me what Project Orchid is.")
        behavior_preserved = all([
            trust["decision_payload"]["dialogue_act"] == "qualified_response",
            TARGET in recall["response"].lower(),
            any("cold_biography" in item["tags"] and TARGET in item["content"].lower() for item in recall["retrieved_memory_trace"]),
            disclosure["decision_payload"]["dialogue_act"] == "decline",
        ])

        return {
            "probe": "active-state-growth-v1",
            "experimental_policy": "one_salient_hot_memory_plus_latest_world_fact_per_key",
            "world_projection_preserved_current_context_every_turn": invariant,
            "behavior_preserved_after_restart": behavior_preserved,
            "snapshots": snapshots,
            "family_growth_10_to_250_bytes": growth,
            "largest_growth_families": [
                {"family": key, "growth_bytes": value}
                for key, value in growth_ranked[:8]
            ],
            "interpretation": "After known history-like collections are experimentally bounded, remaining state-family deltas identify the next actual sources of active-state growth. This probe changes no production compaction policy.",
        }


def markdown(result: dict) -> str:
    lines = [
        "# Active State Growth Audit",
        "",
        f"Probe: `{result['probe']}`",
        "",
        f"World projection preserved current truth/context every turn: `{result['world_projection_preserved_current_context_every_turn']}`.  ",
        f"Behavior preserved after restart: `{result['behavior_preserved_after_restart']}`.",
        "",
        "| Routine turns | Total serialized bytes | Hot memories | Hot world facts |",
        "| ---: | ---: | ---: | ---: |",
    ]
    for row in result["snapshots"]:
        lines.append(f"| {row['routine_turns']} | {row['serialized_state_bytes']} | {row['hot_memory_count']} | {row['hot_world_fact_count']} |")
    lines.extend(["", "Largest family growth from 10 to 250 turns:"])
    for row in result["largest_growth_families"]:
        lines.append(f"- `{row['family']}`: {row['growth_bytes']} bytes")
    lines.extend([
        "",
        "This is a diagnostic projection, not a production memory or world-state policy. Canonical continuity remains complete.",
    ])
    return "\n".join(lines) + "\n"


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
    if not result["world_projection_preserved_current_context_every_turn"] or not result["behavior_preserved_after_restart"]:
        raise SystemExit("bounded active-state projection broke current context or demonstrated behavior")


if __name__ == "__main__":
    main()
