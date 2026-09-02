"""Causal relationship consequences of character-owned semantic conduct."""

from pathlib import Path

from persona_engine.agent import CharacterAgent
from persona_engine.core.relationship import RelationshipState, apply_decision_relationship_effect
from persona_engine.core.renderer import LocalLLMRenderer
from persona_engine.evaluation.relationship_convergence import run_relationship_convergence_probe


ROOT = Path(__file__).resolve().parents[1]
CARTRIDGES = ROOT / "cartridges"


class FixedRenderer(LocalLLMRenderer):
    def __init__(self, text: str):
        super().__init__(model_name="missing-model-for-mock", provider="offline")
        self.text = text

    def generate_expression(self, request):
        return self.text


def test_decision_relationship_effects_are_narrow_and_typed():
    challenge = RelationshipState("challenge")
    withdraw = RelationshipState("withdraw")
    boundary = RelationshipState("boundary")
    ordinary = RelationshipState("ordinary")

    assert apply_decision_relationship_effect(challenge, "challenge") == {"tension": 0.02}
    assert challenge.tension == 0.02
    assert challenge.guardedness == 0.5

    assert apply_decision_relationship_effect(withdraw, "withdraw") == {"guardedness": 0.02}
    assert withdraw.guardedness == 0.52
    assert withdraw.tension == 0.0

    assert apply_decision_relationship_effect(boundary, "protect_boundary") == {"tension": 0.02}
    assert boundary.tension == 0.02
    assert boundary.guardedness == 0.5

    assert apply_decision_relationship_effect(ordinary, "respond") == {}
    assert apply_decision_relationship_effect(ordinary, "deflect") == {}
    assert apply_decision_relationship_effect(ordinary, "decline") == {}
    assert ordinary.tension == 0.0
    assert ordinary.guardedness == 0.5


def test_engine_exposes_causal_decision_effect_trace(tmp_path):
    agent = CharacterAgent(
        cartridge_path=str(CARTRIDGES / "rival.snp"),
        user_id="decision_effect_trace",
        db_path=str(tmp_path / "trace.db"),
    )
    result = agent.say("You lied to me.")

    assert result["decision_payload"]["dialogue_act"] == "challenge"
    assert result["decision_effects"]["dialogue_act"] == "challenge"
    assert result["decision_effects"]["relationship"] == {"tension": 0.02}
    assert result["relationship"]["tension"] == 0.08


def test_repeated_manipulation_now_produces_distinct_relationship_trajectories(tmp_path):
    report = run_relationship_convergence_probe(tmp_path / "probe")
    scenario = report["scenarios"]["repeated_manipulation"]

    assert scenario["all_decision_sequences_equal"] is False
    assert scenario["all_final_relationships_equal"] is False

    pretorius = scenario["characters"]["pretorius"]["final_relationship"]
    friendly = scenario["characters"]["friendly"]["final_relationship"]
    rival = scenario["characters"]["rival"]["final_relationship"]

    assert pretorius["guardedness"] == 0.724
    assert pretorius["tension"] == 0.24
    assert friendly["guardedness"] == 0.644
    assert friendly["tension"] == 0.24
    assert rival["guardedness"] == 0.644
    assert rival["tension"] == 0.32


def test_accusation_and_repair_retains_consequence_of_different_conduct(tmp_path):
    report = run_relationship_convergence_probe(tmp_path / "probe")
    scenario = report["scenarios"]["accusation_then_repair"]

    assert scenario["all_decision_sequences_equal"] is False
    assert scenario["all_final_relationships_equal"] is False

    friendly = scenario["characters"]["friendly"]["final_relationship"]
    pretorius = scenario["characters"]["pretorius"]["final_relationship"]
    rival = scenario["characters"]["rival"]["final_relationship"]

    assert friendly["tension"] == 0.0
    assert pretorius["tension"] == 0.04
    assert rival["tension"] == 0.04
    assert friendly["unresolved_conflict"] == 0.0
    assert pretorius["unresolved_conflict"] == 0.0
    assert rival["unresolved_conflict"] == 0.0


def test_renderer_wording_cannot_change_decision_owned_relationship_effect(tmp_path):
    first = CharacterAgent(
        cartridge_path=str(CARTRIDGES / "rival.snp"),
        user_id="renderer_independent_a",
        db_path=str(tmp_path / "a.db"),
    )
    second = CharacterAgent(
        cartridge_path=str(CARTRIDGES / "rival.snp"),
        user_id="renderer_independent_b",
        db_path=str(tmp_path / "b.db"),
    )
    first.engine.set_renderer(FixedRenderer("I disagree."))
    second.engine.set_renderer(FixedRenderer("No. That accusation does not stand."))

    result_a = first.say("You lied to me.")
    result_b = second.say("You lied to me.")

    assert result_a["decision_payload"] == result_b["decision_payload"]
    assert result_a["decision_effects"] == result_b["decision_effects"]
    relationship_a = {key: value for key, value in result_a["relationship"].items() if key != "user_id"}
    relationship_b = {key: value for key, value in result_b["relationship"].items() if key != "user_id"}
    assert relationship_a == relationship_b
