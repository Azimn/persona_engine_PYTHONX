"""Behavioral richness exposes cartridge character through bounded moves."""

from pathlib import Path

from persona_engine.agent import CharacterAgent
from persona_engine.core.cartridge import load_cartridge
from persona_engine.core.offline_conversation import (
    BehavioralTendency,
    derive_conversation_candidate,
    parse_behavioral_tendencies,
    select_behavioral_tendency,
)


ROOT = Path(__file__).resolve().parents[1]
PRETORIUS = ROOT / "cartridges" / "pretorius.snp"
KIKI = ROOT / "cartridges" / "kiki.snp"


def _agent(tmp_path, cartridge: Path, name: str) -> CharacterAgent:
    return CharacterAgent(
        cartridge_path=str(cartridge),
        user_id="behavior_user",
        db_path=str(tmp_path / f"{name}.db"),
    )


def _tendency(**overrides) -> BehavioralTendency:
    values = {
        "tendency_id": "test_probe",
        "trigger_acts": ("inform",),
        "preferred_move": "probe",
        "bias": 0.1,
        "requires_memory": False,
        "requires_activity": False,
        "min_familiarity": 0.0,
        "max_pressure": 1.0,
        "cooldown_turns": 2,
        "performance_tendency_id": None,
    }
    values.update(overrides)
    return BehavioralTendency(**values)


def test_tendency_selection_enforces_memory_activity_pressure_and_cooldown():
    tendency = _tendency(requires_memory=True, requires_activity=True, max_pressure=0.6)

    assert select_behavioral_tendency(
        tendencies=(tendency,), input_act="inform", has_memory=False,
        has_activity=True, familiarity=1.0, pressure=0.2, turn=10,
        recent_history=(),
    ) is None
    assert select_behavioral_tendency(
        tendencies=(tendency,), input_act="inform", has_memory=True,
        has_activity=False, familiarity=1.0, pressure=0.2, turn=10,
        recent_history=(),
    ) is None
    assert select_behavioral_tendency(
        tendencies=(tendency,), input_act="inform", has_memory=True,
        has_activity=True, familiarity=1.0, pressure=0.8, turn=10,
        recent_history=(),
    ) is None
    assert select_behavioral_tendency(
        tendencies=(tendency,), input_act="inform", has_memory=True,
        has_activity=True, familiarity=1.0, pressure=0.2, turn=10,
        recent_history=((tendency.tendency_id, 9),),
    ) is None
    assert select_behavioral_tendency(
        tendencies=(tendency,), input_act="inform", has_memory=True,
        has_activity=True, familiarity=1.0, pressure=0.2, turn=12,
        recent_history=((tendency.tendency_id, 9),),
    ) == tendency


def test_tendency_parser_is_bounded_and_rejects_unknown_fields():
    valid = {
        "tendencies": [{
            "id": "probe", "trigger_acts": ["inform"],
            "preferred_move": "probe", "mystery": True,
        }]
    }
    try:
        parse_behavioral_tendencies(valid)
    except ValueError as exc:
        assert "unknown behavioral tendency field" in str(exc)
    else:
        raise AssertionError("unknown tendency fields must be rejected")

    too_many = {"tendencies": [
        {"id": f"probe_{index}", "trigger_acts": ["inform"], "preferred_move": "probe"}
        for index in range(13)
    ]}
    try:
        parse_behavioral_tendencies(too_many)
    except ValueError as exc:
        assert "at most 12" in str(exc)
    else:
        raise AssertionError("unbounded tendency banks must be rejected")


def test_same_observation_produces_character_specific_move_and_performance(tmp_path):
    pretorius = _agent(tmp_path, PRETORIUS, "pretorius")
    kiki = _agent(tmp_path, KIKI, "kiki")
    observation = "I built a mechanism that classifies interruptions."

    pretorius_result = pretorius.say(observation)
    kiki_result = kiki.say(observation)

    assert pretorius_result["conversation_candidate"]["move"] == "honor_obligation"
    assert kiki_result["conversation_candidate"]["move"] == "honor_obligation"
    assert pretorius_result["conversation_candidate"]["obligation"] == "acknowledge"
    assert kiki_result["conversation_candidate"]["obligation"] == "acknowledge"
    assert pretorius_result["conversation_candidate"]["extension_move"] == "probe"
    assert kiki_result["conversation_candidate"]["extension_move"] == "express_curiosity"
    assert pretorius_result["conversation_candidate"]["tendency_id"] == "precision_probe"
    assert kiki_result["conversation_candidate"]["tendency_id"] == "bright_curiosity"
    assert pretorius_result["performance_plan"]["social_stance"] != kiki_result["performance_plan"]["social_stance"]
    assert pretorius_result["response"] != kiki_result["response"]


def test_activity_callback_is_a_performance_fact_not_invented_prose(tmp_path):
    agent = _agent(tmp_path, PRETORIUS, "activity")
    activity_before = agent.engine.life_state.current_activity
    result = agent.say("I built a mechanism that classifies interruptions.")

    assert result["performance_plan"]["activity_transition"] == "continued"
    assert result["performance_plan"]["activity_label"] == activity_before
    assert "Observable activity transition: continued" in result["system_prompt"]
    assert any(
        act["channel"] == "activity" and act["target"] == activity_before
        for act in result["performance_plan"]["acts"]
    )


def test_continue_working_move_needs_real_activity():
    tendency = _tendency(
        tendency_id="continue", trigger_acts=("greeting",),
        preferred_move="continue_working", requires_activity=True,
    )
    candidate = derive_conversation_candidate(
        text="Hello.", actor_id=1, renderer_available=False, retrieved=(),
        direct_memory_cue=False, ready_open_loop=None, familiarity=0.8,
        turn=5, tendencies=(tendency,), current_activity="quiet observation",
    )
    assert candidate.move != "continue_working"


def test_cartridges_define_distinct_validated_behavior_banks():
    _, _, pretorius = load_cartridge(str(PRETORIUS))
    _, _, kiki = load_cartridge(str(KIKI))
    pretorius_moves = {
        item.preferred_move for item in parse_behavioral_tendencies(pretorius["behavioral_richness"])
    }
    kiki_moves = {
        item.preferred_move for item in parse_behavioral_tendencies(kiki["behavioral_richness"])
    }

    assert "probe" in pretorius_moves
    assert "express_curiosity" in kiki_moves
    assert len(pretorius["behavioral_richness"]["tendencies"]) <= 12
    assert len(kiki["behavioral_richness"]["tendencies"]) <= 12
