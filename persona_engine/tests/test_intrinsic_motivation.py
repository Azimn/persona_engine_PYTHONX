"""Intrinsic motivation remains generic while cartridges author lived priorities."""

from pathlib import Path

import pytest

from persona_engine.agent import CharacterAgent
from persona_engine.core.cartridge import CartridgeError, load_cartridge
from persona_engine.core.intrinsic import IntrinsicMotivationEngine, IntrinsicState


ROOT = Path(__file__).resolve().parents[1]
CARTRIDGES = ROOT / "cartridges"


def _agent(tmp_path, cartridge: str, user: str = "tester") -> CharacterAgent:
    return CharacterAgent(
        cartridge_path=str(CARTRIDGES / cartridge),
        user_id=user,
        db_path=str(tmp_path / f"{cartridge}-{user}.db"),
    )


def test_pretorius_and_kiki_author_distinct_intrinsic_profiles():
    _p_core, _p_ledger, pretorius = load_cartridge(str(CARTRIDGES / "pretorius.snp"))
    _k_core, _k_ledger, kiki = load_cartridge(str(CARTRIDGES / "kiki.snp"))

    assert {item["id"] for item in pretorius["intrinsic"]["wants"]} == {
        "advance_the_work", "be_witnessed", "preserve_autonomy",
    }
    assert {item["id"] for item in kiki["intrinsic"]["wants"]} == {
        "make_the_cosmos_close", "be_taken_seriously", "keep_things_warm",
    }


def test_intrinsic_selection_is_deterministic_and_structured():
    _core, _ledger, raw = load_cartridge(str(CARTRIDGES / "pretorius.snp"))
    selector = IntrinsicMotivationEngine.from_cartridge(raw["intrinsic"])
    first = selector.select(
        IntrinsicState(), companion_id="subject", tick=8, energy=0.72,
        restlessness=0.2, pressures={}, force=True,
    )
    second = selector.select(
        IntrinsicState(), companion_id="subject", tick=8, energy=0.72,
        restlessness=0.2, pressures={}, force=True,
    )

    assert first == second
    assert first is not None
    assert first.proposed_action_kind in {
        "speak", "gesture", "continue_activity", "observe", "silence", "world_action",
    }
    assert first.score_breakdown
    assert first.selection_reason


def test_intrinsic_proposal_does_not_prematurely_change_life_state(tmp_path):
    agent = _agent(tmp_path, "pretorius.snp")
    before = agent.engine.life_state.to_dict()
    proposal = agent.engine.select_intrinsic_action()

    assert proposal is not None
    assert agent.engine.life_state.to_dict() == before
    assert any(item.source.startswith("intrinsic:") for item in agent.engine.intentions.intentions)

    decision = agent.engine.resolve_intrinsic_proposal()
    assert decision["source"] == f"intrinsic:{proposal['proposal_id']}"
    assert agent.engine.life_state.current_activity == proposal["activity_description"]
    assert agent.engine.life_state.current_intention == proposal["intention"]


def test_neglected_wants_gain_priority_without_unbounded_growth():
    _core, _ledger, raw = load_cartridge(str(CARTRIDGES / "kiki.snp"))
    selector = IntrinsicMotivationEngine.from_cartridge(raw["intrinsic"])
    state = IntrinsicState()

    selected = []
    for tick in range(30):
        decision = selector.select(
            state, companion_id="subject", tick=tick, energy=0.8,
            restlessness=0.3, pressures={}, force=True,
        )
        selected.append(decision.want_id)

    assert len(set(selected)) > 1
    assert all(0.0 <= value <= 1.0 for value in state.want_levels.values())


def test_intrinsic_state_persists_per_character_session(tmp_path):
    db = tmp_path / "state.db"
    first = CharacterAgent(
        cartridge_path=str(CARTRIDGES / "kiki.snp"), user_id="same-user", db_path=str(db),
    )
    proposal = first.engine.select_intrinsic_action()
    decision = first.engine.resolve_intrinsic_proposal()
    restarted = CharacterAgent(
        cartridge_path=str(CARTRIDGES / "kiki.snp"), user_id="same-user", db_path=str(db),
    )

    assert restarted.engine.intrinsic_state.to_dict() == first.engine.intrinsic_state.to_dict()
    assert restarted.engine._last_intrinsic_proposal.to_dict() == proposal
    assert restarted.engine._last_action_decision.to_dict() == decision
    assert restarted.engine._last_performance_plan.decision_id == decision["decision_id"]


def test_completed_intrinsic_action_uses_objective_and_first_person_memory_channels(tmp_path):
    agent = _agent(tmp_path, "pretorius.snp", "completion")
    proposal = agent.engine.select_intrinsic_action()
    decision = agent.engine.resolve_intrinsic_proposal()
    before_level = agent.engine.intrinsic_state.want_levels[proposal["want_id"]]
    result = agent.engine.complete_intrinsic_action(
        observed_outcome="the apparatus remained unstable",
        objective_cause="a loose connection interrupted the circuit",
        expected_outcome="the apparatus stabilized",
        force_execution_failure=True,
        force_wrong_learning=True,
        now=100.0,
    )

    completion = result["completion"]
    assert completion["intention_id"] == decision["intention_id"]
    assert agent.engine.world_events.fetch(completion["world_event_id"]) is not None
    assert completion["subjective_interpretation_reference"]
    assert all(memory.content.startswith("I ") for memory in agent.engine.memory.memories)
    assert f"intrinsic:{proposal['activity_id']}" in agent.engine.habits.habits
    assert agent.engine.intrinsic_state.want_levels[proposal["want_id"]] <= before_level


def test_intrinsic_schema_rejects_unknown_action_type(tmp_path):
    text = (CARTRIDGES / "pretorius.snp").read_text(encoding="utf-8")
    bad = tmp_path / "bad.snp"
    bad.write_text(text.replace('action_type = "continue_activity"', 'action_type = "become_world_authority"', 1), encoding="utf-8")

    with pytest.raises(CartridgeError, match="unsupported intrinsic action_type"):
        load_cartridge(str(bad))


def test_intrinsic_schema_rejects_nonfinite_utility(tmp_path):
    text = (CARTRIDGES / "pretorius.snp").read_text(encoding="utf-8")
    bad = tmp_path / "bad-numeric.snp"
    bad.write_text(text.replace("base_utility = 0.28", "base_utility = nan", 1), encoding="utf-8")

    with pytest.raises(CartridgeError, match="base_utility"):
        load_cartridge(str(bad))


def test_intrinsic_schema_rejects_unknown_performance_tendency(tmp_path):
    text = (CARTRIDGES / "pretorius.snp").read_text(encoding="utf-8")
    bad = tmp_path / "bad-tendency.snp"
    bad.write_text(
        text.replace('performance_tendency_id = "guard_exacting_work"', 'performance_tendency_id = "missing_tendency"', 1),
        encoding="utf-8",
    )

    with pytest.raises(CartridgeError, match="unknown performance tendency"):
        load_cartridge(str(bad))


def test_intrinsic_core_contains_no_character_literals():
    source = (ROOT / "core" / "intrinsic.py").read_text(encoding="utf-8").lower()
    for literal in ("pretorius", "kiki", "henry", "jay"):
        assert literal not in source


def test_kiki_period_constraint_and_pretorius_resistance_reach_renderer_prompt(tmp_path):
    class CaptureRenderer:
        def __init__(self):
            self.request = None

        def generate_expression(self, request):
            self.request = request
            return "Noted."

    kiki = _agent(tmp_path, "kiki.snp", "voice-k")
    pretorius = _agent(tmp_path, "pretorius.snp", "voice-p")
    kiki_renderer = CaptureRenderer()
    pretorius_renderer = CaptureRenderer()
    kiki.engine.set_renderer(kiki_renderer)
    pretorius.engine.set_renderer(pretorius_renderer)

    kiki.say("Explain that idea.")
    pretorius.say("Explain that idea.")

    assert "pre-2000" in kiki_renderer.request.resolved_state["system_prompt"]
    assert "helpful-assistant reassurance" in pretorius_renderer.request.resolved_state["system_prompt"]
