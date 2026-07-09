"""Tests for v7 artificial world and somatic runtime."""

from pathlib import Path

from persona_engine.agent import CharacterAgent
from persona_engine.core.cartridge import load_cartridge

ROOT = Path(__file__).resolve().parents[1]
PRET = ROOT / "cartridges" / "pretorius.snp"


def test_cartridge_carries_world_and_body_profiles():
    _core, _ledger, raw = load_cartridge(str(PRET))
    assert raw["body_profile"]["preferred_posture"] == "seated"
    assert raw["world_profile"]["default_zone"] == "study"
    assert raw["interpretation_bias"]["identity_attack"] == "continuity_threat"


def test_absence_and_world_tick_affect_body_and_pressure(tmp_path):
    agent = CharacterAgent(cartridge_path=str(PRET), user_id="u", db_path=str(tmp_path / "s.db"))
    before_movement = agent.engine.body.need_for_movement
    agent.say("...", server_truth={"user_absent_minutes": 90, "user_presence": "returned"}, visible_context={"room_sound": "quiet", "light_level": "dim"})
    assert agent.engine.body.attention_target == "user"
    assert agent.engine.world.zone == "study"
    assert agent.engine.body.need_for_movement >= before_movement
    assert agent.engine.sensorium.recent()
    assert any(m.source.value == "observed" and "sensorium" in m.tags for m in agent.engine.memory.memories)


def test_workspace_receives_world_body_and_sensorium(tmp_path):
    agent = CharacterAgent(cartridge_path=str(PRET), user_id="u", db_path=str(tmp_path / "s.db"))
    result = agent.say("Did you hear that?", visible_context={"ambient_event": "sound in hallway", "noise_level": "high"})
    prompt = result["system_prompt"]
    assert "Artificial world:" in prompt
    assert "Somatic state:" in prompt
    assert "Sensorium:" in prompt
    assert "sound in hallway" in prompt


def test_world_body_state_persists_across_restart(tmp_path):
    db = str(tmp_path / "s.db")
    agent = CharacterAgent(cartridge_path=str(PRET), user_id="u", db_path=db)
    agent.say("Hello.", visible_context={"noise_level": "high", "light_level": "bright", "zone": "studio"})
    load = agent.engine.body.sensory_load
    agent2 = CharacterAgent(cartridge_path=str(PRET), user_id="u", db_path=db)
    assert agent2.engine.world.zone == "studio"
    assert agent2.engine.world.noise_level == "high"
    assert agent2.engine.body.sensory_load == load


def test_new_runtime_modules_are_character_agnostic():
    forbidden = ["Klaus", "Pretorius", "Jay", "stoic", "melancholic"]
    for module in ["body.py", "world.py", "sensorium.py", "organism_tick.py"]:
        text = (ROOT / "core" / module).read_text(encoding="utf-8")
        lowered = text.lower()
        for term in forbidden:
            assert term.lower() not in lowered, f"{term} leaked into {module}"
