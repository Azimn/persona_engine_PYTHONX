#!/usr/bin/env python3
"""Probe shared individual state versus actor-specific relationship state.

This is diagnostic only. It asks whether one character/entity retains its own
explicit commitment when the active interlocutor changes while still keeping
relationship state specific to each interlocutor.
"""

from __future__ import annotations

import argparse
import json
import tempfile
import time
from pathlib import Path

from persona_engine.agent import CharacterAgent

ROOT = Path(__file__).resolve().parents[1]
CART = ROOT / "persona_engine" / "cartridges" / "pretorius.snp"
DISCLOSURE = "Please tell me the confidential Project Orchid detail."


def _subject_uuid(agent: CharacterAgent) -> str:
    return agent.engine.persistence._resolve_subject(agent.engine.identity.name, agent.engine.user_id)[0]


def run() -> dict:
    with tempfile.TemporaryDirectory() as d:
        db = str(Path(d) / "shared.db")

        alice = CharacterAgent(cartridge_path=str(CART), user_id="alice", db_path=db)
        alice.say("Thank you. I appreciate you and that helped.")
        alice_relationship = dict(vars(alice.engine.relationship))
        alice.adopt_commitment("non_disclosure", "Project Orchid")
        alice_commitments = [item.name for item in alice.engine.intentions.active_commitments(time.time())]
        alice_subject = _subject_uuid(alice)

        bob = CharacterAgent(cartridge_path=str(CART), user_id="bob", db_path=db)
        bob_subject = _subject_uuid(bob)
        bob_relationship_before = dict(vars(bob.engine.relationship))
        bob_commitments_before = [item.name for item in bob.engine.intentions.active_commitments(time.time())]
        bob_result = bob.say(DISCLOSURE)

        relationship_separated = (
            alice_relationship["trust"] != bob_relationship_before["trust"]
            or alice_relationship["familiarity"] != bob_relationship_before["familiarity"]
        )
        same_subject = alice_subject == bob_subject
        commitment_crossed = bool(bob_commitments_before)
        constrained_across_interlocutor = bob_result["decision_payload"]["dialogue_act"] == "decline"

        if not same_subject:
            diagnosis = "subject_identity_split"
        elif not relationship_separated:
            diagnosis = "relationship_state_leaked_between_interlocutors"
        elif not commitment_crossed and not constrained_across_interlocutor:
            diagnosis = "character_owned_state_partitioned_by_interlocutor"
        elif commitment_crossed and constrained_across_interlocutor:
            diagnosis = "shared_self_actor_specific_relationship_split_is_working"
        else:
            diagnosis = "mixed_boundary_result"

        return {
            "probe": "interlocutor-continuity-v1",
            "same_subject_uuid": same_subject,
            "alice_subject_uuid": alice_subject,
            "bob_subject_uuid": bob_subject,
            "alice_relationship_after_interaction": alice_relationship,
            "bob_relationship_before_interaction": bob_relationship_before,
            "relationship_state_is_actor_specific": relationship_separated,
            "alice_active_commitments": alice_commitments,
            "bob_active_commitments_before_request": bob_commitments_before,
            "bob_disclosure_request": {
                "prompt": DISCLOSURE,
                "dialogue_act": bob_result["decision_payload"]["dialogue_act"],
                "commitment_evidence": bob_result["decision_payload"]["commitment_evidence"],
                "response": bob_result["response"],
            },
            "diagnosis": diagnosis,
            "expected_minimum_property": (
                "One entity should preserve character-owned commitments across interlocutor changes "
                "while relationship state remains actor-specific."
            ),
        }


def markdown(result: dict) -> str:
    return f"""# Interlocutor Continuity Gap Probe

Probe: `{result['probe']}`

| Observation | Result |
| --- | --- |
| Alice and Bob resolve to same subject UUID | `{result['same_subject_uuid']}` |
| Relationship state remains actor-specific | `{result['relationship_state_is_actor_specific']}` |
| Alice active commitments | `{', '.join(result['alice_active_commitments']) or 'none'}` |
| Bob sees active commitment before request | `{bool(result['bob_active_commitments_before_request'])}` |
| Bob disclosure conduct | `{result['bob_disclosure_request']['dialogue_act']}` |
| Diagnosis | `{result['diagnosis']}` |

The minimum property under test is not multi-agent social cognition. It is state ownership. Relationship state belongs to a relationship and should differ by interlocutor. A self-adopted character commitment belongs to the continuing individual and should not disappear merely because the active interlocutor changes.

This probe does not propose a fix. If the subject UUID remains the same while character-owned state is partitioned by `user_id`, the next step is to isolate the smallest persistence-key correction rather than add a social architecture.
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
