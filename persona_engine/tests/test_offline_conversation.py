"""Portable conversation uses memory, notes, and nonverbal acknowledgement."""

from pathlib import Path

from persona_engine.agent import CharacterAgent
from persona_engine.core.offline_conversation import classify_input
from persona_engine.core.renderer import LocalLLMRenderer


ROOT = Path(__file__).resolve().parents[1]
PRETORIUS = ROOT / "cartridges" / "pretorius.snp"
END_TIME = 1_800_000_000.0


def _agent(tmp_path, name="offline"):
    return CharacterAgent(
        cartridge_path=str(PRETORIUS), user_id="offline_user",
        db_path=str(tmp_path / f"{name}.db"),
    )


def test_bounded_input_acts_cover_conversational_jobs():
    assert classify_input("Hello.") == "greeting"
    assert classify_input("What do you remember about Henry?") == "ask_memory"
    assert classify_input("Why analyze the philosophical implications?") == "ask_analysis"
    assert classify_input("I am sorry.") == "apologize"
    assert classify_input("...") == "low_information"


def test_offline_unknown_analysis_is_noted_without_inventing_an_answer(tmp_path):
    agent = _agent(tmp_path)
    result = agent.say("Why should tensor categories change quantum gravity?")
    notes = [item for item in agent.engine.intentions.open_loops if item.reason == "offline_knowledge_unavailable"]

    assert result["conversation_candidate"]["move"] == "defer_and_note"
    assert result["action_decision"]["communicative_function"] == "defer_and_note"
    assert len(notes) == 1
    assert notes[0].required_capability == "language_model"
    assert notes[0].status == "pending"
    assert "quantum gravity" in notes[0].topic.lower()
    assert "pending notes" in result["response"].lower() or "marked" in result["response"].lower()


def test_offline_reminiscence_uses_a_considered_autobiographical_memory(tmp_path):
    agent = _agent(tmp_path)
    agent.replay_genesis(end_time=END_TIME)
    result = agent.say("What do you remember about Henry Frankenstein?", event_time=END_TIME + 1)
    source_id = result["conversation_candidate"]["source_memory_id"]
    considered = {
        item["influence_id"] for item in result["synthesis"]["considered_influences"]
    }

    assert result["conversation_candidate"]["move"] == "reminisce"
    assert result["action_decision"]["communicative_function"] == "reminisce"
    assert source_id is not None
    assert f"memory:{source_id}" in considered
    assert "remember" in result["response"].lower()
    assert "henry" in result["response"].lower()


def test_memory_can_support_reminiscence_without_pretending_to_support_analysis(tmp_path):
    agent = _agent(tmp_path)
    agent.replay_genesis(end_time=END_TIME)
    result = agent.say(
        "Why should recursive self-modeling change the philosophy of digital consciousness?",
        event_time=END_TIME + 1,
    )

    assert result["conversation_candidate"]["move"] == "reminisce_and_note"
    assert result["action_decision"]["communicative_function"] == "reminisce_and_note"
    assert "remember" in result["response"].lower()
    assert "larger question" in result["response"].lower()
    assert any(item.required_capability == "language_model" for item in agent.engine.intentions.open_loops)


def test_low_information_can_acknowledge_without_speech_or_model_call(tmp_path):
    agent = _agent(tmp_path)
    result = agent.say("...")

    assert result["conversation_candidate"]["move"] == "acknowledge_nonverbal"
    assert result["action_decision"]["action_kind"] in {"gesture", "continue_activity"}
    assert result["response"] == ""
    assert result["model_calls"]["total_model_calls"] == 0


def test_repeated_statement_can_be_acknowledged_without_repeating_speech(tmp_path):
    agent = _agent(tmp_path)
    text = "I heard the boundary. Let me ask more carefully."
    first = agent.say(text)
    second = agent.say(text)
    third = agent.say(text)

    assert first["response"]
    assert second["conversation_candidate"]["move"] == "acknowledge_nonverbal"
    assert second["response"] == ""
    assert second["action_decision"]["action_kind"] == "gesture"
    assert third["action_decision"]["action_kind"] == "continue_activity"


def test_lexical_overlap_does_not_turn_ordinary_dialogue_into_recursive_memory():
    renderer = LocalLLMRenderer(provider="offline")._offline
    messages = [
        {"role": "system", "content": "Relevant memories, use only as background and do not recite verbatim: I heard you say: continue carefully."},
        {"role": "user", "content": "Continue carefully."},
    ]
    response = renderer.render(messages, seed=3)

    assert "I remember that I heard you say" not in response


def test_vague_thread_request_asks_for_a_grounded_cue_instead_of_echoing_dialogue(tmp_path):
    agent = _agent(tmp_path)
    result = agent.say("Where did we leave the unfinished part?")

    assert result["conversation_candidate"]["move"] == "ask_clarification"
    assert result["action_decision"]["communicative_function"] == "ask_clarification"
    assert "I remember that I heard you say" not in result["response"]


def test_note_and_shuffle_history_survive_reload(tmp_path):
    agent = _agent(tmp_path)
    agent.say("Why analyze the metaphysics of an unknown causal lattice?")
    agent.say("Hello.")
    before = agent.debug_snapshot()["life_inspector"]["offline_realization_state"]

    restarted = _agent(tmp_path)
    after = restarted.debug_snapshot()["life_inspector"]["offline_realization_state"]

    assert any(item.required_capability == "language_model" for item in restarted.engine.intentions.open_loops)
    assert after == before
    assert len(after["recent_global"]) <= 24


def test_model_reconnection_surfaces_note_without_resolving_it(tmp_path):
    agent = _agent(tmp_path)
    agent.say("Why analyze the metaphysics of an unknown causal lattice?")
    note = next(item for item in agent.engine.intentions.open_loops if item.required_capability == "language_model")
    note.created_at -= 120
    note.last_touched -= 120

    def unavailable(*args, **kwargs):
        raise OSError("test model unavailable")

    agent.engine.set_renderer(LocalLLMRenderer(model_name="fake", provider="ollama", opener=unavailable))
    results = []
    for _ in range(4):
        result = agent.say("Was there something you wanted to return to?")
        results.append(result)
        if result["action_decision"]["communicative_function"] == "return_to_topic":
            break
        note.last_touched -= 120

    assert any(item["conversation_candidate"]["move"] == "return_to_topic" for item in results)
    assert result["action_decision"]["communicative_function"] == "return_to_topic"
    assert note.status == "surfaced"
    assert note in agent.engine.intentions.open_loops
    assert any(word in result["response"].lower() for word in ("unfinished", "note", "survived"))


def test_conversation_notes_are_private_inspectable_state(tmp_path):
    agent = _agent(tmp_path)
    agent.say("Why analyze the metaphysics of an unknown causal lattice?")

    assert "conversation_notes" not in agent.public_status()
    inspector = agent.debug_snapshot()["life_inspector"]
    assert inspector["conversation_notes"]
    assert inspector["conversation_candidate"]["move"] == "defer_and_note"


def test_pending_topics_do_not_cross_actor_boundaries(tmp_path):
    agent = _agent(tmp_path)
    agent.say(
        "Why analyze the metaphysics of an unknown causal lattice?",
        visible_context={"speaker_id": "jay", "speaker_name": "Jay"},
    )
    note = next(item for item in agent.engine.intentions.open_loops if item.required_capability == "language_model")
    note.created_at -= 120
    note.last_touched -= 120
    note.status = "ready"

    result = agent.say(
        "Was there something you wanted to return to?",
        visible_context={"speaker_id": "kiki", "speaker_name": "Kiki"},
    )

    assert result["conversation_candidate"]["move"] != "return_to_topic"
    assert note.status == "ready"
