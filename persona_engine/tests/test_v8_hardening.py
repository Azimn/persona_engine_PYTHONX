"""v8 hardening tests for schema, event authority, replay, and memory firewall."""

from pathlib import Path
import os
import tempfile

import pytest

from persona_engine.agent import CharacterAgent
from persona_engine.core.cartridge import CartridgeError, load_cartridge
from persona_engine.core.replay import export_event_log, replay_from_events, state_digest

ROOT = Path(__file__).resolve().parents[1]
CART = ROOT / "cartridges" / "pretorius.snp"


def test_cartridge_rejects_unknown_engine_leak_field(tmp_path):
    text = (ROOT / "cartridges" / "neutral.snp").read_text()
    bad = tmp_path / "bad.snp"
    bad.write_text(text + "\n[engine_default]\ncharacter_name = 'bad'\n")
    with pytest.raises(CartridgeError, match="unknown field"):
        load_cartridge(str(bad))


def test_cartridge_rejects_out_of_range_body_profile(tmp_path):
    text = (ROOT / "cartridges" / "neutral.snp").read_text().replace("baseline_energy = 0.75", "baseline_energy = 1.75")
    bad = tmp_path / "bad_range.snp"
    bad.write_text(text)
    with pytest.raises(CartridgeError, match="baseline_energy"):
        load_cartridge(str(bad))


def test_event_log_records_canonical_trace_and_speech_noncanonical():
    with tempfile.TemporaryDirectory() as d:
        agent = CharacterAgent(cartridge_path=str(CART), user_id="jay", db_path=os.path.join(d, "state.db"))
        agent.add_pressure("shame", 0.4)
        agent.say("You lied to me.", server_truth={"user_absent_minutes": 25}, visible_context={"room_sound": "quiet"})
        events = export_event_log(agent.engine.persistence, agent.engine.identity.name, agent.engine.user_id)
        event_types = {e["event_type"] for e in events}
        assert {"input", "state_transition", "belief", "speech", "turn"}.issubset(event_types)
        speech = [e for e in events if e["event_type"] == "speech"][-1]
        assert speech["payload"]["response_is_canonical_truth"] is False


def test_replay_uses_input_events_and_produces_state_digest():
    with tempfile.TemporaryDirectory() as d:
        agent = CharacterAgent(cartridge_path=str(CART), user_id="jay", db_path=os.path.join(d, "state.db"))
        for text in ["Hello.", "You lied to me.", "I'm sorry."]:
            agent.say(text)
        events = export_event_log(agent.engine.persistence, agent.engine.identity.name, agent.engine.user_id)
        replay = replay_from_events(str(CART), events, user_id="jay")
        assert replay.turns_replayed == 3
        digest = replay.final_digest
        assert digest["timestep"] >= 3
        assert "relationship" in digest and "pressures" in digest and "memory_count" in digest


def test_renderer_output_is_not_canonical_memory_truth():
    with tempfile.TemporaryDirectory() as d:
        agent = CharacterAgent(cartridge_path=str(CART), user_id="jay", db_path=os.path.join(d, "state.db"))
        res = agent.say("I apologize. Let me make it right.")
        assert res["response"]
        assert any("canonical_user_statement" in m.tags for m in agent.engine.memory.memories)
        assert not any("Response:" in m.content for m in agent.engine.memory.memories)


def test_core_modules_have_no_character_specific_literals():
    forbidden = ["Klaus", "Pretorius", "Jay", "stoic", "melancholic", "obedient pet"]
    allowed_files = {"cartridge.py"}  # schema errors may mention cartridge, not character literals
    core_dir = ROOT / "core"
    for path in core_dir.glob("*.py"):
        if path.name in allowed_files:
            continue
        text = path.read_text(encoding="utf-8").lower()
        for term in forbidden:
            assert term.lower() not in text, f"{term} leaked into {path.name}"
