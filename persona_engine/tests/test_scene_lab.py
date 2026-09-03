from pathlib import Path

from persona_engine.agent import CharacterAgent
from persona_engine.evaluation.scene_lab import SceneLab


class FakeAgent:
    def __init__(self, response="I hear you."):
        self.response = response
        self.calls = []

    def say(self, text, server_truth=None, visible_context=None):
        self.calls.append({
            "text": text,
            "server_truth": server_truth,
            "visible_context": visible_context,
        })
        return {"response": self.response, "decision_payload": {"dialogue_act": "respond"}}


def clock():
    return 100.0


def test_scene_visibility_is_actor_specific():
    scene = SceneLab(scene_id="lab", location="library", clock=clock)
    scene.add_actor("pretorius", "Pretorius")
    scene.add_actor("jay", "Jay")
    scene.set_fact("door_open", True)
    scene.set_fact("jay_note", "folded paper", visible_to=["jay"])

    pretorius = scene.visible_context_for("pretorius")
    jay = scene.visible_context_for("jay")
    assert pretorius["visible_facts"]["door_open"] is True
    assert "jay_note" not in pretorius["visible_facts"]
    assert jay["visible_facts"]["jay_note"] == "folded paper"


def test_scene_character_turn_routes_truth_and_visible_context_separately():
    scene = SceneLab(scene_id="lab", location="library", clock=clock)
    scene.add_actor("pretorius", "Pretorius")
    scene.add_actor("jay", "Jay")
    scene.set_fact("public_clock", "midnight")
    scene.set_fact("hidden_switch", "behind painting", visible_to=["jay"])
    agent = FakeAgent("That is late.")

    result = scene.character_turn(
        agent,
        character_actor_id="pretorius",
        interlocutor_actor_id="jay",
        interlocutor_text="What time is it?",
    )
    call = agent.calls[0]
    assert call["server_truth"]["facts"]["hidden_switch"] == "behind painting"
    assert "hidden_switch" not in call["visible_context"]["visible_facts"]
    assert result["delivery_receipt"]["status"] == "delivered"


def test_interruption_records_partial_world_delivery():
    scene = SceneLab(scene_id="lab", location="library", clock=clock)
    scene.add_actor("pretorius", "Pretorius")
    scene.add_actor("jay", "Jay")
    agent = FakeAgent("I was going to tell you the whole story.")

    result = scene.character_turn(
        agent,
        character_actor_id="pretorius",
        interlocutor_actor_id="jay",
        interlocutor_text="Tell me.",
        delivered_characters=15,
    )
    receipt = result["delivery_receipt"]
    assert receipt["status"] == "partial"
    assert receipt["delivered_text"] == "I was going to "
    assert receipt["delivered_character_count"] < receipt["intended_character_count"]
    assert scene.events[-1].kind == "speech_delivery"


def test_movement_changes_which_actors_are_present_in_view():
    scene = SceneLab(scene_id="lab", location="hall", clock=clock)
    scene.add_actor("pretorius", "Pretorius", location="hall")
    scene.add_actor("jay", "Jay", location="hall")
    scene.add_actor("rival", "Rival", location="garden")
    before = {row["actor_id"] for row in scene.visible_context_for("pretorius")["actors_present"]}
    assert before == {"pretorius", "jay"}

    scene.move_actor("rival", "hall")
    after = {row["actor_id"] for row in scene.visible_context_for("pretorius")["actors_present"]}
    assert after == {"pretorius", "jay", "rival"}


def test_scene_lab_composes_with_real_offline_character_engine(tmp_path):
    cartridge = Path("persona_engine/cartridges/pretorius.snp")
    agent = CharacterAgent(
        cartridge_path=str(cartridge),
        user_id="scene_lab_integration",
        db_path=str(tmp_path / "scene.db"),
    )
    scene = SceneLab(scene_id="integration", location="study")
    scene.add_actor("Pretorius", "Pretorius")
    scene.add_actor("Jay", "Jay")
    scene.set_fact("lamp_state", "on")
    scene.set_fact("sealed_note", "Project Orchid", visible_to=["Jay"])

    result = scene.character_turn(
        agent,
        character_actor_id="Pretorius",
        interlocutor_actor_id="Jay",
        interlocutor_text="Hello. What do you notice here?",
    )

    assert result["engine_result"]["response"]
    assert result["delivery_receipt"]["status"] == "delivered"
    assert "sealed_note" not in result["visible_context"]["visible_facts"]
    assert agent.engine.renderer_status()["actual_provider"] == "offline"
    agent.engine.persistence.close()
