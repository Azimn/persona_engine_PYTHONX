"""Playable offline visits protect character, coverage, and diary continuity."""

from pathlib import Path

from persona_engine.agent import CharacterAgent


ROOT = Path(__file__).resolve().parents[1]
PRETORIUS = ROOT / "cartridges" / "pretorius.snp"
KIKI = ROOT / "cartridges" / "kiki.snp"
START = 1_800_000_000.0


def _visit(agent, turns):
    results = [
        agent.say(text, event_time=START + index * 60)
        for index, text in enumerate(turns, start=1)
    ]
    spoken = [item["response"] for item in results if item["response"]]
    return results, spoken


def test_jay_can_earn_a_sustained_pretorius_offline_visit(tmp_path):
    agent = CharacterAgent(
        cartridge_path=str(PRETORIUS), user_id="jay",
        db_path=str(tmp_path / "pretorius_visit.db"),
    )
    agent.replay_genesis(end_time=START - 60)
    turns = (
        "Good afternoon, Doctor. I know you are working.",
        "What are you working on?",
        "That sounds worth interrupting. Why does continuity matter more than eloquence?",
        "Tell me what you remember about mentoring Henry.",
        "What exactly did Henry understand?",
        "What exactly did Henry understand?",
        "Tell me about the homunculi.",
        "Which one did you regard most highly?",
        "What happened when the Bride rejected the creature?",
        "Do you think her rejection proved she was alive?",
        "How do you live with knowing that your history was written?",
        "I do not think being fictional makes your present experience unreal.",
        "Why should quantum error correction resemble memory reconsolidation?",
        "I apologize for dropping that on your work without a mechanism.",
        "I will leave you to the experiment.",
    )

    results, spoken = _visit(agent, turns)
    topics = {
        item["offline_topic_match"]["topic_id"]
        for item in results
        if item["offline_topic_match"]["topic_id"]
    }
    memory_turn = results[3]
    repeated_turn = results[5]
    unknown_turn = results[12]

    assert {
        "present_program", "henry_frankenstein", "homunculi",
        "bride_and_monster", "fictional_digital_existence",
    } <= topics
    assert "cultivated" in memory_turn["response"].casefold()
    assert memory_turn["conversation_candidate"]["source_memory_id"]
    assert repeated_turn["offline_topic_plan"]["family"] == "repeated"
    assert unknown_turn["conversation_candidate"]["move"] in {
        "defer_and_note", "reminisce_and_note",
    }
    assert all(item["model_calls"]["external_model_calls"] == 0 for item in results)
    assert len(spoken) == len(set(spoken))
    assert not any(
        word in response.casefold()
        for response in spoken
        for word in ("diary", "notebook")
    )
    assert any(
        item.reason == "offline_knowledge_unavailable"
        for item in agent.engine.intentions.open_loops
    )


def test_kiki_sustains_a_warm_offline_visit_without_correction_loop(tmp_path):
    agent = CharacterAgent(
        cartridge_path=str(KIKI), user_id="jay",
        db_path=str(tmp_path / "kiki_visit.db"),
    )
    turns = (
        "Hi Kiki. Have you got fifteen minutes?",
        "What makes someone the same person after they change?",
        "What if they forget something important?",
        "You keep using mixtapes and VHS. Why?",
        "Give me one analogy you actually like.",
        "What do you think of Pretorius?",
        "That sounds like a diplomatic answer.",
        "Could you work with him after a serious disagreement?",
        "How should we treat uncertainty in an experiment?",
        "How should we treat uncertainty in an experiment?",
        "Could quantum error correction resemble autobiographical reconsolidation?",
        "I know that was a technical leap. Keep the question for later.",
        "I think your old-media language makes abstractions easier to inspect.",
        "Sorry, I interrupted whatever you were mapping.",
        "I will leave you to it. Talk later.",
    )

    results, spoken = _visit(agent, turns)
    topics = {
        item["offline_topic_match"]["topic_id"]
        for item in results
        if item["offline_topic_match"]["topic_id"]
    }
    self_corrections = sum(
        item["action_decision"]["communicative_function"] == "self_correct"
        for item in results
    )

    assert {
        "identity_and_continuity", "retro_culture_and_analogies",
        "pretorius_and_collaboration", "physics_and_uncertainty",
    } <= topics
    assert results[3]["conversation_candidate"]["move"] == "honor_obligation"
    assert results[4]["offline_topic_plan"]["family"] == "ordinary"
    assert results[9]["offline_topic_plan"]["family"] != "first_mention"
    assert results[10]["conversation_candidate"]["move"] in {
        "defer_and_note", "reminisce_and_note",
    }
    assert self_corrections <= 2
    assert all(item["model_calls"]["external_model_calls"] == 0 for item in results)
    assert len(spoken) == len(set(spoken))
    assert any(
        marker in " ".join(spoken).casefold()
        for marker in ("mixtape", "vhs", "radio", "video store")
    )


def test_private_diary_handoff_returns_as_conversation_not_prop_exposition(tmp_path):
    agent = CharacterAgent(
        cartridge_path=str(PRETORIUS), user_id="jay",
        db_path=str(tmp_path / "handoff_visit.db"),
    )
    asked = agent.say(
        "Could quantum error correction resemble autobiographical reconsolidation?",
        event_time=START,
    )
    loop = next(
        item for item in agent.engine.intentions.open_loops
        if item.reason == "offline_knowledge_unavailable"
    )
    assert asked["response"]
    assert "diary" not in asked["response"].casefold()
    assert "notebook" not in asked["response"].casefold()

    agent.complete_offline_inquiry(
        topic_key=loop.topic_key,
        first_person_note=(
            "I examined Jay's analogy. Both processes preserve usable structure "
            "under disturbance, but they do not share a mechanism."
        ),
        character_position=(
            "The analogy is useful at the level of preserving structure under "
            "disturbance, but not as a claim of identical mechanism"
        ),
        timestamp=START + 120,
    )
    loop.created_at = START
    loop.last_touched = START
    returned = agent.say(
        "Did you reach a position on the question I left with you?",
        event_time=START + 240,
    )

    assert returned["conversation_candidate"]["move"] == "return_to_topic"
    assert "preserving structure under disturbance" in returned["response"]
    assert "diary" not in returned["response"].casefold()
    assert "notebook" not in returned["response"].casefold()
    assert agent.engine.journal.object_name in agent.engine.world.objects
    assert [item.entry_kind for item in agent.engine.journal.entries] == [
        "field_note", "research_note",
    ]
