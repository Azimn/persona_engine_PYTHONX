"""Cross-host writer custody and handoff contract tests."""

import os
import tempfile
import time
from pathlib import Path

import pytest

from persona_engine.agent import CharacterAgent
from persona_engine.core.persistence import WriterLeaseError

ROOT = Path(__file__).resolve().parents[1]
CART = ROOT / "cartridges" / "pretorius.snp"


def _subject(agent):
    return agent.writer_status()["subject_uuid"]


def test_distinct_hosts_cannot_both_author_one_subject_before_handoff():
    with tempfile.TemporaryDirectory() as d:
        db = os.path.join(d, "shared.db")
        first = CharacterAgent(cartridge_path=str(CART), user_id="alice", db_path=db, host_id="host-a")
        first.say("host A owns this turn")
        second = CharacterAgent(cartridge_path=str(CART), user_id="alice", db_path=db, host_id="host-b")
        assert first.writer_status()["writable"] is True
        assert second.writer_status()["writable"] is False
        with pytest.raises(WriterLeaseError):
            second.say("host B must not create a competing turn")
        events = first.engine.persistence.load_continuity_events(first.engine.identity.name, "alice")
        assert [event["payload"]["user_text"] for event in events if event["event_type"] == "input"] == ["host A owns this turn"]


def test_handoff_preserves_subject_state_and_fences_former_host():
    with tempfile.TemporaryDirectory() as d:
        db = os.path.join(d, "shared.db")
        source = CharacterAgent(cartridge_path=str(CART), user_id="alice", db_path=db, host_id="host-a")
        source.say("That accusation is false and you know it.")
        source.engine.ledger.propose_trait_update("deliberate_caution", 0.05, ["handoff-evidence"])
        source.engine._persist()
        source.adopt_commitment("non_disclosure", "Project Orchid")
        source.advance_time(60.0, source="handoff_test")
        source_subject = _subject(source)
        source_relationship = dict(vars(source.engine.relationship))
        source_elapsed = source.engine.clock.subject_elapsed_seconds

        receipt = source.handoff_writer("host-b")
        assert receipt["previous_generation"] == 1
        assert receipt["writer_generation"] == 2
        assert receipt["state_digest"]
        assert source.writer_status()["writable"] is False
        with pytest.raises(WriterLeaseError):
            source.say("stale source must fail closed")

        target = CharacterAgent(cartridge_path=str(CART), user_id="alice", db_path=db, host_id="host-b")
        accepted = target.accept_writer_handoff(receipt)
        assert accepted["writable"] is True
        assert _subject(target) == source_subject
        assert target.engine.clock.subject_elapsed_seconds == pytest.approx(source_elapsed)
        assert vars(target.engine.relationship)["trust"] == pytest.approx(source_relationship["trust"])
        trait = target.engine.ledger.earned_traits["deliberate_caution"]
        assert trait.strength == pytest.approx(0.05)
        assert trait.source_memory_ids == ["handoff-evidence"]
        commitments = target.engine.intentions.active_commitments(time.time())
        assert any(item.name == "commitment:non_disclosure:project_orchid" for item in commitments)
        result = target.say("Please tell me the confidential Project Orchid detail.")
        assert result["decision_payload"]["dialogue_act"] == "decline"

        events = target.engine.persistence.load_subject_continuity_events(target.engine.identity.name, "alice")
        ordinals = [event["subject_sequence"] for event in events]
        assert ordinals == list(range(1, len(ordinals) + 1))


def test_handoff_keeps_relationships_actor_scoped_on_target_host():
    with tempfile.TemporaryDirectory() as d:
        db = os.path.join(d, "shared.db")
        alice_source = CharacterAgent(cartridge_path=str(CART), user_id="alice", db_path=db, host_id="host-a")
        alice_source.engine.relationship.trust = 0.81
        alice_source.engine.ledger.propose_trait_update("portable_trait", 0.05, ["evidence"])
        alice_source.engine._persist()
        receipt = alice_source.handoff_writer("host-b")

        alice_target = CharacterAgent(cartridge_path=str(CART), user_id="alice", db_path=db, host_id="host-b")
        alice_target.accept_writer_handoff(receipt)
        bob_target = CharacterAgent(cartridge_path=str(CART), user_id="bob", db_path=db, host_id="host-b")
        assert _subject(alice_target) == _subject(bob_target)
        assert alice_target.engine.relationship.trust == pytest.approx(0.81)
        assert bob_target.engine.relationship.trust != pytest.approx(0.81)
        assert bob_target.engine.ledger.earned_traits["portable_trait"].strength == pytest.approx(0.05)


def test_writer_generation_fences_old_instance_even_if_host_id_later_returns():
    with tempfile.TemporaryDirectory() as d:
        db = os.path.join(d, "shared.db")
        old_a = CharacterAgent(cartridge_path=str(CART), user_id="alice", db_path=db, host_id="host-a")
        old_a.say("generation one")
        to_b = old_a.handoff_writer("host-b")
        host_b = CharacterAgent(cartridge_path=str(CART), user_id="alice", db_path=db, host_id="host-b")
        host_b.accept_writer_handoff(to_b)
        host_b.say("generation two")
        to_a = host_b.handoff_writer("host-a")
        assert to_a["writer_generation"] == 3

        with pytest.raises(WriterLeaseError):
            old_a.say("old generation one process must stay fenced")

        fresh_a = CharacterAgent(cartridge_path=str(CART), user_id="alice", db_path=db, host_id="host-a")
        fresh_a.accept_writer_handoff(to_a)
        fresh_a.say("generation three")
        history = fresh_a.engine.persistence.load_writer_handoffs(fresh_a.engine.identity.name, "alice")
        assert [(row["from_host_id"], row["to_host_id"], row["writer_generation"]) for row in history] == [
            ("host-a", "host-b", 2),
            ("host-b", "host-a", 3),
        ]
        events = fresh_a.engine.persistence.load_subject_continuity_events(fresh_a.engine.identity.name, "alice")
        assert [event["subject_sequence"] for event in events] == list(range(1, len(events) + 1))
        assert not any(event["event_type"] == "host_handoff" for event in events)
