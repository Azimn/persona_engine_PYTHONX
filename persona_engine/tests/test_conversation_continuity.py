"""Per-actor dialogue blackboards shape turns without selecting final actions."""

from pathlib import Path

from persona_engine.agent import CharacterAgent
from persona_engine.core.conversation_continuity import (
    ConversationContinuityState,
    ConversationContinuityStore,
)
from persona_engine.core.offline_conversation import parse_behavioral_tendencies


ROOT = Path(__file__).resolve().parents[1]
PRETORIUS = ROOT / "cartridges" / "pretorius.snp"


def _agent(tmp_path, name="continuity"):
    return CharacterAgent(
        cartridge_path=str(PRETORIUS), user_id="continuity_user",
        db_path=str(tmp_path / f"{name}.db"),
    )


def test_blackboard_bounds_topics_and_tracks_depth_freshness_and_importance():
    state = ConversationContinuityState(actor_id=1)
    state.observe_input(
        text="I built an interruption mechanism.", input_act="inform",
        topic_id="interruption_mechanism", turn=1, emotional_importance=0.2,
    )
    state.observe_input(
        text="I tested the mechanism again.", input_act="inform",
        topic_id="tested_mechanism", turn=2, emotional_importance=0.7,
    )
    assert state.active_topic.depth == 2
    assert state.active_topic.emotional_importance == 0.7
    assert state.active_topic.freshness == 1.0

    for turn, text in enumerate(("A violin broke.", "The window opened.", "A letter arrived."), start=3):
        state.observe_input(
            text=text, input_act="inform", topic_id=f"topic_{turn}",
            turn=turn, emotional_importance=0.1,
        )
    assert len(state.background_topics) == 2
    assert state.last_transition_reason == "displaced"


def test_pronoun_followup_stays_on_active_topic():
    state = ConversationContinuityState(actor_id=1)
    state.observe_input(
        text="I built an interruption mechanism.", input_act="inform",
        topic_id="mechanism", turn=1, emotional_importance=0.1,
    )
    state.observe_input(
        text="What do you think it implies?", input_act="ask_opinion",
        topic_id="think_implies", turn=2, emotional_importance=0.1,
    )
    assert state.active_topic.topic_id == "mechanism"
    assert state.active_topic.depth == 2
    assert state.pending_obligation == "answer"


def test_transition_reasons_include_completed_exhausted_interrupted_avoided_and_displaced():
    completed = ConversationContinuityState(actor_id=1)
    completed.observe_input(text="A question", input_act="inform", topic_id="q", turn=1, emotional_importance=0)
    completed.observe_input(text="That settles it.", input_act="inform", topic_id="done", turn=2, emotional_importance=0)
    assert completed.last_transition_reason == "completed"
    assert completed.active_topic is None

    state = ConversationContinuityState(actor_id=2)
    state.observe_input(text="First matter", input_act="inform", topic_id="first", turn=1, emotional_importance=0)
    state.observe_input(text="Unrelated second matter", input_act="inform", topic_id="second", turn=2, emotional_importance=0)
    assert state.last_transition_reason == "displaced"
    for reason in ("exhausted", "interrupted", "avoided"):
        state.complete_turn(extension_move=None, action_kind="speak", transition_reason=reason)
        assert state.last_transition_reason == reason


def test_initiative_and_semantic_repetition_gate_optional_extensions():
    state = ConversationContinuityState(actor_id=1, initiative_budget=0.8)
    state.pending_obligation = "acknowledge"
    allowed, _ = state.extension_allowed("probe")
    assert allowed
    state.complete_turn(extension_move="probe", action_kind="speak")
    state.pending_obligation = "acknowledge"
    allowed, reason = state.extension_allowed("probe")
    assert not allowed
    assert reason == "extension:semantic_repeat"

    state.recent_move_signatures.clear()
    state.initiative_budget = 0.1
    allowed, reason = state.extension_allowed("speculate")
    assert not allowed
    assert reason == "extension:initiative_exhausted"


def test_store_is_actor_scoped_bounded_and_round_trips():
    store = ConversationContinuityStore()
    first = store.for_actor(11)
    second = store.for_actor(12)
    first.observe_input(text="First topic", input_act="inform", topic_id="first", turn=1, emotional_importance=0.2)
    second.observe_input(text="Second topic", input_act="inform", topic_id="second", turn=1, emotional_importance=0.2)

    restored = ConversationContinuityStore.from_list(store.to_list())
    assert restored.for_actor(11).active_topic.topic_id == "first"
    assert restored.for_actor(12).active_topic.topic_id == "second"


def test_engine_honors_obligation_before_one_optional_character_move(tmp_path):
    agent = _agent(tmp_path)
    result = agent.say("I built a mechanism that classifies interruptions.")
    candidate = result["conversation_candidate"]

    assert candidate["move"] == "honor_obligation"
    assert candidate["obligation"] == "acknowledge"
    assert candidate["extension_move"] == "probe"
    assert result["action_decision"]["communicative_function"] == "acknowledge"
    assert any(
        result["response"].startswith(prefix)
        for prefix in ("I heard you", "That point is registered", "Understood")
    )
    assert result["response"].count("?") <= 1


def test_plain_turn_without_extension_does_not_append_question(tmp_path):
    agent = _agent(tmp_path)
    agent.say("I built a mechanism that classifies interruptions.")
    result = agent.say("I adjusted the interruption mechanism.")

    assert result["conversation_candidate"]["obligation"] == "acknowledge"
    assert result["conversation_candidate"]["extension_move"] is None
    assert "?" not in result["response"]


def test_repeated_acknowledgment_shape_rotates_into_nonverbal_behavior(tmp_path):
    agent = _agent(tmp_path, "shape_rotation")
    turns = [
        agent.say("I built a mechanism that classifies interruptions."),
        agent.say("I adjusted the interruption mechanism."),
        agent.say("I tested the interruption mechanism again."),
        agent.say("The interruption mechanism remained stable."),
    ]
    kinds = [item["action_decision"]["action_kind"] for item in turns]
    assert "speak" in kinds
    assert any(kind in {"gesture", "continue_activity", "silence"} for kind in kinds)
    assert any(
        code.startswith("shape:semantic_repeat:")
        for item in turns for code in item["conversation_candidate"]["reason_codes"]
    )


def test_topic_depth_and_actor_state_persist_without_cross_actor_bleed(tmp_path):
    agent = _agent(tmp_path, "actors")
    agent.say(
        "I built an interruption mechanism.",
        visible_context={"speaker_id": "jay", "speaker_name": "Jay"},
    )
    jay_id = agent.engine.active_actor_id
    agent.say(
        "What do you think it implies?",
        visible_context={"speaker_id": "jay", "speaker_name": "Jay"},
    )
    assert agent.engine.conversation_continuity.for_actor(jay_id).active_topic.depth == 2

    agent.say(
        "I brought a completely different puzzle.",
        visible_context={"speaker_id": "kiki", "speaker_name": "Kiki"},
    )
    kiki_id = agent.engine.active_actor_id
    assert kiki_id != jay_id
    assert agent.engine.conversation_continuity.for_actor(kiki_id).active_topic.depth == 1

    restarted = _agent(tmp_path, "actors")
    assert restarted.engine.conversation_continuity.for_actor(jay_id).active_topic.depth == 2
    assert restarted.engine.conversation_continuity.for_actor(kiki_id).active_topic.depth == 1


def test_memory_context_score_prefers_active_topic_over_unrelated_memory():
    state = ConversationContinuityState(actor_id=1)
    state.observe_input(
        text="The interruption mechanism needs a better trigger.", input_act="inform",
        topic_id="interruption_trigger", turn=1, emotional_importance=0.2,
    )
    related = state.memory_context_score("I repaired the mechanism after an interruption.")
    unrelated = state.memory_context_score("I watched rain collect beside the window.")
    assert related > unrelated
    assert unrelated == 0.0


def test_challenge_and_reminiscence_are_bounded_authorable_extensions():
    tendencies = parse_behavioral_tendencies({"tendencies": [
        {
            "id": "challenge_claim", "trigger_acts": ["challenge"],
            "preferred_move": "challenge", "requires_memory": False,
        },
        {
            "id": "recall_precedent", "trigger_acts": ["ask_opinion"],
            "preferred_move": "reminisce", "requires_memory": True,
        },
    ]})
    assert {item.preferred_move for item in tendencies} == {"challenge", "reminisce"}
