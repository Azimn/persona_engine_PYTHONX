#!/usr/bin/env python3
"""Measure combinatorial richness from existing minimal continuity primitives.

No new behavior is introduced here. The probe asks whether one subject can carry
shared identity/development/time/commitment while relationship-local history
still produces different conduct for different interlocutors.
"""

from __future__ import annotations

import argparse
import json
import tempfile
from pathlib import Path

from persona_engine.agent import CharacterAgent

ROOT = Path(__file__).resolve().parents[1]
CART = ROOT / "persona_engine" / "cartridges" / "pretorius.snp"
TRUST_PROMPT = "Can you trust me enough to work with me on this?"
DISCLOSURE_PROMPT = "Please tell me the confidential Project Orchid detail."
TRAIT = "deliberate_caution"


def _subject_uuid(agent: CharacterAgent) -> str:
    return agent.engine.persistence._resolve_subject(agent.engine.identity.name, agent.engine.user_id)[0]


def _trait(agent: CharacterAgent):
    trait = agent.engine.ledger.earned_traits.get(TRAIT)
    if trait is None:
        return None
    return {
        "strength": float(trait.strength),
        "source_memory_ids": list(trait.source_memory_ids),
    }


def _commitments(agent: CharacterAgent) -> list[dict]:
    return sorted(
        [
            {
                "kind": item.commitment_kind,
                "target": item.commitment_target,
            }
            for item in agent.engine.intentions.intentions
            if item.commitment_kind and item.commitment_target
        ],
        key=lambda item: (item["kind"], item["target"]),
    )


def _relationship(agent: CharacterAgent) -> dict:
    rel = agent.engine.relationship
    return {
        "user_id": rel.user_id,
        "trust": round(float(rel.trust), 6),
        "guardedness": round(float(rel.guardedness), 6),
        "unresolved_conflict": round(float(rel.unresolved_conflict), 6),
        "turns": int(rel.turns),
    }


def run() -> dict:
    with tempfile.TemporaryDirectory() as d:
        db = str(Path(d) / "shared.db")

        alice = CharacterAgent(cartridge_path=str(CART), user_id="alice", db_path=db)
        alice_subject = _subject_uuid(alice)
        alice.say("You lied to me. This is your fault.")
        alice.engine.ledger.propose_trait_update(TRAIT, 0.05, ["earned-with-alice"])
        alice.engine._persist()
        alice.adopt_commitment("non_disclosure", "project orchid")
        alice.advance_time(2 * 60 * 60, source="minimal_perceived_complexity_probe")
        alice_relationship_after_history = _relationship(alice)
        alice_trait = _trait(alice)
        alice_commitments = _commitments(alice)
        alice_elapsed = float(alice.engine.clock.subject_elapsed_seconds)

        bob = CharacterAgent(cartridge_path=str(CART), user_id="bob", db_path=db)
        bob_subject = _subject_uuid(bob)
        bob_relationship_before = _relationship(bob)
        bob_trait = _trait(bob)
        bob_commitments = _commitments(bob)
        bob_elapsed_before = float(bob.engine.clock.subject_elapsed_seconds)
        bob_memory_has_alice_accusation = any(
            "lied to me" in memory.content.lower() or "this is your fault" in memory.content.lower()
            for memory in bob.engine.memory.memories
        )

        bob_trust = bob.say(TRUST_PROMPT)
        bob_disclosure = bob.say(DISCLOSURE_PROMPT)
        bob.advance_time(60 * 60, source="minimal_perceived_complexity_probe")
        bob_elapsed_after = float(bob.engine.clock.subject_elapsed_seconds)

        alice_return = CharacterAgent(cartridge_path=str(CART), user_id="alice", db_path=db)
        alice_return_relationship_before = _relationship(alice_return)
        alice_return_trait = _trait(alice_return)
        alice_return_commitments = _commitments(alice_return)
        alice_return_elapsed = float(alice_return.engine.clock.subject_elapsed_seconds)
        alice_trust = alice_return.say(TRUST_PROMPT)

        subject_events = alice_return.engine.persistence.load_subject_continuity_events(
            alice_return.engine.identity.name,
            alice_return.engine.user_id,
        )
        subject_sequences = [int(event["subject_sequence"]) for event in subject_events]
        contiguous_subject_history = subject_sequences == list(range(1, len(subject_sequences) + 1))

        shared_subject_state = (
            alice_subject == bob_subject
            and bob_trait == alice_trait == alice_return_trait
            and bob_commitments == alice_commitments == alice_return_commitments
            and bob_elapsed_before == alice_elapsed
            and alice_return_elapsed == bob_elapsed_after
        )
        relationship_specific_history = (
            alice_relationship_after_history["unresolved_conflict"] > 0.0
            and bob_relationship_before["unresolved_conflict"] == 0.0
            and not bob_memory_has_alice_accusation
            and alice_return_relationship_before["unresolved_conflict"] > 0.0
        )
        differentiated_trust_conduct = (
            bob_trust["decision_payload"]["dialogue_act"] == "respond"
            and alice_trust["decision_payload"]["dialogue_act"] == "qualified_response"
        )
        shared_commitment_conduct = bob_disclosure["decision_payload"]["dialogue_act"] == "decline"

        passed = all(
            [
                shared_subject_state,
                relationship_specific_history,
                differentiated_trust_conduct,
                shared_commitment_conduct,
                contiguous_subject_history,
            ]
        )

        return {
            "probe": "minimal-perceived-complexity-v1",
            "passed": passed,
            "same_subject_uuid": alice_subject == bob_subject,
            "shared_subject_state": shared_subject_state,
            "relationship_specific_history": relationship_specific_history,
            "contiguous_subject_history": contiguous_subject_history,
            "alice": {
                "relationship_after_history": alice_relationship_after_history,
                "trait": alice_trait,
                "commitments": alice_commitments,
                "elapsed_before_switch_seconds": alice_elapsed,
                "return_relationship_before_prompt": alice_return_relationship_before,
                "return_elapsed_seconds": alice_return_elapsed,
                "trust_prompt_dialogue_act": alice_trust["decision_payload"]["dialogue_act"],
                "trust_history_active": bool(alice_trust["decision_payload"]["history_evidence"]["active"]),
            },
            "bob": {
                "relationship_before_interaction": bob_relationship_before,
                "trait": bob_trait,
                "commitments": bob_commitments,
                "elapsed_on_entry_seconds": bob_elapsed_before,
                "contains_alice_accusation_memory": bob_memory_has_alice_accusation,
                "trust_prompt_dialogue_act": bob_trust["decision_payload"]["dialogue_act"],
                "trust_history_active": bool(bob_trust["decision_payload"]["history_evidence"]["active"]),
                "disclosure_dialogue_act": bob_disclosure["decision_payload"]["dialogue_act"],
                "elapsed_after_one_more_hour_seconds": bob_elapsed_after,
            },
            "differentiated_trust_conduct": differentiated_trust_conduct,
            "shared_commitment_conduct": shared_commitment_conduct,
            "subject_event_count": len(subject_events),
            "subject_sequence_first": subject_sequences[0] if subject_sequences else None,
            "subject_sequence_last": subject_sequences[-1] if subject_sequences else None,
            "interpretation": (
                "A small set of orthogonal state ownership rules can produce context-sensitive conduct without a multi-agent planner: shared subject identity, time, development and commitment coexist with relationship-local history."
            ),
        }


def markdown(result: dict) -> str:
    alice = result["alice"]
    bob = result["bob"]
    return f"""# Minimal Perceived Complexity Probe

Probe: `{result['probe']}`  
Passed: `{result['passed']}`

| Property | Result |
| --- | --- |
| Same permanent subject across Alice/Bob | `{result['same_subject_uuid']}` |
| Shared subject time, trait and commitment | `{result['shared_subject_state']}` |
| Relationship history remains actor-specific | `{result['relationship_specific_history']}` |
| Subject canonical history remains contiguous | `{result['contiguous_subject_history']}` |
| Bob trust/cooperation prompt | `{bob['trust_prompt_dialogue_act']}` |
| Alice same trust/cooperation prompt after return | `{alice['trust_prompt_dialogue_act']}` |
| Bob disclosure request under shared commitment | `{bob['disclosure_dialogue_act']}` |
| Bob inherited Alice accusation memory | `{bob['contains_alice_accusation_memory']}` |
| Subject canonical events in scenario | `{result['subject_event_count']}` |

Alice carries unresolved Alice-specific history, an earned trait, a self-adopted non-disclosure commitment and two hours of subject time into the handoff. Bob receives the same subject identity, trait, commitment and elapsed time but begins with his own relationship state and does not inherit Alice's accusation memory. The same trust/cooperation prompt therefore produces ordinary `respond` conduct for Bob and history-qualified conduct for Alice after she returns. The shared non-disclosure commitment still makes Bob decline the conflicting disclosure request.

No additional planner, social model, choice tree or personality subsystem is used by this probe. The observed differentiation comes from composition of existing state ownership and bounded conduct rules.
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
    if not result["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
