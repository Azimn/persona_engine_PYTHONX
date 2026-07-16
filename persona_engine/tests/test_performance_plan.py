"""Behavior selection remains separate from outward performance."""

from pathlib import Path

from persona_engine.agent import CharacterAgent
from persona_engine.core.expression import build_performance_plan
from persona_engine.core.renderer import LocalLLMRenderer


ROOT = Path(__file__).resolve().parents[1]
CARTRIDGES = ROOT / "cartridges"


def test_performance_plan_is_deterministic_and_does_not_reselect_action():
    action = {
        "decision_id": "decision-1",
        "action_type": "gesture",
        "visibility": "observable",
        "interruptible": True,
    }
    first = build_performance_plan({"dialogue_act": "respond"}, None, action)
    second = build_performance_plan({"dialogue_act": "respond"}, None, action)

    assert first == second
    assert first.action_type == "gesture"
    assert first.utterance_required is False
    assert first.source_decision_id == "decision-1"


def test_identity_resistance_keeps_speech_guard_at_nonverbal_action():
    plan = build_performance_plan(
        {"dialogue_act": "protect_boundary"},
        "character_refusal",
        {"decision_id": "decision-2", "action_type": "gesture", "interruptible": True},
    )

    assert plan.action_type == "speak"
    assert plan.utterance_required is True
    assert plan.voice_directive == "character_refusal"


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
    assert result["performance_plan"]["action_type"] == "silence"
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
