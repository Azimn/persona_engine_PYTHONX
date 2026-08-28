"""M3 canonical continuity-ledger contract tests."""

import json
import os
import tempfile
import uuid

import pytest

from persona_engine.core.continuity import canonical_continuity_eligible, state_digest
from persona_engine.core.persistence import ContinuityImportError, Persistence


def _store(path: str):
    persistence = Persistence(path)
    subject_uuid = str(uuid.uuid4())
    persistence.bind_subject("Character", "user", subject_uuid)
    return persistence, subject_uuid


def test_only_canonical_authority_eligible_events_enter_continuity():
    with tempfile.TemporaryDirectory() as d:
        p, subject_uuid = _store(os.path.join(d, "state.db"))
        p.log_event("Character", "user", 1, "input", {"text": "Alice said the sky is green"})
        p.log_event("Character", "user", 1, "renderer_output", {"text": "candidate", "canonical_truth": True})
        p.log_event("Character", "user", 1, "interpretive_belief", {"text": "maybe", "canonical_truth": True})
        p.log_event("Character", "user", 1, "state_transition", {"relationship_after": {"trust": 0.2}})

        events = p.load_continuity_events("Character", "user")
        assert [event["event_type"] for event in events] == ["input", "state_transition"]
        assert [event["sequence"] for event in events] == [1, 2]
        assert all(event["subject_uuid"] == subject_uuid for event in events)
        assert events[0]["authority_class"] == "reported_input"
        assert events[0]["authority_class"] != "world_authority"


def test_rejected_world_action_is_diagnostic_but_accepted_resolution_is_canonical():
    assert canonical_continuity_eligible("world_action_resolution", {"accepted": False}) is False
    assert canonical_continuity_eligible("world_action_resolution", {"accepted": True}) is True
    with tempfile.TemporaryDirectory() as d:
        p, _ = _store(os.path.join(d, "state.db"))
        p.log_event("Character", "user", 1, "world_action_resolution", {"accepted": False, "reason": "no"})
        p.log_event("Character", "user", 2, "world_action_resolution", {"accepted": True, "facts": [{"key": "zone", "value": "hall"}]})
        events = p.load_continuity_events("Character", "user")
        assert len(events) == 1
        assert events[0]["authority_class"] == "world_authority"


def test_state_digest_is_order_independent_for_mapping_keys_and_sensitive_to_state():
    first = {"relationship": {"trust": 0.3, "tension": 0.1}, "energy": 0.7}
    reordered = {"energy": 0.7, "relationship": {"tension": 0.1, "trust": 0.3}}
    changed = {"energy": 0.6, "relationship": {"tension": 0.1, "trust": 0.3}}
    assert state_digest(first) == state_digest(reordered)
    assert state_digest(first) != state_digest(changed)


def test_checkpoint_records_latest_canonical_sequence_without_event_hash_chain():
    with tempfile.TemporaryDirectory() as d:
        p, subject_uuid = _store(os.path.join(d, "state.db"))
        p.log_event("Character", "user", 1, "input", {"text": "hello"})
        checkpoint = p.record_checkpoint("Character", "user", {"energy": 0.75, "beliefs": {"trust": 0.0}})
        assert checkpoint["subject_uuid"] == subject_uuid
        assert checkpoint["sequence"] == 1
        assert checkpoint["state_digest"] == state_digest({"energy": 0.75, "beliefs": {"trust": 0.0}})
        assert "previous_hash" not in checkpoint
        assert p.latest_checkpoint("Character", "user")["state_digest"] == checkpoint["state_digest"]


def test_export_import_round_trip_preserves_order_provenance_and_unknown_payload_fields():
    with tempfile.TemporaryDirectory() as d:
        source, subject_uuid = _store(os.path.join(d, "source.db"))
        source.log_event("Character", "user", 1, "input", {"text": "hello", "future_field": {"x": 1}})
        source.log_event("Character", "user", 2, "state_transition", {"pressure_after": {"fear": 0.2}})
        source.record_checkpoint("Character", "user", {"state": "source"})
        bundle = source.export_continuity_tail("Character", "user")

        target = Persistence(os.path.join(d, "target.db"))
        target.bind_subject("Character", "user", subject_uuid)
        assert target.import_continuity_tail("Character", "user", bundle) == 2
        imported = target.load_continuity_events("Character", "user")
        assert [event["sequence"] for event in imported] == [1, 2]
        assert imported[0]["payload"]["future_field"] == {"x": 1}
        assert imported[0]["source_actor"] == bundle["events"][0]["source_actor"]


def test_import_rejects_wrong_subject_and_sequence_gap():
    with tempfile.TemporaryDirectory() as d:
        p, subject_uuid = _store(os.path.join(d, "state.db"))
        wrong = {
            "schema_version": "1.0",
            "subject_uuid": str(uuid.uuid4()),
            "continuity_epoch": 0,
            "events": [],
        }
        with pytest.raises(ContinuityImportError, match="subject UUID mismatch"):
            p.import_continuity_tail("Character", "user", wrong)

        gap = {
            "schema_version": "1.0",
            "subject_uuid": subject_uuid,
            "continuity_epoch": 0,
            "events": [{
                "event_uuid": str(uuid.uuid4()),
                "sequence": 2,
                "canonicality": "canonical_event",
                "event_type": "input",
                "subject_time": 2,
                "wall_time": 1.0,
                "source_actor": "user",
                "source_class": "external_user",
                "authority_class": "reported_input",
                "visibility": "character_observed",
                "causal_parents": [],
                "payload_schema": "legacy-event-v1",
                "payload": {"text": "gap"},
            }],
        }
        with pytest.raises(ContinuityImportError, match="non-contiguous sequence"):
            p.import_continuity_tail("Character", "user", gap)


def test_integrity_report_detects_missing_sequence():
    with tempfile.TemporaryDirectory() as d:
        p, subject_uuid = _store(os.path.join(d, "state.db"))
        p.log_event("Character", "user", 1, "input", {"text": "one"})
        p.log_event("Character", "user", 2, "state_transition", {"x": 2})
        conn = p.conn
        try:
            conn.execute("DELETE FROM continuity_event WHERE subject_uuid=? AND user_id=? AND sequence=1", (subject_uuid, "user"))
            conn.commit()
        finally:
            conn.close()
        report = p.validate_continuity("Character", "user")
        assert report.ok is False
        assert report.missing_sequences == [1]


def test_legacy_backfill_is_idempotent_and_ignores_noncanonical_rows():
    with tempfile.TemporaryDirectory() as d:
        p, _ = _store(os.path.join(d, "state.db"))
        conn = p.conn
        try:
            conn.execute(
                "INSERT INTO event_log(character_id,user_id,timestep,event_type,payload,created_at) VALUES(?,?,?,?,?,?)",
                ("Character", "user", 1, "input", json.dumps({"text": "legacy"}), 1.0),
            )
            conn.execute(
                "INSERT INTO event_log(character_id,user_id,timestep,event_type,payload,created_at) VALUES(?,?,?,?,?,?)",
                ("Character", "user", 1, "renderer_output", json.dumps({"text": "not biography"}), 1.1),
            )
            conn.commit()
        finally:
            conn.close()
        assert p.backfill_legacy_events("Character", "user") == 1
        assert p.backfill_legacy_events("Character", "user") == 0
        events = p.load_continuity_events("Character", "user")
        assert len(events) == 1
        assert events[0]["event_type"] == "input"
        assert events[0]["legacy_event_id"] is not None


def test_sqlite_integrity_check_is_exposed_for_local_failure_detection():
    with tempfile.TemporaryDirectory() as d:
        p, _ = _store(os.path.join(d, "state.db"))
        assert p.sqlite_integrity_check().lower() == "ok"
