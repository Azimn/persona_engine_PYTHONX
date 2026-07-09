"""Memory wording contract.

Memories are character-side records. They should read as first-person lived
history, while renderer speech remains noncanonical event evidence.
"""

from pathlib import Path

from persona_engine.agent import CharacterAgent
from persona_engine.core.memory import MemoryStore, MemoryUnit, first_person_memory_content


ROOT = Path(__file__).resolve().parents[1]
PRET = ROOT / "cartridges" / "pretorius.snp"


def test_user_turn_memory_is_first_person(tmp_path):
    agent = CharacterAgent(cartridge_path=str(PRET), user_id="u", db_path=str(tmp_path / "s.db"))
    agent.say("Please remember the word lantern.")

    contents = [m.content for m in agent.engine.memory.memories]
    assert any(content.startswith("I heard you say:") for content in contents)
    assert not any(content.startswith("User stated:") for content in contents)


def test_sensorium_memory_is_first_person(tmp_path):
    agent = CharacterAgent(cartridge_path=str(PRET), user_id="u", db_path=str(tmp_path / "s.db"))
    agent.say("...", server_truth={"user_absent_minutes": 90, "user_presence": "returned"})

    contents = [m.content for m in agent.engine.memory.memories if "sensorium" in m.tags]
    assert contents
    assert all(content.startswith(("I noticed", "I felt")) for content in contents)
    assert not any(content.startswith("[sensorium]") for content in contents)


def test_legacy_memory_formats_normalize_to_first_person():
    assert first_person_memory_content("User stated: The word was lantern.") == "I heard you say: The word was lantern."
    assert first_person_memory_content("[sensorium] body_state: body is depleted") == "I noticed my body state: body is depleted"
    assert first_person_memory_content("[reflection] Recent exchanges formed a pattern.") == "I formed a reflection: Recent exchanges formed a pattern."


def test_memory_store_normalizes_legacy_content_on_add():
    store = MemoryStore()
    store.add(MemoryUnit("User mentioned a chair", created_at=1.0))

    assert store.memories[0].content == "I heard you mention a chair"


def test_persisted_memory_reloads_as_first_person(tmp_path):
    db = str(tmp_path / "s.db")
    agent = CharacterAgent(cartridge_path=str(PRET), user_id="u", db_path=db)
    agent.say("Please remember the word lantern.")

    restarted = CharacterAgent(cartridge_path=str(PRET), user_id="u", db_path=db)
    contents = [m.content for m in restarted.engine.memory.memories]
    assert any(content.startswith("I heard you say:") for content in contents)
    assert not any(content.startswith("User stated:") for content in contents)
