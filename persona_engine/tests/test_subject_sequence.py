"""Minimum subject-wide canonical ordering contract."""

import json
import os
import sqlite3
import tempfile
import uuid

from persona_engine.core.persistence import Persistence


def test_subject_sequence_orders_one_biography_without_replacing_stream_sequence():
    with tempfile.TemporaryDirectory() as d:
        p = Persistence(os.path.join(d, "state.db"))
        subject_uuid = str(uuid.uuid4())
        p.bind_subject("Character", "alice", subject_uuid)
        p.bind_subject("Character", "bob", subject_uuid)

        p.log_event("Character", "alice", 1, "input", {"text": "alice one"})
        p.log_event("Character", "bob", 2, "input", {"text": "bob one"})
        p.log_event("Character", "alice", 3, "state_transition", {"x": 1})

        events = p.load_subject_continuity_events("Character", "alice")
        assert [event["subject_sequence"] for event in events] == [1, 2, 3]
        assert [(event["user_id"], event["sequence"]) for event in events] == [
            ("alice", 1),
            ("bob", 1),
            ("alice", 2),
        ]


def test_existing_pre_subject_sequence_database_is_backfilled_deterministically():
    with tempfile.TemporaryDirectory() as d:
        path = os.path.join(d, "legacy.db")
        subject_uuid = str(uuid.uuid4())
        conn = sqlite3.connect(path)
        conn.execute(
            """CREATE TABLE continuity_event (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_uuid TEXT NOT NULL UNIQUE,
                subject_uuid TEXT NOT NULL,
                character_id TEXT NOT NULL,
                user_id TEXT NOT NULL,
                sequence INTEGER NOT NULL,
                continuity_epoch INTEGER NOT NULL DEFAULT 0,
                subject_time REAL NOT NULL,
                wall_time REAL NOT NULL,
                source_actor TEXT NOT NULL,
                source_class TEXT NOT NULL,
                authority_class TEXT NOT NULL,
                event_type TEXT NOT NULL,
                visibility TEXT NOT NULL,
                canonicality TEXT NOT NULL,
                causal_parents TEXT NOT NULL,
                payload_schema TEXT NOT NULL,
                payload TEXT NOT NULL,
                legacy_event_id INTEGER UNIQUE,
                UNIQUE(subject_uuid, user_id, continuity_epoch, sequence)
            )"""
        )
        rows = [
            (str(uuid.uuid4()), subject_uuid, "Character", "alice", 1, 0, 1.0, 10.0, "user", "external_user", "reported_input", "input", "character_observed", "canonical_event", "[]", "legacy-event-v1", json.dumps({"text": "first"}), 1),
            (str(uuid.uuid4()), subject_uuid, "Character", "bob", 1, 0, 2.0, 20.0, "user", "external_user", "reported_input", "input", "character_observed", "canonical_event", "[]", "legacy-event-v1", json.dumps({"text": "second"}), 2),
            (str(uuid.uuid4()), subject_uuid, "Character", "alice", 2, 0, 3.0, 30.0, "user", "external_user", "reported_input", "input", "character_observed", "canonical_event", "[]", "legacy-event-v1", json.dumps({"text": "third"}), 3),
        ]
        conn.executemany(
            "INSERT INTO continuity_event(event_uuid,subject_uuid,character_id,user_id,sequence,continuity_epoch,subject_time,wall_time,source_actor,source_class,authority_class,event_type,visibility,canonicality,causal_parents,payload_schema,payload,legacy_event_id) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            rows,
        )
        conn.commit()
        conn.close()

        p = Persistence(path)
        p.bind_subject("Character", "alice", subject_uuid)
        events = p.load_subject_continuity_events("Character", "alice")
        assert [event["subject_sequence"] for event in events] == [1, 2, 3]
        assert [event["user_id"] for event in events] == ["alice", "bob", "alice"]


def test_v1_export_keeps_existing_stream_shape_without_subject_sequence():
    with tempfile.TemporaryDirectory() as d:
        p = Persistence(os.path.join(d, "state.db"))
        subject_uuid = str(uuid.uuid4())
        p.bind_subject("Character", "user", subject_uuid)
        p.log_event("Character", "user", 1, "input", {"text": "hello"})

        local_event = p.load_continuity_events("Character", "user")[0]
        bundle_event = p.export_continuity_tail("Character", "user")["events"][0]

        assert local_event["subject_sequence"] == 1
        assert "subject_sequence" not in bundle_event
        assert bundle_event["sequence"] == 1
