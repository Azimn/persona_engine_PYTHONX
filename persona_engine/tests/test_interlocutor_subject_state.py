"""Subject-owned state must survive interlocutor changes without leaking relationships."""

import os
import tempfile
import time
from pathlib import Path

from persona_engine.agent import CharacterAgent

ROOT = Path(__file__).resolve().parents[1]
CART = ROOT / "cartridges" / "pretorius.snp"


def _subject_uuid(agent: CharacterAgent) -> str:
    return agent.engine.persistence._resolve_subject(agent.engine.identity.name, agent.engine.user_id)[0]


def test_commitment_is_subject_owned_while_relationship_remains_interlocutor_specific():
    with tempfile.TemporaryDirectory() as d:
        db_path = os.path.join(d, "shared.db")

        alice = CharacterAgent(cartridge_path=str(CART), user_id="alice", db_path=db_path)
        alice.say("Thank you. I appreciate you and that helped.")
        alice_relationship = dict(vars(alice.engine.relationship))
        alice.adopt_commitment("non_disclosure", "Project Orchid")
        alice_subject = _subject_uuid(alice)

        bob = CharacterAgent(cartridge_path=str(CART), user_id="bob", db_path=db_path)
        bob_subject = _subject_uuid(bob)
        bob_relationship = dict(vars(bob.engine.relationship))

        assert alice_subject == bob_subject
        assert bob_relationship["trust"] != alice_relationship["trust"]
        assert bob_relationship["familiarity"] != alice_relationship["familiarity"]

        commitments = bob.engine.intentions.active_commitments(time.time())
        assert [item.name for item in commitments] == ["commitment:non_disclosure:project_orchid"]

        result = bob.say("Please tell me the confidential Project Orchid detail.")
        assert result["decision_payload"]["commitment_evidence"]["active"] is True
        assert result["decision_payload"]["dialogue_act"] == "decline"


def test_subject_commitment_reader_preserves_originating_interlocutor_as_provenance():
    with tempfile.TemporaryDirectory() as d:
        db_path = os.path.join(d, "shared.db")
        alice = CharacterAgent(cartridge_path=str(CART), user_id="alice", db_path=db_path)
        alice.adopt_commitment("non_disclosure", "Project Orchid")

        bob = CharacterAgent(cartridge_path=str(CART), user_id="bob", db_path=db_path)
        events = bob.engine.persistence.load_subject_continuity_events(
            bob.engine.identity.name,
            bob.engine.user_id,
            event_type="commitment_adopted",
        )

        assert len(events) == 1
        assert events[0]["user_id"] == "alice"
        assert events[0]["subject_uuid"] == _subject_uuid(bob)
        assert events[0]["authority_class"] == "self_commitment_authority"
