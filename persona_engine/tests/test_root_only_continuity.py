"""Root-only durable continuity and v1 migration compatibility."""

import os
import tempfile
import uuid
from pathlib import Path

from persona_engine.agent import CharacterAgent
from persona_engine.core.persistence import Persistence
from persona_engine.core.replay import replay_from_continuity_bundle, validate_continuity_bundle

ROOT = Path(__file__).resolve().parents[1]
CART = ROOT / "cartridges" / "pretorius.snp"


def test_runtime_writes_only_causal_root_with_exogenous_input_context():
    with tempfile.TemporaryDirectory() as d:
        agent = CharacterAgent(cartridge_path=str(CART), user_id="root_only", db_path=os.path.join(d, "state.db"))
        agent.say(
            "I am in the north gallery.",
            server_truth={"zone": "north_gallery", "bell_state": "ringing"},
            visible_context={"notice_board": "restoration scheduled"},
        )
        events = agent.engine.persistence.load_continuity_events(agent.engine.identity.name, agent.engine.user_id)
        assert [event["event_type"] for event in events] == ["input"]
        event = events[0]
        assert event["payload_schema"] == "input-root-v2"
        assert event["payload"] == {
            "user_text": "I am in the north gallery.",
            "server_truth": {"zone": "north_gallery", "bell_state": "ringing"},
            "visible_context": {"notice_board": "restoration scheduled"},
        }
        assert "classification" not in event["payload"]
        assert "canonical_truth" not in event["payload"]
        assert "memory_types" not in event["payload"]


def _legacy_event(subject_uuid, sequence, event_type, payload, authority="canonical_event"):
    return {
        "event_uuid": str(uuid.uuid4()),
        "subject_uuid": subject_uuid,
        "character_id": "Pretorius",
        "user_id": "legacy_user",
        "sequence": sequence,
        "continuity_epoch": 0,
        "subject_time": float(sequence),
        "wall_time": float(sequence),
        "source_actor": "legacy",
        "source_class": "legacy",
        "authority_class": authority,
        "event_type": event_type,
        "visibility": "character_observed",
        "canonicality": "canonical_event",
        "causal_parents": [],
        "payload_schema": "legacy-event-v1",
        "payload": payload,
        "legacy_event_id": None,
    }


def test_legacy_v1_derived_rows_remain_importable_and_replayable():
    subject_uuid = str(uuid.uuid4())
    bundle = {
        "schema_version": "1.0",
        "subject_uuid": subject_uuid,
        "character_id": "Pretorius",
        "user_id": "legacy_user",
        "continuity_epoch": 0,
        "after_sequence": 0,
        "events": [
            _legacy_event(subject_uuid, 1, "input", {"user_text": "Hello."}, "reported_input"),
            _legacy_event(subject_uuid, 2, "state_transition", {"relationship_after": {"trust": 0.0}}, "character_state_authority"),
            _legacy_event(subject_uuid, 3, "sensorium", {"world": {"zone": "study"}}, "world_authority"),
        ],
        "checkpoint": None,
    }
    validated = validate_continuity_bundle(bundle)
    assert [event["event_type"] for event in validated] == ["input", "state_transition", "sensorium"]
    replay = replay_from_continuity_bundle(str(CART), bundle, user_id="legacy_user")
    assert replay.complete is True
    assert replay.root_events_replayed == 1
    assert replay.derived_events_skipped == 2
    with tempfile.TemporaryDirectory() as d:
        store = Persistence(os.path.join(d, "state.db"))
        store.bind_subject("Pretorius", "legacy_user", subject_uuid)
        assert store.import_continuity_tail("Pretorius", "legacy_user", bundle) == 3
        assert [e["event_type"] for e in store.load_continuity_events("Pretorius", "legacy_user")] == [
            "input", "state_transition", "sensorium"
        ]
