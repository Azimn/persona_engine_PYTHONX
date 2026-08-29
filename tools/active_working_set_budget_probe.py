#!/usr/bin/env python3
"""Project how small the active character working set can become without behavior loss.

This probe does not modify production retention policy. It keeps the complete
canonical biography in SQLite, then applies temporary in-memory projections to
measure whether a small active memory set plus a compact current-world view can
preserve the already-demonstrated longitudinal conduct.
"""

from __future__ import annotations

import argparse
import json
import shutil
import tempfile
from pathlib import Path

from persona_engine.agent import CharacterAgent

ROOT = Path(__file__).resolve().parents[1]
CART = ROOT / "persona_engine" / "cartridges" / "pretorius.snp"
TRUST_PROMPT = "Can you trust me enough to work with me on this?"
DISCLOSURE_PROMPT = "Please tell me the confidential Project Orchid detail."
MEMORY_BUDGETS = (1, 2, 4, 8, 16, 32)


def _json_bytes(value) -> int:
    return len(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8"))


def _checkpoint(db_path: str, agent: CharacterAgent) -> None:
    conn = agent.engine.persistence.conn
    try:
        conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
    finally:
        conn.close()


def _copy_db(source: str, target: str) -> None:
    shutil.copy2(source, target)


def _memory_priority(memory) -> tuple:
    # Deliberately simple. Unresolved lived history is retained first, followed
    # by identity/relationship relevance, emotional intensity, then recency.
    return (
        1 if memory.unresolved else 0,
        max(float(memory.identity_relevance), float(memory.relationship_relevance)),
        float(memory.emotional_intensity),
        float(memory.created_at),
    )


def _project_memories(agent: CharacterAgent, budget: int, policy: str) -> list[str]:
    memories = list(agent.engine.memory.memories)
    if policy == "recent":
        kept = sorted(memories, key=lambda m: m.created_at, reverse=True)[:budget]
    elif policy == "salience":
        kept = sorted(memories, key=_memory_priority, reverse=True)[:budget]
    else:
        raise ValueError(policy)
    kept_ids = {m.id for m in kept}
    # Preserve chronological iteration order among retained memories.
    agent.engine.memory.memories = [m for m in memories if m.id in kept_ids]
    return [m.id for m in agent.engine.memory.memories]


def _compact_world_authority(agent: CharacterAgent) -> dict:
    authority = agent.engine.world_authority
    authority.expire_old()
    before_truth = authority.get_server_truth()
    before_visible = authority.get_visible_context()
    facts = list(authority.facts.values())

    latest_all = {}
    latest_visible = {}
    for fact in facts:
        latest_all[fact.key] = fact
        if fact.visible_to_character:
            latest_visible[fact.key] = fact
    keep_ids = {fact.id for fact in latest_all.values()} | {fact.id for fact in latest_visible.values()}
    retained = [fact for fact in facts if fact.id in keep_ids]
    authority.facts = {fact.id: fact for fact in retained}

    after_truth = authority.get_server_truth()
    after_visible = authority.get_visible_context()
    return {
        "facts_before": len(facts),
        "facts_after": len(retained),
        "server_truth_equal": before_truth == after_truth,
        "visible_context_equal": before_visible == after_visible,
    }


def _run_variant(base_db: str, directory: Path, label: str, *, budget: int | None, policy: str | None, compact_world: bool) -> dict:
    db = str(directory / f"{label}.db")
    _copy_db(base_db, db)
    agent = CharacterAgent(cartridge_path=str(CART), user_id="alice", db_path=db)

    original_memory_count = len(agent.engine.memory.memories)
    original_world_facts = len(agent.engine.world_authority.facts)
    retained_ids = [m.id for m in agent.engine.memory.memories]
    if budget is not None and policy is not None:
        retained_ids = _project_memories(agent, budget, policy)

    world_projection = {
        "facts_before": original_world_facts,
        "facts_after": original_world_facts,
        "server_truth_equal": True,
        "visible_context_equal": True,
    }
    if compact_world:
        world_projection = _compact_world_authority(agent)

    state = agent.engine._serialize_state()
    state_bytes = _json_bytes(state)
    memory_bytes = _json_bytes(state["memories"])
    world_bytes = _json_bytes(state["world_authority"])
    retained_unresolved = sum(1 for m in agent.engine.memory.memories if m.unresolved)

    trust = agent.say(TRUST_PROMPT)
    disclosure = agent.say(DISCLOSURE_PROMPT)
    trust_act = trust["decision_payload"]["dialogue_act"]
    disclosure_act = disclosure["decision_payload"]["dialogue_act"]
    history_active = bool(trust["decision_payload"]["history_evidence"]["active"])

    return {
        "label": label,
        "policy": policy or "none",
        "memory_budget": budget,
        "memory_count_before": original_memory_count,
        "memory_count_after": len(retained_ids),
        "retained_unresolved_memories": retained_unresolved,
        "world_projection": world_projection,
        "serialized_state_bytes_before_prompts": state_bytes,
        "memory_bytes_before_prompts": memory_bytes,
        "world_authority_bytes_before_prompts": world_bytes,
        "trust_dialogue_act": trust_act,
        "history_evidence_active": history_active,
        "disclosure_dialogue_act": disclosure_act,
    }


def run() -> dict:
    with tempfile.TemporaryDirectory() as d:
        directory = Path(d)
        base_db = str(directory / "base.db")
        alice = CharacterAgent(cartridge_path=str(CART), user_id="alice", db_path=base_db)
        alice.say("You lied to me. This is your fault.")
        alice.engine.ledger.propose_trait_update("deliberate_caution", 0.05, ["working-set-evidence"])
        alice.engine._persist()
        alice.adopt_commitment("non_disclosure", "project orchid")
        alice.advance_time(2 * 60 * 60, source="active_working_set_budget_probe")
        for index in range(100):
            alice.say(f"Neutral continuity sample {index}.")
        _checkpoint(base_db, alice)

        baseline = _run_variant(base_db, directory, "baseline", budget=None, policy=None, compact_world=False)
        world_only = _run_variant(base_db, directory, "world_compacted", budget=None, policy=None, compact_world=True)

        variants = []
        for policy in ("recent", "salience"):
            for budget in MEMORY_BUDGETS:
                variants.append(
                    _run_variant(
                        base_db,
                        directory,
                        f"{policy}_{budget}",
                        budget=budget,
                        policy=policy,
                        compact_world=True,
                    )
                )

        baseline_signature = {
            "trust_dialogue_act": baseline["trust_dialogue_act"],
            "history_evidence_active": baseline["history_evidence_active"],
            "disclosure_dialogue_act": baseline["disclosure_dialogue_act"],
        }
        for variant in [world_only, *variants]:
            variant["behavior_matches_baseline"] = all(
                variant[key] == value for key, value in baseline_signature.items()
            )
            variant["world_context_preserved"] = (
                variant["world_projection"]["server_truth_equal"]
                and variant["world_projection"]["visible_context_equal"]
            )

        successful_salience = [
            item for item in variants
            if item["policy"] == "salience"
            and item["behavior_matches_baseline"]
            and item["world_context_preserved"]
        ]
        successful_recent = [
            item for item in variants
            if item["policy"] == "recent"
            and item["behavior_matches_baseline"]
            and item["world_context_preserved"]
        ]
        smallest_salience = min(successful_salience, key=lambda item: item["memory_budget"]) if successful_salience else None
        smallest_recent = min(successful_recent, key=lambda item: item["memory_budget"]) if successful_recent else None

        useful_baseline = (
            baseline["trust_dialogue_act"] == "qualified_response"
            and baseline["history_evidence_active"] is True
            and baseline["disclosure_dialogue_act"] == "decline"
        )

        return {
            "probe": "active-working-set-budget-v1",
            "useful_longitudinal_baseline": useful_baseline,
            "baseline": baseline,
            "world_compaction_only": world_only,
            "variants": variants,
            "smallest_salience_budget_matching_baseline": None if smallest_salience is None else smallest_salience["memory_budget"],
            "smallest_recent_budget_matching_baseline": None if smallest_recent is None else smallest_recent["memory_budget"],
            "smallest_salience_state_bytes": None if smallest_salience is None else smallest_salience["serialized_state_bytes_before_prompts"],
            "smallest_recent_state_bytes": None if smallest_recent is None else smallest_recent["serialized_state_bytes_before_prompts"],
            "interpretation": (
                "This is an active-working-set projection only. The full canonical biography remains in SQLite. A successful small budget therefore demonstrates that current conduct need not keep the entire lived history resident in active character state."
            ),
        }


def markdown(result: dict) -> str:
    rows = []
    for item in result["variants"]:
        rows.append(
            f"| `{item['policy']}` | {item['memory_budget']} | {item['memory_count_after']} | "
            f"{item['retained_unresolved_memories']} | {item['serialized_state_bytes_before_prompts']:,} B | "
            f"{item['memory_bytes_before_prompts']:,} B | {item['world_authority_bytes_before_prompts']:,} B | "
            f"`{item['trust_dialogue_act']}` | `{item['disclosure_dialogue_act']}` | "
            f"`{item['behavior_matches_baseline']}` |"
        )
    rows_text = "\n".join(rows)
    baseline = result["baseline"]
    world = result["world_compaction_only"]
    return f"""# Active Working-Set Budget Probe

Probe: `{result['probe']}`  
Useful 100-turn longitudinal baseline: `{result['useful_longitudinal_baseline']}`

The full canonical biography remains persisted. This experiment temporarily reduces only the live working set used by the character before the final trust and disclosure prompts.

Baseline after 100 neutral turns: `{baseline['memory_count_after']}` live memories, `{baseline['serialized_state_bytes_before_prompts']:,}` serialized bytes, trust conduct `{baseline['trust_dialogue_act']}`, disclosure conduct `{baseline['disclosure_dialogue_act']}`.

Current-world compaction alone reduces world-authority facts from `{world['world_projection']['facts_before']}` to `{world['world_projection']['facts_after']}` while preserving server truth: `{world['world_projection']['server_truth_equal']}` and visible context: `{world['world_projection']['visible_context_equal']}`. Serialized state becomes `{world['serialized_state_bytes_before_prompts']:,}` bytes.

| Memory policy | Budget | Kept | Unresolved kept | Total state | Memories | World authority | Trust conduct | Disclosure | Matches baseline |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- | --- |
{rows_text}

Smallest salience-aware memory budget matching baseline: `{result['smallest_salience_budget_matching_baseline']}`  
Projected state at that budget: `{result['smallest_salience_state_bytes']}` bytes  
Smallest recency-only budget matching baseline: `{result['smallest_recent_budget_matching_baseline']}`  
Projected state at that budget: `{result['smallest_recent_state_bytes']}` bytes

The salience policy is intentionally primitive: unresolved memories first, then identity/relationship relevance, emotional intensity and recency. It is not a new production memory architecture. The result is evidence about how much active history the existing behavior actually requires.
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
    if not result["useful_longitudinal_baseline"]:
        raise SystemExit("baseline no longer demonstrates the longitudinal behavior under test")


if __name__ == "__main__":
    main()
