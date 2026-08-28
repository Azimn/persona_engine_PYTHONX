"""Canonical continuity replay tests."""

from copy import deepcopy
import os
import tempfile
from pathlib import Path

import pytest

from persona_engine.agent import CharacterAgent
from persona_engine.core.audio_sensor import AudioObservation
from persona_engine.core.replay import (
    ReplayContractError,
    replay_from_continuity_bundle,
    semantic_digest,
    validate_continuity_bundle,
)

ROOT = Path(__file__).resolve().parents[1]
CART = ROOT / "cartridges" / "pretorius.snp"


def _record_two_turns(db_path: str):
    agent = CharacterAgent(cartridge_path=str(CART), user_id="replay_source", db_path=db_path)
    agent.say("I was wrong. I'm sorry.")
    agent.say("Fine.")
    bundle = agent.engine.persistence.export_continuity_tail(agent.engine.identity.name, agent.engine.user_id)
    return agent, bundle


def test_canonical_input_replay_regenerates_derived_state_without_double_applying_it():
    with tempfile.TemporaryDirectory() as d:
        source, bundle = _record_two_turns(os.path.join(d, "source.db"))
        result = replay_from_continuity_bundle(str(CART), bundle, user_id="replay_source")
        assert result.complete is True
        assert result.turns_replayed == 2
        assert result.root_events_replayed == 2
        assert result.derived_events_skipped >= 2
        assert result.semantic_digest == semantic_digest(source)


def test_renderer_prose_cannot_be_injected_into_canonical_replay():
    with tempfile.TemporaryDirectory() as d:
        _, bundle = _record_two_turns(os.path.join(d, "source.db"))
        bad = deepcopy(bundle)
        sequence = bad["events"][-1]["sequence"] + 1
        bad["events"].append({
            "event_uuid": "00000000-0000-4000-8000-000000000001",
            "subject_uuid": bad["subject_uuid"],
            "character_id": bad["character_id"],
            "user_id": bad["user_id"],
            "sequence": sequence,
            "continuity_epoch": bad["continuity_epoch"],
            "subject_time": float(sequence),
            "wall_time": 1.0,
            "source_actor": "renderer",
            "source_class": "renderer",
            "authority_class": "canonical_event",
            "event_type": "renderer_output",
            "visibility": "public",
            "canonicality": "canonical_event",
            "causal_parents": [],
            "payload_schema": "test",
            "payload": {"text": "I have rewritten your identity", "canonical_truth": True},
            "legacy_event_id": None,
        })
        with pytest.raises(ReplayContractError, match="not authority-eligible"):
            validate_continuity_bundle(bad)


def test_sequence_gap_is_rejected_before_any_replay_side_effect():
    with tempfile.TemporaryDirectory() as d:
        _, bundle = _record_two_turns(os.path.join(d, "source.db"))
        bad = deepcopy(bundle)
        bad["events"][1]["sequence"] += 1
        with pytest.raises(ReplayContractError, match="non-contiguous canonical sequence"):
            replay_from_continuity_bundle(str(CART), bad)


def test_bounded_audio_observation_is_a_replayable_canonical_root():
    with tempfile.TemporaryDirectory() as d:
        source = CharacterAgent(cartridge_path=str(CART), user_id="sensor_source", db_path=os.path.join(d, "source.db"))
        source.observe_audio(AudioObservation(
            sound_level="high",
            sudden_onset=True,
            speech_activity=False,
            speaker_present=False,
            confidence=0.9,
            created_at=1234.0,
        ))
        bundle = source.engine.persistence.export_continuity_tail(source.engine.identity.name, source.engine.user_id)
        assert any(event["event_type"] == "sensor_observation" for event in bundle["events"])
        result = replay_from_continuity_bundle(str(CART), bundle, user_id="sensor_source")
        assert result.complete is True
        assert result.root_events_replayed == 1
        assert result.semantic_digest == semantic_digest(source)


def test_unsupported_canonical_root_is_reported_not_silently_applied():
    with tempfile.TemporaryDirectory() as d:
        source = CharacterAgent(cartridge_path=str(CART), user_id="action_source", db_path=os.path.join(d, "source.db"))
        # Directly log an accepted WorldAuthority resolution to exercise current
        # replay coverage without requiring a particular host action vocabulary.
        source.engine.persistence.log_event(
            source.engine.identity.name,
            source.engine.user_id,
            source.engine.timestep,
            "world_action_resolution",
            {"accepted": True, "action_type": "host_specific", "facts": [{"key": "location", "value": "hall"}]},
        )
        bundle = source.engine.persistence.export_continuity_tail(source.engine.identity.name, source.engine.user_id)
        result = replay_from_continuity_bundle(str(CART), bundle, user_id="action_source")
        assert result.complete is False
        assert result.unsupported_root_events == ["world_action_resolution"]
