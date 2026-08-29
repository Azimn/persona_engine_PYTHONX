#!/usr/bin/env python3
"""Probe whether earned character development belongs to the subject or interlocutor."""

from __future__ import annotations

import argparse
import json
import tempfile
from pathlib import Path

from persona_engine.agent import CharacterAgent

ROOT = Path(__file__).resolve().parents[1]
CART = ROOT / "persona_engine" / "cartridges" / "pretorius.snp"
TRAIT = "deliberate_caution"
EVIDENCE_ID = "trait-ownership-probe-evidence"


def _subject_uuid(agent: CharacterAgent) -> str:
    return agent.engine.persistence._resolve_subject(agent.engine.identity.name, agent.engine.user_id)[0]


def _trait(agent: CharacterAgent):
    item = agent.engine.ledger.earned_traits.get(TRAIT)
    if item is None:
        return None
    return {
        "name": item.name,
        "strength": float(item.strength),
        "source_memory_ids": list(item.source_memory_ids),
    }


def run() -> dict:
    with tempfile.TemporaryDirectory() as d:
        db = str(Path(d) / "shared.db")

        alice = CharacterAgent(cartridge_path=str(CART), user_id="alice", db_path=db)
        alice.engine.ledger.propose_trait_update(TRAIT, 0.05, [EVIDENCE_ID])
        alice.engine._persist()
        alice_trait = _trait(alice)
        alice_subject = _subject_uuid(alice)

        alice_restart = CharacterAgent(cartridge_path=str(CART), user_id="alice", db_path=db)
        alice_restart_trait = _trait(alice_restart)

        bob = CharacterAgent(cartridge_path=str(CART), user_id="bob", db_path=db)
        bob_trait = _trait(bob)
        bob_subject = _subject_uuid(bob)

        same_subject = alice_subject == bob_subject
        alice_restart_preserved = alice_restart_trait == alice_trait and alice_trait is not None
        bob_preserved = bob_trait == alice_trait and alice_trait is not None

        if not same_subject:
            diagnosis = "subject_identity_split"
        elif not alice_restart_preserved:
            diagnosis = "earned_trait_not_persistent_even_with_same_interlocutor"
        elif bob_preserved:
            diagnosis = "earned_character_development_is_subject_owned"
        else:
            diagnosis = "earned_character_development_partitioned_by_interlocutor"

        return {
            "probe": "subject-earned-trait-ownership-v1",
            "trait_name": TRAIT,
            "same_subject_uuid": same_subject,
            "alice_trait_after_learning": alice_trait,
            "alice_trait_after_restart": alice_restart_trait,
            "bob_trait_on_same_subject": bob_trait,
            "same_interlocutor_restart_preserved": alice_restart_preserved,
            "cross_interlocutor_trait_preserved": bob_preserved,
            "diagnosis": diagnosis,
            "expected_minimum_property": (
                "Slow evidence-backed character development should remain attached to the continuing subject when the active interlocutor changes."
            ),
            "scope_note": (
                "This probe tests IdentityLedger.earned_traits only. It does not claim that relationship beliefs, pressures, memories, body state, world state, or symbols share the same ownership semantics."
            ),
        }


def markdown(result: dict) -> str:
    return f"""# Earned Trait Ownership Probe

Probe: `{result['probe']}`

| Observation | Result |
| --- | --- |
| Alice/Bob same subject UUID | `{result['same_subject_uuid']}` |
| Alice learned trait | `{result['alice_trait_after_learning']}` |
| Alice restart preserved trait | `{result['same_interlocutor_restart_preserved']}` |
| Bob on same subject preserved trait | `{result['cross_interlocutor_trait_preserved']}` |
| Bob trait state | `{result['bob_trait_on_same_subject']}` |
| Diagnosis | `{result['diagnosis']}` |

The property under test is narrow. `IdentityLedger.earned_traits` represents slow, evidence-backed development of the continuing character. If it survives an Alice restart but disappears merely because Bob becomes the active interlocutor, the failure is state ownership rather than trait learning or persistence.

This probe does not generalize ownership rules for memories, pressures, body, world, symbols, or relationship beliefs.
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
