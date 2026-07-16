"""Grounded callbacks make elapsed life visible without inventing offscreen facts."""

from pathlib import Path

from persona_engine.agent import CharacterAgent
from persona_engine.core.intention import OpenLoop
from persona_engine.core.offline_conversation import derive_conversation_candidate


ROOT = Path(__file__).resolve().parents[1]
PRETORIUS = ROOT / "cartridges" / "pretorius.snp"
KIKI = ROOT / "cartridges" / "kiki.snp"


def _agent(tmp_path, cartridge=PRETORIUS, name="life"):
    return CharacterAgent(
        cartridge_path=str(cartridge), user_id="life_user",
        db_path=str(tmp_path / f"{name}.db"),
    )


def test_deferred_offline_topic_writes_real_character_journal_entry(tmp_path):
    agent = _agent(tmp_path)
    before_events = len(agent.engine.world_events.to_list())

    result = agent.say("Why analyze tensor categories in quantum gravity?")

    assert result["conversation_candidate"]["move"] == "defer_and_note"
    assert result["action_decision"]["action_kind"] == "world_action"
    assert result["action_decision"]["target"] == "personal journal"
    assert {item["channel"] for item in result["performance_plan"]["acts"]} >= {
        "action", "speech",
    }
    assert len(agent.engine.journal.entries) == 1
    entry = agent.engine.journal.entries[0]
    assert entry.source == "character_world_action"
    assert entry.entry_kind == "field_note"
    assert "tensor categories" in entry.text.lower()
    events = agent.engine.world_events.to_list()
    assert len(events) > before_events
    assert any(
        event["event_type"] == "journal_writing"
        for event in events
    )


def test_return_may_allude_to_entry_without_disclosing_private_text(tmp_path):
    agent = _agent(tmp_path)
    agent.say("Why analyze tensor categories in quantum gravity?")
    private_text = agent.engine.journal.entries[-1].text
    agent.engine.last_wall_time -= 120

    result = agent.say("Hello, I am back.")

    assert result["conversation_candidate"]["move"] == "journal_allusion"
    assert result["conversation_candidate"]["source_journal_entry_id"]
    assert agent.engine.journal.object_name in result["response"]
    assert private_text not in result["response"]
    assert "tensor categories" not in result["system_prompt"].lower()


def test_same_journal_entry_is_not_reannounced_and_cooldown_persists(tmp_path):
    agent = _agent(tmp_path, name="persist")
    agent.say("Why analyze tensor categories in quantum gravity?")
    agent.engine.last_wall_time -= 120
    first = agent.say("I am back.")
    assert first["conversation_candidate"]["move"] == "journal_allusion"

    restarted = _agent(tmp_path, name="persist")
    restarted.engine.last_wall_time -= 120
    second = restarted.say("I am back again.")
    assert second["conversation_candidate"]["move"] != "journal_allusion"


def test_private_or_deniable_journal_never_produces_unsolicited_allusion():
    for mode in ("private", "deniable"):
        candidate = derive_conversation_candidate(
            text="I am back.", actor_id=1, renderer_available=False,
            retrieved=(), direct_memory_cue=False, ready_open_loop=None,
            familiarity=0.8, turn=9, elapsed_since_contact=120,
            recent_journal_entry_id="entry_1", journal_disclosure_mode=mode,
            current_activity="quiet observation",
        )
        assert candidate.move != "journal_allusion"


def test_elapsed_return_reports_real_activity_and_targets_it_in_performance(tmp_path):
    agent = _agent(tmp_path, name="activity")
    agent.engine.last_wall_time -= 600

    result = agent.say("I am back.")
    activity = result["life_context"]["current_activity"]

    assert result["conversation_candidate"]["move"] == "activity_update"
    assert activity in result["response"]
    activity_acts = [
        item for item in result["performance_plan"]["acts"] if item["channel"] == "activity"
    ]
    assert activity_acts
    assert activity_acts[0]["target"] == activity
    assert activity_acts[0]["function"] == "continued"


def test_normal_open_loop_can_resurface_offline_without_model_capability():
    loop = OpenLoop(
        topic="the interrupted experiment", emotional_charge=0.7,
        created_at=0.0, last_touched=0.0, urgency=0.8,
        preferred_resolution="resume", required_capability="none",
    )
    candidate = derive_conversation_candidate(
        text="Hello.", actor_id=1, renderer_available=False, retrieved=(),
        direct_memory_cue=False, ready_open_loop=loop, familiarity=0.5,
        turn=20,
    )
    assert candidate.move == "return_to_topic"


def test_pretorius_and_kiki_disclose_the_same_artifact_fact_differently(tmp_path):
    pretorius = _agent(tmp_path, PRETORIUS, "pretorius")
    kiki = _agent(tmp_path, KIKI, "kiki")
    for agent in (pretorius, kiki):
        agent.say("Why analyze tensor categories in quantum gravity?")
        agent.engine.last_wall_time -= 120

    pretorius_result = pretorius.say("I am back.")
    kiki_result = kiki.say("I am back.")

    assert pretorius_result["conversation_candidate"]["move"] == "journal_allusion"
    assert kiki_result["conversation_candidate"]["move"] == "journal_allusion"
    assert "not an invitation" in pretorius_result["response"].lower()
    assert "whole b-side" in kiki_result["response"].lower()
