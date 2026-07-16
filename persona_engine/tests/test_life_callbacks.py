"""Grounded callbacks make elapsed life visible without inventing offscreen facts."""

from pathlib import Path

from persona_engine.agent import CharacterAgent
from persona_engine.core.intention import OpenLoop
from persona_engine.core.offline_conversation import derive_conversation_candidate


ROOT = Path(__file__).resolve().parents[1]
PRETORIUS = ROOT / "cartridges" / "pretorius.snp"
KIKI = ROOT / "cartridges" / "kiki.snp"
NEUTRAL = ROOT / "cartridges" / "neutral.snp"


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


def test_return_does_not_unsolicitedly_mention_journal_or_private_text(tmp_path):
    agent = _agent(tmp_path)
    agent.say("Why analyze tensor categories in quantum gravity?")
    private_text = agent.engine.journal.entries[-1].text
    agent.engine.last_wall_time -= 120

    result = agent.say("Hello, I am back.")

    assert result["conversation_candidate"]["move"] != "journal_allusion"
    assert agent.engine.journal.object_name not in result["response"]
    assert private_text not in result["response"]
    assert "tensor categories" not in result["system_prompt"].lower()


def test_every_character_possesses_its_journal_as_world_inventory(tmp_path):
    pretorius = _agent(tmp_path, PRETORIUS, "pretorius_inventory")
    kiki = _agent(tmp_path, KIKI, "kiki_inventory")
    neutral = _agent(tmp_path, NEUTRAL, "neutral_inventory")

    for agent in (pretorius, kiki, neutral):
        assert agent.engine.journal.object_name in agent.engine.world.objects


def test_journal_inventory_survives_reload_without_duplicate(tmp_path):
    first = _agent(tmp_path, KIKI, "inventory_reload")
    object_name = first.engine.journal.object_name
    first.say("Hello.")

    restarted = _agent(tmp_path, KIKI, "inventory_reload")
    assert restarted.engine.world.objects.count(object_name) == 1


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


def test_pretorius_and_kiki_keep_journal_out_of_ordinary_return_dialogue(tmp_path):
    pretorius = _agent(tmp_path, PRETORIUS, "pretorius")
    kiki = _agent(tmp_path, KIKI, "kiki")
    for agent in (pretorius, kiki):
        agent.say("Why analyze tensor categories in quantum gravity?")
        agent.engine.last_wall_time -= 120

    pretorius_result = pretorius.say("I am back.")
    kiki_result = kiki.say("I am back.")

    assert pretorius.engine.journal.object_name not in pretorius_result["response"]
    assert kiki.engine.journal.object_name not in kiki_result["response"]
