"""Disconnected authority-store transfer contract tests."""

import copy
import os
import tempfile
import time
from pathlib import Path

import pytest

from persona_engine.agent import CharacterAgent
from persona_engine.core.persistence import ContinuityImportError, WriterLeaseError

ROOT = Path(__file__).resolve().parents[1]
CART = ROOT / "cartridges" / "pretorius.snp"


def _subject(agent):
    return agent.writer_status()["subject_uuid"]


def _prepare_two_stream_subject(root: str):
    source_db = os.path.join(root, "source.db")
    alice = CharacterAgent(cartridge_path=str(CART), user_id="alice", db_path=source_db, host_id="host-a")
    alice.say("That accusation is false and you know it.")
    alice.engine.relationship.trust = 0.81
    alice.engine.ledger.propose_trait_update("portable_trait", 0.05, ["transfer-evidence"])
    alice.engine._persist()
    alice.adopt_commitment("non_disclosure", "Project Orchid")
    alice.advance_time(60.0, source="disconnected_transfer_test")
    bob = CharacterAgent(cartridge_path=str(CART), user_id="bob", db_path=source_db, host_id="host-a")
    bob.engine.relationship.trust = 0.23
    bob.engine._persist()
    bob.say("Bob has a separate relationship history.")
    return source_db, alice, bob


def test_disconnected_transfer_moves_whole_subject_and_permanently_retires_source_store():
    with tempfile.TemporaryDirectory() as d:
        source_db, alice, bob = _prepare_two_stream_subject(d)
        target_db = os.path.join(d, "target.db")
        subject = _subject(alice)
        alice_trust = alice.engine.relationship.trust
        bob_trust = bob.engine.relationship.trust
        source_evidence = alice.engine.persistence.event_counts_since(alice.engine.identity.name, "alice", 0.0)

        bundle = alice.prepare_disconnected_transfer("host-b")
        assert bundle["schema_version"] == "disconnected-transfer-v1"
        assert {item["user_id"] for item in bundle["content"]["bindings"]} >= {"alice", "bob"}
        assert [event["subject_sequence"] for event in bundle["content"]["events"]] == list(
            range(1, bundle["subject_sequence_anchor"] + 1)
        )
        assert alice.writer_status()["transfer_pending"] is True
        assert alice.writer_status()["writable"] is False
        with pytest.raises(WriterLeaseError):
            alice.say("prepared source must be quiescent")
        with pytest.raises(WriterLeaseError):
            bob.say("quiescence applies across interlocutor streams")

        stage = CharacterAgent.stage_disconnected_transfer(
            bundle, db_path=target_db, host_id="host-b"
        )
        target_alice = CharacterAgent(
            cartridge_path=str(CART), user_id="alice", db_path=target_db, host_id="host-b"
        )
        assert _subject(target_alice) == subject
        assert target_alice.writer_status()["writable"] is False
        with pytest.raises(WriterLeaseError):
            target_alice.say("staged target cannot author before source retirement")

        final = alice.finalize_disconnected_transfer(stage)
        assert final["target_generation"] == 2
        assert alice.writer_status()["store_retired"] is True
        with pytest.raises(WriterLeaseError):
            alice.say("retired source cannot author")

        reopened_old_file_as_target = CharacterAgent(
            cartridge_path=str(CART), user_id="alice", db_path=source_db, host_id="host-b"
        )
        assert reopened_old_file_as_target.writer_status()["store_retired"] is True
        assert reopened_old_file_as_target.writer_status()["writable"] is False
        with pytest.raises(WriterLeaseError):
            reopened_old_file_as_target.say("host-id reuse must not revive the retired store")

        activated = target_alice.activate_disconnected_transfer(final)
        assert activated["writable"] is True
        assert activated["writer_generation"] == 2
        assert target_alice.engine.relationship.trust == pytest.approx(alice_trust)
        assert target_alice.engine.clock.subject_elapsed_seconds >= 60.0
        trait = target_alice.engine.ledger.earned_traits["portable_trait"]
        assert trait.strength == pytest.approx(0.05)
        commitments = target_alice.engine.intentions.active_commitments(time.time())
        assert any(item.name == "commitment:non_disclosure:project_orchid" for item in commitments)
        assert target_alice.engine.persistence.event_counts_since(target_alice.engine.identity.name, "alice", 0.0) == source_evidence

        target_bob = CharacterAgent(
            cartridge_path=str(CART), user_id="bob", db_path=target_db, host_id="host-b"
        )
        assert _subject(target_bob) == subject
        assert target_bob.engine.relationship.trust == pytest.approx(bob_trust)
        assert target_bob.engine.relationship.trust != pytest.approx(alice_trust)
        assert target_bob.engine.ledger.earned_traits["portable_trait"].strength == pytest.approx(0.05)

        target_alice.say("target continues the moved life")
        events = target_alice.engine.persistence.load_subject_continuity_events(
            target_alice.engine.identity.name, "alice"
        )
        assert [event["subject_sequence"] for event in events] == list(range(1, len(events) + 1))
        assert not any(event["event_type"] == "host_transfer" for event in events)


def test_prepared_transfer_can_be_canceled_without_changing_writer_generation():
    with tempfile.TemporaryDirectory() as d:
        _, alice, _ = _prepare_two_stream_subject(d)
        bundle = alice.prepare_disconnected_transfer("host-b")
        assert alice.writer_status()["writable"] is False
        restored = alice.cancel_disconnected_transfer(bundle["transfer_uuid"])
        assert restored["writable"] is True
        assert restored["writer_generation"] == 1
        alice.say("source continues after canceled transfer")


def test_stage_rejects_tampered_bundle_and_wrong_target_host():
    with tempfile.TemporaryDirectory() as d:
        _, alice, _ = _prepare_two_stream_subject(d)
        bundle = alice.prepare_disconnected_transfer("host-b")
        tampered = copy.deepcopy(bundle)
        tampered["content"]["stream_state"][0]["key"] = "tampered-key"
        with pytest.raises(ContinuityImportError):
            CharacterAgent.stage_disconnected_transfer(
                tampered, db_path=os.path.join(d, "tampered.db"), host_id="host-b"
            )
        with pytest.raises(ContinuityImportError):
            CharacterAgent.stage_disconnected_transfer(
                bundle, db_path=os.path.join(d, "wrong-host.db"), host_id="host-c"
            )
        alice.cancel_disconnected_transfer(bundle["transfer_uuid"])


def test_stage_is_idempotent_for_the_exact_same_bundle_in_the_same_target_store():
    with tempfile.TemporaryDirectory() as d:
        _, alice, _ = _prepare_two_stream_subject(d)
        target_db = os.path.join(d, "target.db")
        bundle = alice.prepare_disconnected_transfer("host-b")
        first = CharacterAgent.stage_disconnected_transfer(bundle, db_path=target_db, host_id="host-b")
        second = CharacterAgent.stage_disconnected_transfer(bundle, db_path=target_db, host_id="host-b")
        assert first == second
        alice.cancel_disconnected_transfer(bundle["transfer_uuid"])


def test_finalize_rejects_modified_stage_receipt_and_source_remains_quiesced_until_cancel():
    with tempfile.TemporaryDirectory() as d:
        _, alice, _ = _prepare_two_stream_subject(d)
        target_db = os.path.join(d, "target.db")
        bundle = alice.prepare_disconnected_transfer("host-b")
        stage = CharacterAgent.stage_disconnected_transfer(bundle, db_path=target_db, host_id="host-b")
        bad = dict(stage)
        bad["content_digest"] = "0" * 64
        with pytest.raises(WriterLeaseError):
            alice.finalize_disconnected_transfer(bad)
        assert alice.writer_status()["transfer_pending"] is True
        assert alice.writer_status()["writable"] is False
        alice.cancel_disconnected_transfer(bundle["transfer_uuid"])
        assert alice.writer_status()["writable"] is True


def test_target_activation_rejects_state_digest_mismatch_without_granting_custody():
    with tempfile.TemporaryDirectory() as d:
        _, alice, _ = _prepare_two_stream_subject(d)
        target_db = os.path.join(d, "target.db")
        bundle = alice.prepare_disconnected_transfer("host-b")
        stage = CharacterAgent.stage_disconnected_transfer(bundle, db_path=target_db, host_id="host-b")
        final = alice.finalize_disconnected_transfer(stage)
        target = CharacterAgent(cartridge_path=str(CART), user_id="alice", db_path=target_db, host_id="host-b")
        target.engine.energy = 0.123456
        with pytest.raises(WriterLeaseError):
            target.activate_disconnected_transfer(final)
        assert target.writer_status()["writable"] is False
