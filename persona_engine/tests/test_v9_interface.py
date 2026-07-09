"""v9 semi-embodiment interface tests."""

from pathlib import Path
import os
import tempfile
import time

from persona_engine.agent import CharacterAgent
from persona_engine.core.intention import OpenLoop
from persona_engine.ui import stream_payload_chunks

ROOT = Path(__file__).resolve().parents[1]
CART = ROOT / "cartridges" / "pretorius.snp"


def _agent(tmpdir):
    return CharacterAgent(cartridge_path=str(CART), user_id="interface_user", db_path=os.path.join(tmpdir, "state.db"))


def test_public_status_contains_only_categorical_strings():
    with tempfile.TemporaryDirectory() as d:
        agent = _agent(d)
        agent.say("Hello.", visible_context={"user_presence": "present", "noise_level": "high"})
        status = agent.public_status()
        assert status["avatar_state"] in {"neutral", "attentive", "guarded", "tense", "tired", "overloaded", "restless"}
        assert status["energy"] in {"low", "steady", "high"}
        assert all(isinstance(value, str) for value in status.values())
        assert not any(isinstance(value, (int, float)) for value in status.values())


def test_turn_result_exposes_ui_state_without_raw_authoring():
    with tempfile.TemporaryDirectory() as d:
        agent = _agent(d)
        result = agent.say("You lied to me.", server_truth={"user_absent_minutes": 47}, visible_context={"room_sound": "quiet"})
        assert result["public_status"]
        assert result["avatar_state"] == result["public_status"]["avatar_state"]
        assert isinstance(result["second_thoughts"], list)
        assert result["stream_plan"]["source"] == "core_engine"


def test_proactive_events_are_read_only_proposals():
    with tempfile.TemporaryDirectory() as d:
        agent = _agent(d)
        now = time.time()
        agent.engine.intentions.add_open_loop(OpenLoop(
            topic="unresolved test matter",
            emotional_charge=0.9,
            created_at=now - 120,
            last_touched=now - 120,
            urgency=0.9,
            preferred_resolution="return carefully",
        ))
        before = len(agent.engine.intentions.open_loops)
        events = agent.poll_proactive_events()
        after = len(agent.engine.intentions.open_loops)
        assert before == after
        assert events and events[0]["event_type"] == "open_loop_return"


def test_sse_chunk_helper_authors_no_state():
    chunks = list(stream_payload_chunks("one two", delay_seconds=0.0))
    assert chunks[0].startswith("data:")
    assert chunks[-1].startswith("data:")
    assert "token" in chunks[0]


def test_ui_layer_has_no_direct_state_persistence_calls():
    ui_text = (ROOT / "ui.py").read_text(encoding="utf-8")
    forbidden = [".persistence.save", ".persistence.log_event", ".body.", ".world.", ".relationship.", ".pressures."]
    for term in forbidden:
        assert term not in ui_text
