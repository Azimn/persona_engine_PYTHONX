"""Conversation choreography varies interaction without becoming an executive."""

from pathlib import Path
from types import SimpleNamespace

from persona_engine.agent import CharacterAgent
from persona_engine.core.action import ActionDecision
from persona_engine.core.conversation_choreography import ConversationChoreographyPlanner
from persona_engine.core.conversation_continuity import ConversationContinuityState
from persona_engine.core.offline_conversation import ConversationCandidate
from persona_engine.core.performance import PerformancePlanner
from persona_engine.core.offline_template_renderer import OfflineTemplateRenderer
from persona_engine.core.relationship import RelationshipState
from persona_engine.core.emotion import PressureSystem


ROOT = Path(__file__).resolve().parents[1]
PRETORIUS = ROOT / "cartridges" / "pretorius.snp"


def _decision(kind="speak", function="answer"):
    return ActionDecision(
        schema_version=2, decision_id=f"decision-{kind}", tick=3, source="test",
        intention_id="preserve_thread", action_kind=kind, target="interlocutor",
        communicative_function=function, expected_effect="honor the selected move",
        selected_habit_id=None, synthesis_id="synthesis-test", confidence=0.72,
        interruptible=True, visibility="observable", reason_codes=("test",),
    )


def _candidate(obligation="answer", extension=None, memory_id=None):
    return ConversationCandidate(
        schema_version=1, candidate_id="conversation-test", input_act="ask_fact",
        move="honor_obligation", strength=0.8, response_value=0.8,
        topic_key="apparatus", source_memory_id=memory_id, source_open_loop_key=None,
        required_capability="none", reason_codes=("test",), obligation=obligation,
        extension_move=extension,
    )


def _continuity():
    state = ConversationContinuityState(actor_id=7, initiative_budget=0.72)
    state.observe_input(
        text="What does the apparatus prove?", input_act="ask_fact",
        topic_id="apparatus", turn=3, emotional_importance=0.45,
    )
    return state


def _plan(*, state=None, candidate=None, decision=None, seed=19, energy=.7, fatigue=.1):
    return ConversationChoreographyPlanner().plan(
        decision=decision or _decision(), candidate=candidate or _candidate(),
        continuity=state or _continuity(),
        body=SimpleNamespace(energy=energy, fatigue=fatigue),
        relationship=SimpleNamespace(familiarity=.5), dominant_pressure=.2,
        self_monitor=SimpleNamespace(perceived_confidence=.7),
        activity_transition="paused", stable_seed=seed,
    )


def test_choreography_is_deterministic_bounded_and_replay_authoritative():
    first = _plan()
    second = _plan()

    assert first == second
    assert 0.0 <= first.conversational_energy <= 1.0
    assert first.decision_id == "decision-speak"
    assert first.to_dict()["record_authority"] == "deterministic_conversation_realization_record"
    assert first.to_dict()["replay_authoritative"] is True


def test_selected_extension_is_preserved_and_never_invented():
    no_extension = _plan(candidate=_candidate(extension=None))
    compare = _plan(candidate=_candidate(extension="compare", memory_id="memory-1"))

    assert no_extension.selected_extension is None
    assert compare.selected_extension == "compare"
    assert compare.rhetorical_strategy == "compare"
    assert compare.memory_role == "analogy"

    working = _plan(candidate=_candidate(extension="continue_working"))
    assert working.selected_extension == "continue_working"
    assert working.rhetorical_strategy == "return_to_work"


def test_recent_trajectory_changes_shape_without_changing_action():
    state = _continuity()
    first = _plan(state=state)
    state.record_trajectory(first.trajectory_signature)
    second = _plan(state=state)

    assert first.trajectory_signature != second.trajectory_signature
    assert first.decision_id == second.decision_id == "decision-speak"


def test_organism_state_changes_conversational_energy_and_span():
    low = _plan(energy=.15, fatigue=.9)
    high = _plan(energy=.95, fatigue=.0)

    assert low.conversational_energy < high.conversational_energy
    assert low.energy_band == "low"
    assert high.energy_band in {"medium", "high"}
    assert low.response_span != "extended"


def test_choreography_cannot_turn_nonverbal_action_into_speech():
    decision = _decision("silence", "withhold_response")
    choreography = _plan(decision=decision)
    performance = PerformancePlanner().plan(
        decision=decision, relationship=RelationshipState("tester"),
        pressures=PressureSystem(), capacity=.6,
        conversation_choreography=choreography,
    )

    assert choreography.rhetorical_strategy == "withhold"
    assert performance.requires_language_renderer is False
    assert all(item.channel != "speech" for item in performance.acts)
    assert performance.conversation_choreography_id == choreography.choreography_id


def test_engine_persists_actor_trajectory_and_links_performance(tmp_path):
    db = tmp_path / "plasticity.db"
    agent = CharacterAgent(
        cartridge_path=str(PRETORIUS), user_id="plasticity-user", db_path=str(db),
    )
    result = agent.say("What does the interruption mechanism prove?")
    choreography = result["conversation_choreography"]

    assert choreography["decision_id"] == result["action_decision"]["decision_id"]
    assert result["performance_plan"]["conversation_choreography_id"] == choreography["choreography_id"]
    assert result["conversation_continuity"]["recent_trajectory_signatures"][-1] == choreography["trajectory_signature"]
    assert "CONVERSATION CHOREOGRAPHY" in result["system_prompt"]

    restarted = CharacterAgent(
        cartridge_path=str(PRETORIUS), user_id="plasticity-user", db_path=str(db),
    )
    assert (
        restarted.engine._last_conversation_choreography.choreography_id
        == choreography["choreography_id"]
    )


def test_offline_choreography_uses_orthogonal_structure_not_more_response_banks():
    renderer = OfflineTemplateRenderer()
    qualified = renderer._apply_choreography(
        "I can answer the established part.",
        {"rhetorical_strategy": "qualify", "response_span": "normal",
         "answer_shape": "qualified", "pacing": "measured"},
        has_extension=False,
        realization={"choreography_qualify": ("Precisely framed: {content}",)},
    )
    reflected = renderer._apply_choreography(
        "That point is registered.",
        {"rhetorical_strategy": "reflect", "response_span": "normal",
         "answer_shape": "direct", "pacing": "measured"},
        has_extension=False,
        realization={"choreography_reflect": ("The retained implication: {content}",)},
    )

    assert qualified == "Precisely framed: I can answer the established part."
    assert reflected == "The retained implication: That point is registered."
