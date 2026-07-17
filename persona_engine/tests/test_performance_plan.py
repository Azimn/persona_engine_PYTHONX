"""Behavior selection remains separate from outward performance."""

from pathlib import Path

from persona_engine.agent import CharacterAgent
from persona_engine.core.action import ActionDecision
from persona_engine.core.avatar import AvatarProjector
from persona_engine.core.cartridge import load_cartridge
from persona_engine.core.performance import PerformancePlanner, PerformanceProfile
from persona_engine.core.emotion import PressureSystem
from persona_engine.core.relationship import RelationshipState
from persona_engine.core.renderer import LocalLLMRenderer
from persona_engine.core.voice import VoicePlanner


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


def _plan(decision: ActionDecision, profile: PerformanceProfile | None = None):
    return PerformancePlanner().plan(
        decision=decision,
        relationship=RelationshipState("tester"),
        pressures=PressureSystem(),
        capacity=0.7,
        performance_profile=profile,
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


def test_speech_coordinates_language_voice_and_avatar_channels():
    plan = _plan(_decision("speak", "challenge"))
    channels = {act.channel for act in plan.acts}

    assert {"speech", "voice", "gaze", "face", "timing"}.issubset(channels)
    assert plan.requires_language_renderer is True


def test_silence_coordinates_gaze_face_and_continued_activity_without_speech():
    plan = _plan(_decision("silence", "withhold_response"))
    channels = {act.channel for act in plan.acts}

    assert "speech" not in channels
    assert {"activity", "gaze", "face", "timing"}.issubset(channels)
    assert plan.requires_language_renderer is False


def test_cartridge_tendencies_change_channels_without_changing_action():
    _pcore, _pledger, pretorius = load_cartridge(str(CARTRIDGES / "pretorius.snp"))
    _kcore, _kledger, kiki = load_cartridge(str(CARTRIDGES / "kiki.snp"))
    action = _decision("speak", "respond")
    guarded = PerformanceProfile.from_cartridge_tendency(
        pretorius["performance_tendencies"], "guard_exacting_work",
    )
    bright = PerformanceProfile.from_cartridge_tendency(
        kiki["performance_tendencies"], "bright_scientific_precision",
    )

    guarded_plan = _plan(action, guarded)
    bright_plan = _plan(action, bright)
    assert guarded_plan.decision_id == bright_plan.decision_id == action.decision_id
    assert guarded_plan.social_stance != bright_plan.social_stance
    assert guarded_plan.directness != bright_plan.directness
    assert [(act.channel, act.function) for act in guarded_plan.acts] != [
        (act.channel, act.function) for act in bright_plan.acts
    ]

    voice = VoicePlanner().plan("hello", bright_plan)
    avatar = AvatarProjector().project({
        "avatar_state": "neutral", "attention": "user", "movement_need": "low",
        "posture": "settled",
    }, bright_plan)
    assert voice.rate_bucket == "fluid"
    assert avatar.face_state == "expressive"
    assert avatar.gaze_state == "alternating"
    assert avatar.motion_state == "gesture_animated"


def test_performance_plan_preserves_action_fields_and_cannot_leak_withheld_fact():
    action = _decision("speak", "protect_boundary")
    plan = PerformancePlanner().plan(
        decision=action,
        relationship=RelationshipState("tester"),
        pressures=PressureSystem(),
        capacity=0.5,
        concealment_mode="selective_truth",
    )

    assert plan.decision_id == action.decision_id
    assert plan.turn_intention == action.intention_id
    assert all(act.target == action.target for act in plan.acts)
    assert all(act.leakage_source_id is None for act in plan.acts)
    assert all("unselected_private_state" not in act.function for act in plan.acts)


def test_quiet_resistance_skips_expression_renderer_and_records_nonverbal_performance(tmp_path):
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
    assert all(act["channel"] != "speech" for act in result["performance_plan"]["acts"])
    assert any(act["channel"] == "activity" for act in result["performance_plan"]["acts"])
    assert result["model_calls"]["total_model_calls"] == 0
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
