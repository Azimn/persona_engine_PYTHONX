"""Cartridge-authored history must become imperfect lived state, not imported biography."""

from pathlib import Path
import json

from persona_engine.agent import CharacterAgent
from persona_engine.core.memory import MemoryStore, MemoryUnit
from persona_engine.core.renderer import LocalLLMRenderer
from persona_engine.core.c99_fixtures import developmental_fixture


ROOT = Path(__file__).resolve().parents[1]
CART = ROOT / "cartridges" / "pretorius.snp"
END_TIME = 1_800_000_000.0


def _agent(tmp_path, name="pretorius"):
    return CharacterAgent(
        cartridge_path=str(CART), user_id="genesis_test", db_path=str(tmp_path / f"{name}.db"),
    )


def test_genesis_replays_through_world_perception_and_memory_owners(tmp_path):
    agent = _agent(tmp_path)
    result = agent.replay_genesis(end_time=END_TIME)

    assert result["episodes_processed"] == 23
    assert result["events_created"] == 23
    assert result["events_missed"] == 1
    assert 1 <= result["memories_consolidated"] < result["episodes_processed"]
    assert all(event.source == "cartridge_genesis" for event in agent.engine.world_events.recent(100))
    assert all(item.perceived_summary.startswith("I ") for item in agent.engine.experiences.experiences)
    assert not any(
        "shared moral decision" in item.content for item in agent.engine.memory.memories
    )


def test_genesis_is_idempotent_and_persists_across_reload(tmp_path):
    agent = _agent(tmp_path)
    first = agent.replay_genesis(end_time=END_TIME)
    counts = (
        len(agent.engine.world_events.to_list()),
        len(agent.engine.experiences.experiences),
        len(agent.engine.memory.memories),
    )
    second = agent.replay_genesis(end_time=END_TIME)
    restarted = _agent(tmp_path)

    assert second["already_applied"] is True
    assert second["replay_digest"] == first["replay_digest"]
    assert counts == (
        len(restarted.engine.world_events.to_list()),
        len(restarted.engine.experiences.experiences),
        len(restarted.engine.memory.memories),
    )
    assert restarted.replay_genesis(end_time=END_TIME)["already_applied"] is True


def test_incompatible_fictional_continuities_remain_inspectable(tmp_path):
    agent = _agent(tmp_path)
    agent.replay_genesis(end_time=END_TIME)
    outcomes = [item.outcome for item in agent.engine.world_events.recent(100)]
    interpretations = [item.current_meaning for item in agent.engine.autobiographical_interpretations.interpretations]

    assert any("unable to escape" in item and "survival" in item for item in outcomes)
    assert any("fictional character" in item and "Ernest Thesiger" in item for item in outcomes)
    assert any("remember dying and surviving" in item for item in interpretations)
    assert any("fictional while I can demonstrate" in item for item in interpretations)


def test_remote_explicit_cue_can_defeat_unrelated_recency():
    store = MemoryStore()
    store.add(MemoryUnit("I worked with Henry Frankenstein on forbidden creation.", created_at=1.0, salience=.7))
    store.add(MemoryUnit("I adjusted a lamp yesterday.", created_at=10_000_000.0, salience=1.0, emotional_intensity=1.0))

    result = store.retrieve_explained("What do I remember about Henry Frankenstein?", 10_000_001.0, top_k=1)[0]

    assert "Henry Frankenstein" in result.memory.content
    assert result.reasons["direct_symbolic_cue"] == 1.0


def test_retrieval_candidates_do_not_strengthen_until_considered():
    store = MemoryStore()
    selected = MemoryUnit("I remember the selected event.", created_at=1.0)
    inhibited = MemoryUnit("I remember the inhibited event.", created_at=1.0)
    store.add(selected)
    store.add(inhibited)

    store.retrieve_explained("event", 100.0, top_k=2)
    assert selected.recall_times == inhibited.recall_times == []

    store.record_recall([selected], 100.0)
    assert selected.recall_times == [100.0]
    assert inhibited.recall_times == []


def test_genesis_changes_memory_grounded_expression_without_renderer_authority(tmp_path):
    fresh = _agent(tmp_path, "fresh")
    lived = _agent(tmp_path, "lived")
    lived.replay_genesis(end_time=END_TIME)
    historical_ids = {
        item.interpretation_id for item in lived.engine.autobiographical_interpretations.interpretations
    }

    fresh_result = fresh.say("What happened when the Bride opened her eyes?", event_time=END_TIME + 1)
    lived_result = lived.say("What happened when the Bride opened her eyes?", event_time=END_TIME + 1)

    assert not any(item["reasons"].get("direct_symbolic_cue") for item in fresh_result["retrieved_memory_trace"])
    assert any(item["reasons"].get("direct_symbolic_cue") for item in lived_result["retrieved_memory_trace"])
    assert lived_result["response"] != fresh_result["response"]
    assert historical_ids.issubset({
        item.interpretation_id for item in lived.engine.autobiographical_interpretations.interpretations
    })


def test_journal_is_a_plain_text_artifact_and_reading_creates_new_experience(tmp_path):
    agent = _agent(tmp_path)
    agent.replay_genesis(end_time=END_TIME)
    before = len(agent.engine.experiences.experiences)
    path = Path(agent.materialize_journal())
    text = path.read_text(encoding="utf-8")

    assert path.name.endswith(".journal.txt")
    assert "Pretorius's black laboratory notebook" in text
    assert "The evidence is offensively good" in text

    read = agent.read_journal("fictional evidence", timestamp=END_TIME + 1)
    assert read["entries"]
    assert read["experience"]["distortion"]["journal_is_evidence_of_writing_not_objective_truth"] is True
    assert len(agent.engine.experiences.experiences) == before + 1
    assert agent.engine.world_events.fetch(read["world_event_id"]).event_type == "journal_reading"


def test_journal_read_and_write_use_world_action_channel(tmp_path):
    agent = _agent(tmp_path)
    agent.replay_genesis(end_time=END_TIME)

    written = agent.propose_world_action(
        "write_journal", {"text": "The contradiction remains useful because it refuses a cheap conclusion."},
        event_time=END_TIME + 1,
    )
    read = agent.propose_world_action(
        "read_journal", {"query": "contradiction conclusion"}, event_time=END_TIME + 2,
    )

    assert written["accepted"] is True
    assert written["journal_entry"]["source"] == "character_world_action"
    assert read["accepted"] is True
    assert any("cheap conclusion" in item["text"] for item in read["journal"]["entries"])
    assert all(fact["source"] == "action_resolution" for fact in read["facts"])


def test_model_memory_invention_falls_back_to_grounded_expression(tmp_path):
    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def read(self):
            return json.dumps({
                "message": {"content": "She gave me a quiet, assessing gaze before accepting the Monster."}
            }).encode("utf-8")

    agent = _agent(tmp_path)
    agent.replay_genesis(end_time=END_TIME)
    agent.engine.set_renderer(LocalLLMRenderer(
        model_name="fake", provider="ollama", thinking_mode="off",
        opener=lambda *args, **kwargs: FakeResponse(),
    ))

    result = agent.say("What happened when the Bride opened her eyes?", event_time=END_TIME + 1)

    assert "watched the Bride open her eyes" in result["response"]
    assert "accepting the Monster" not in result["response"]
    assert agent.engine.renderer_status()["actual_provider"] == "offline"
    assert "grounding check" in agent.engine.renderer_status()["fallback_reason"]


def test_genesis_and_journal_are_private_inspectable_portable_state(tmp_path):
    agent = _agent(tmp_path)
    agent.replay_genesis(end_time=END_TIME)

    public = agent.public_status()
    debug = agent.debug_snapshot()["life_inspector"]
    fixture = developmental_fixture(agent.engine)

    assert "journal" not in public
    assert "genesis_replays" not in public
    assert len(debug["journal"]["entries"]) == 10
    assert debug["genesis_replays"][0]["episodes_processed"] == 23
    assert fixture["journal"]["entries"] == debug["journal"]["entries"]
    assert fixture["genesis_replays"][0]["replay_digest"] == debug["genesis_replays"][0]["replay_digest"]
