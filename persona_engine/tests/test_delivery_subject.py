from pathlib import Path

from persona_engine.agent import CharacterAgent
from persona_engine.core.delivery import make_text_delivery_receipt
from persona_engine.evaluation.scene_lab import SceneLab


CARTRIDGE = Path("persona_engine/cartridges/pretorius.snp")


def test_partial_delivery_becomes_lived_subject_evidence_and_survives_restart(tmp_path):
    db_path = tmp_path / "delivery.db"
    agent = CharacterAgent(
        cartridge_path=str(CARTRIDGE),
        user_id="delivery",
        db_path=str(db_path),
    )
    receipt = make_text_delivery_receipt(
        receipt_id="r1",
        speech_id="s1",
        intended_text="I was going to tell you the whole story.",
        delivered_text="I was going to ",
        created_at=10.0,
        reason="interrupted",
    )
    payload = agent.record_delivery_receipt(receipt)
    memory_id = payload["memory_id"]
    assert "interrupted before I finished" in payload["lived_experience"]
    assert agent.engine.pressures.pressures["startle"].magnitude > 0
    agent.engine.persistence.close()

    restored = CharacterAgent(
        cartridge_path=str(CARTRIDGE),
        user_id="delivery",
        db_path=str(db_path),
    )
    try:
        memory = next(item for item in restored.engine.memory.memories if item.id == memory_id)
        assert "delivery:partial" in memory.tags
        assert memory.unresolved is True
        assert "I was going to " in memory.content
        assert "the whole story" not in memory.content
    finally:
        restored.engine.persistence.close()


def test_scene_lab_automatically_writes_real_delivery_back_to_real_agent(tmp_path):
    agent = CharacterAgent(
        cartridge_path=str(CARTRIDGE),
        user_id="scene_delivery",
        db_path=str(tmp_path / "scene.db"),
    )
    scene = SceneLab(scene_id="delivery-scene", location="study")
    scene.add_actor("Pretorius", "Pretorius")
    scene.add_actor("Jay", "Jay")
    try:
        result = scene.character_turn(
            agent,
            character_actor_id="Pretorius",
            interlocutor_actor_id="Jay",
            interlocutor_text="Tell me what you were thinking.",
            delivered_characters=8,
        )
        assert result["delivery_receipt"]["status"] == "partial"
        assert result["subject_delivery_experience"] is not None
        memory_id = result["subject_delivery_experience"]["memory_id"]
        memory = next(item for item in agent.engine.memory.memories if item.id == memory_id)
        assert memory.tags >= {"speech_delivery", "delivery:partial"}
        assert memory.content.startswith("I began to say:")
    finally:
        agent.engine.persistence.close()
