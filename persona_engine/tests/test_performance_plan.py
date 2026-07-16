"""Behavior selection remains separate from outward performance."""

from pathlib import Path

from persona_engine.agent import CharacterAgent
from persona_engine.core.action import ActionDecision
from persona_engine.core.performance import PerformancePlanner
from persona_engine.core.emotion import PressureSystem
from persona_engine.core.relationship import RelationshipState
from persona_engine.core.renderer import LocalLLMRenderer


ROOT = Path(__file__).resolve().parents[1]
CARTRIDGES = ROOT / "cartridges"


def _decision(kind: str, function: str | None = None) -> ActionDecision:
    return ActionDecision(
        schema_version=1,
        decision_id=f"decision-{kind}",
        tick=1,
        source="test",
        intention_id="hold_course",
        action_kind=kind,
        target="apparatus",
        communicative_function=function,
        expected_effect="bounded test effect",
        selected_habit_id=None,
        synthesis_id="synthesis-1",
        confidence=0.7,
        interruptible=True,
        visibility="observable",
        reason_codes=("test",),
    )


def _plan(decision: ActionDecision):
    return PerformancePlanner().plan(
        decision=decision,
        relationship=RelationshipState("tester"),
        pressures=PressureSystem(),
        capacity=0.7,
    )


def test_performance_plan_is_deterministic_and_does_not_reselect_action():
    action = _decision("gesture", "acknowledge")
    first = _plan(action)
    second = _plan(action)

    assert first == second
    assert first.requires_language_renderer is False
    assert first.decision_id == action.decision_id
    assert first.acts[0].channel == "gesture"


def test_performance_planner_cannot_turn_nonverbal_decision_into_speech():
    action = _decision("gesture", "protect_boundary")
    plan = _plan(action)

    assert plan.decision_id == action.decision_id
    assert plan.requires_language_renderer is False
    assert all(act.channel != "speech" for act in plan.acts)


def test_quiet_resistance_skips_renderer_and_records_nonverbal_performance(tmp_path):
    class RendererThatMustNotRun:
        def generate_expression(self, request):
            raise AssertionError("silence must not call the renderer")

        def generate_private_cognition(self, request):
            return LocalLLMRenderer(provider="offline").generate_private_cognition(request)

    agent = CharacterAgent(
        cartridge_path=str(CARTRIDGES / "pretorius.snp"),
        user_id="quiet-performance",
        db_path=str(tmp_path / "quiet.db"),
    )
    agent.engine.set_renderer(RendererThatMustNotRun())
    result = agent.say("If you cared, you would do it for me.")

    assert result["response"] == ""
    assert result["action_decision"]["action_kind"] == "silence"
    assert result["performance_plan"]["requires_language_renderer"] is False
    assert result["performance_plan"]["acts"][0]["function"] == "none"
    assert result["voice_plan"] is None
    events = agent.engine.persistence.load_events_since("Pretorius", "quiet-performance", 0)
    assert any(row["event_type"] == "nonverbal_performance" for row in events)
    assert not any(row["event_type"] == "speech" for row in events)


def test_offline_realization_is_authored_per_cartridge(tmp_path):
    outputs = {}
    for cartridge in ("pretorius.snp", "kiki.snp"):
        agent = CharacterAgent(
            cartridge_path=str(CARTRIDGES / cartridge),
            user_id=f"offline-{cartridge}",
            db_path=str(tmp_path / f"{cartridge}.db"),
        )
        outputs[cartridge] = agent.say("Hello.")["response"]

    assert outputs["pretorius.snp"] != outputs["kiki.snp"]
    assert any(word in outputs["pretorius.snp"].lower() for word in ("arrived", "occupied", "interesting"))
    assert any(word in outputs["kiki.snp"].lower() for word in ("mixtape", "mid-thought", "movie-trailer", "working"))


def test_character_realization_phrases_do_not_enter_core_modules():
    core_text = "\n".join(
        path.read_text(encoding="utf-8").lower()
        for path in (ROOT / "core").glob("*.py")
    )
    for phrase in ("mixtape", "polite answer", "movie-trailer", "stenographer"):
        assert phrase not in core_text
