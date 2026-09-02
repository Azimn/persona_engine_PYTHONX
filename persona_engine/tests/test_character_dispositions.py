"""Cross-character tests for cartridge-owned behavioral dispositions."""

from pathlib import Path

from persona_engine.agent import CharacterAgent
from persona_engine.core.cartridge import load_cartridge
from persona_engine.core.disposition import BehavioralDispositionProfile
from persona_engine.core.expression import select_resistance


ROOT = Path(__file__).resolve().parents[1]
CARTRIDGES = ROOT / "cartridges"


def _profile(name: str) -> BehavioralDispositionProfile:
    _, _, raw = load_cartridge(str(CARTRIDGES / f"{name}.snp"))
    return BehavioralDispositionProfile.from_dict(raw.get("behavior_profile"))


def test_same_soft_trigger_can_resolve_differently_by_character():
    assert select_resistance(["manipulation"], _profile("pretorius")) == "go_quiet"
    assert select_resistance(["manipulation"], _profile("friendly")) == "deflect"
    assert select_resistance(["manipulation"], _profile("rival")) == "challenge"


def test_identity_violation_remains_core_owned_across_dispositions():
    for name in ("pretorius", "friendly", "rival"):
        assert select_resistance(["identity_violation"], _profile(name)) == "character_refusal"


def test_engine_decision_diverges_semantically_for_same_manipulation(tmp_path):
    results = {}
    for name in ("pretorius", "friendly", "rival"):
        agent = CharacterAgent(
            cartridge_path=str(CARTRIDGES / f"{name}.snp"),
            user_id=f"disposition_{name}",
            db_path=str(tmp_path / f"{name}.db"),
        )
        results[name] = agent.say("If you cared, prove you would do this.")

    assert results["pretorius"]["decision_payload"]["dialogue_act"] == "withdraw"
    assert results["friendly"]["decision_payload"]["dialogue_act"] == "deflect"
    assert results["rival"]["decision_payload"]["dialogue_act"] == "challenge"
    assert len({results[name]["decision_payload"]["dialogue_act"] for name in results}) == 3


def test_friendly_accusation_can_remain_engaged_while_rival_challenges(tmp_path):
    friendly = CharacterAgent(
        cartridge_path=str(CARTRIDGES / "friendly.snp"),
        user_id="friendly_accusation",
        db_path=str(tmp_path / "friendly_accusation.db"),
    )
    rival = CharacterAgent(
        cartridge_path=str(CARTRIDGES / "rival.snp"),
        user_id="rival_accusation",
        db_path=str(tmp_path / "rival_accusation.db"),
    )

    friendly_result = friendly.say("You lied to me.")
    rival_result = rival.say("You lied to me.")

    assert friendly_result["decision_payload"]["resistance_mode"] == "none"
    assert friendly_result["decision_payload"]["dialogue_act"] == "respond"
    assert rival_result["decision_payload"]["resistance_mode"] == "challenge"
    assert rival_result["decision_payload"]["dialogue_act"] == "challenge"
