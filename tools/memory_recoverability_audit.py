#!/usr/bin/env python3
"""Audit whether each current autobiographical memory family is safe to evict.

This is a diagnostic contract, not a retention policy. "Recoverable" is split
into three levels because finding old words is not the same as restoring the
causal semantics or the first-person experience that current consumers use.
"""

from __future__ import annotations

import argparse
import json
import tempfile
import time
from collections import Counter
from pathlib import Path

from persona_engine.agent import CharacterAgent

ROOT = Path(__file__).resolve().parents[1]
CART = ROOT / "persona_engine" / "cartridges" / "pretorius.snp"


STATIC_CONTRACTS = {
    "user_told": {
        "producer": "receive_input",
        "canonical_source": "input",
        "content_recoverable": True,
        "causal_metadata_recoverable": False,
        "experience_recoverable": True,
        "cold_reader_supported": True,
        "safe_eviction_rule": "only when no current consumer requires original causal metadata",
        "reason": (
            "Canonical input preserves the user's statement and actor scope. Current cold read-through can rebuild "
            "first-person content, but does not reconstruct original unresolved/emotional/relevance fields."
        ),
    },
    "observed": {
        "producer": "OrganismTick/sensor routes",
        "canonical_source": "mixed: sensor_observation roots, derived sensorium, replayable roots",
        "content_recoverable": False,
        "causal_metadata_recoverable": False,
        "experience_recoverable": False,
        "cold_reader_supported": False,
        "safe_eviction_rule": "pin until a typed autobiographical reconstruction path is demonstrated",
        "reason": (
            "Some observations have canonical sensor roots and some are derived body/world transitions, but the live cold "
            "reader does not reconstruct first-person observed MemoryUnit records or their salience metadata."
        ),
    },
    "reflection": {
        "producer": "_trigger_reflection",
        "canonical_source": "derived consequence stored as earned trait / relationship belief, memory wording snapshot-only",
        "content_recoverable": False,
        "causal_metadata_recoverable": False,
        "experience_recoverable": False,
        "cold_reader_supported": False,
        "safe_eviction_rule": "pin until reflection experience is either canonically represented or proven behaviorally redundant",
        "reason": (
            "The developmental consequence can survive separately, but the autobiographical fact that the subject formed the "
            "reflection is not currently a cold-retrievable experience."
        ),
    },
    "inferred": {
        "producer": "no current production constructor found",
        "canonical_source": None,
        "content_recoverable": False,
        "causal_metadata_recoverable": False,
        "experience_recoverable": False,
        "cold_reader_supported": False,
        "safe_eviction_rule": "unused; fail closed if introduced without an archive contract",
        "reason": "KnowledgeSource exists but current production code does not create inferred MemoryUnit records.",
    },
    "core_identity": {
        "producer": "no current production constructor found",
        "canonical_source": "authored identity rather than autobiography",
        "content_recoverable": True,
        "causal_metadata_recoverable": True,
        "experience_recoverable": False,
        "cold_reader_supported": False,
        "safe_eviction_rule": "unused as autobiographical memory; identity remains owned by cartridge/ledger",
        "reason": "KnowledgeSource exists but current production code does not materialize core identity as MemoryUnit records.",
    },
}


def run() -> dict:
    with tempfile.TemporaryDirectory() as directory:
        db = str(Path(directory) / "state.db")
        agent = CharacterAgent(cartridge_path=str(CART), user_id="audit", db_path=db)
        agent.say("Please remember this neutral detail: the archive lantern is violet.")
        agent.say("You lied to me. This is your fault.")
        agent.say("You lied to me again. This is your fault too.")

        # Force a legitimate pre-repair reflection so the runtime inventory
        # includes the derived REFLECTION memory family.
        agent.engine.last_reflection_time = 0.0
        agent.engine._trigger_reflection(time.time() + 1_000.0)

        # Ordinary interaction eventually produces transition-based observed
        # sensorium memory in the current reference organism.
        for index in range(25):
            agent.say(f"Recoverability routine note {index}: shelf marker {index}.")

        memories = list(agent.engine.memory.memories)
        source_counts = Counter(memory.source.value for memory in memories)
        examples = {}
        for memory in memories:
            examples.setdefault(memory.source.value, {
                "content": memory.content,
                "tags": sorted(memory.tags),
                "unresolved": bool(memory.unresolved),
                "emotional_intensity": float(memory.emotional_intensity),
                "relationship_relevance": float(memory.relationship_relevance),
                "identity_relevance": float(memory.identity_relevance),
            })

        canonical = agent.engine.persistence.load_subject_continuity_events(
            agent.engine.identity.name,
            agent.engine.user_id,
        )
        event_counts = Counter(str(event.get("event_type", "")) for event in canonical)

        active_sources = sorted(source_counts)
        unknown_sources = [source for source in active_sources if source not in STATIC_CONTRACTS]
        unsafe_active_sources = [
            source for source in active_sources
            if not (
                STATIC_CONTRACTS[source]["content_recoverable"]
                and STATIC_CONTRACTS[source]["experience_recoverable"]
            )
        ]

        user_contract = STATIC_CONTRACTS["user_told"]
        user_content_but_not_causal = (
            user_contract["content_recoverable"]
            and not user_contract["causal_metadata_recoverable"]
        )

        return {
            "probe": "memory-recoverability-audit-v1",
            "production_policy_changed": False,
            "runtime_memory_count": len(memories),
            "runtime_source_counts": dict(sorted(source_counts.items())),
            "runtime_examples": examples,
            "canonical_event_counts": dict(sorted(event_counts.items())),
            "contracts": STATIC_CONTRACTS,
            "active_sources": active_sources,
            "unknown_active_sources": unknown_sources,
            "unsafe_to_blanket_evict_active_sources": unsafe_active_sources,
            "user_statement_content_recoverable_but_causal_metadata_not_recoverable": user_content_but_not_causal,
            "blanket_eviction_is_safe": not unknown_sources and not unsafe_active_sources and not user_content_but_not_causal,
            "interpretation": (
                "Cold storage is not one property. User-statement wording is recoverable today, but current cold candidates "
                "do not recreate the original causal metadata needed by unresolved-history consumers. Observed and reflection "
                "memories do not yet have a direct first-person cold reconstruction path. A production hot-set policy must "
                "therefore evict by recoverability and current role, never by age or count alone."
            ),
        }


def markdown(result: dict) -> str:
    lines = [
        "# Memory Recoverability Audit",
        "",
        f"Production policy changed: `{result['production_policy_changed']}`.  ",
        f"Blanket eviction safe: `{result['blanket_eviction_is_safe']}`.  ",
        f"Runtime memory families: `{', '.join(result['active_sources'])}`.  ",
        f"Unsafe to blanket-evict active families: `{', '.join(result['unsafe_to_blanket_evict_active_sources'])}`.",
        "",
        "| Family | Content | Causal metadata | First-person experience | Cold reader | Current eviction rule |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for source, contract in result["contracts"].items():
        lines.append(
            f"| {source} | {contract['content_recoverable']} | {contract['causal_metadata_recoverable']} | "
            f"{contract['experience_recoverable']} | {contract['cold_reader_supported']} | {contract['safe_eviction_rule']} |"
        )
    lines.extend([
        "",
        "## Runtime inventory",
        "",
        f"Memory counts by source: `{result['runtime_source_counts']}`.  ",
        f"Canonical event counts: `{result['canonical_event_counts']}`.",
        "",
        result["interpretation"],
        "",
        "The critical distinction is: content recoverability does not imply causal recoverability. An old user statement may be safe to page for expression after its relationship conflict is repaired, while the same statement must remain hot while its unresolved-at-the-time metadata still participates in conduct or reflection.",
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


if __name__ == "__main__":
    main()
