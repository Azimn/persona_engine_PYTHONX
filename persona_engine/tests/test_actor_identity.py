"""Actor identity keeps social history separate without requiring unique names."""

from pathlib import Path

from persona_engine.agent import CharacterAgent
from persona_engine.core.actors import ActorRegistry


ROOT = Path(__file__).resolve().parents[1]
PRETORIUS = ROOT / "cartridges" / "pretorius.snp"
END_TIME = 1_800_000_000.0


def _agent(tmp_path, name="actors"):
    return CharacterAgent(
        cartridge_path=str(PRETORIUS),
        user_id="actor_test",
        db_path=str(tmp_path / f"{name}.db"),
    )


def test_duplicate_names_remain_distinct_and_ambiguous_reference_matches_both():
    registry = ActorRegistry()
    first = registry.resolve(
        stable_key="game:npc_17", display_name="Henry", tick=1, actor_kind="npc"
    )
    second = registry.resolve(
        stable_key="discord:48291", display_name="Henry", tick=2, actor_kind="human"
    )

    assert first.actor_id != second.actor_id
    assert {registry.display_label(first.actor_id), registry.display_label(second.actor_id)} == {
        "Henry-A", "Henry-B"
    }
    assert {item.actor_id for item in registry.match_text("Henry said he would return.")} == {
        first.actor_id, second.actor_id
    }


def test_stable_external_key_restores_the_same_actor_without_false_encounter():
    registry = ActorRegistry()
    actor = registry.resolve(
        stable_key="discord:48291", display_name="Jay", tick=3, actor_kind="human"
    )
    loaded = ActorRegistry.from_list(registry.to_list())
    restored = loaded.resolve(
        stable_key="discord:48291", display_name="Jay", tick=50,
        actor_kind="human", observe=False,
    )

    assert restored.actor_id == actor.actor_id
    assert restored.encounter_count == 1
    assert restored.last_seen_tick == 3


def test_relationship_state_is_scoped_to_the_active_actor_and_restored(tmp_path):
    agent = _agent(tmp_path)
    agent.say(
        "You are worthless and you lied to me.",
        visible_context={"speaker_id": "jay-1", "speaker_name": "Jay"},
    )
    jay_id = agent.engine.active_actor_id
    jay_state = agent.engine.actor_relationships.for_actor(jay_id)
    jay_tension = jay_state.tension

    agent.say(
        "Thank you. I appreciate you.",
        visible_context={"speaker_id": "kiki-1", "speaker_name": "Kiki"},
    )
    kiki_id = agent.engine.active_actor_id
    kiki_state = agent.engine.actor_relationships.for_actor(kiki_id)

    assert jay_id != kiki_id
    assert jay_tension > kiki_state.tension
    assert jay_state.turns == 1
    assert kiki_state.turns == 1

    agent.say(
        "I am back.",
        visible_context={"speaker_id": "jay-1", "speaker_name": "Jay"},
    )

    assert agent.engine.active_actor_id == jay_id
    assert agent.engine.relationship is jay_state
    assert agent.engine.relationship.tension >= jay_tension


def test_actor_identity_tags_the_event_experience_and_memory(tmp_path):
    agent = _agent(tmp_path)
    agent.say(
        "Remember that I returned the brass key.",
        visible_context={"speaker_id": "jay-1", "speaker_name": "Jay"},
    )
    actor_id = agent.engine.active_actor_id
    event = next(
        item for item in agent.engine.world_events.recent(20)
        if item.source == "user_input"
    )
    experience = next(
        item for item in agent.engine.experiences.experiences
        if item.world_event_id == event.event_id
    )
    memory = agent.engine.experiences.consolidate(
        experience, agent.engine.memory, event.timestamp, force=True
    )

    assert event.payload["actor_ids"] == [actor_id]
    assert experience.provenance["actor_ids"] == [actor_id]
    assert memory is not None
    assert f"actor:{actor_id:08x}" in memory.tags


def test_actor_relationships_persist_without_collapsing_people(tmp_path):
    agent = _agent(tmp_path)
    agent.say(
        "You lied to me.",
        visible_context={"speaker_id": "henry-a", "speaker_name": "Henry"},
    )
    first_id = agent.engine.active_actor_id
    agent.say(
        "Thank you.",
        visible_context={"speaker_id": "henry-b", "speaker_name": "Henry"},
    )
    second_id = agent.engine.active_actor_id
    expected = {
        first_id: agent.engine.actor_relationships.for_actor(first_id).tension,
        second_id: agent.engine.actor_relationships.for_actor(second_id).tension,
    }

    restarted = _agent(tmp_path)

    assert first_id != second_id
    assert restarted.engine.actor_registry.fetch(first_id).display_name == "Henry"
    assert restarted.engine.actor_registry.fetch(second_id).display_name == "Henry"
    assert {
        actor_id: restarted.engine.actor_relationships.for_actor(actor_id).tension
        for actor_id in expected
    } == expected


def test_genesis_uses_historical_age_and_actor_tagged_sparse_chapters(tmp_path):
    agent = _agent(tmp_path)
    result = agent.replay_genesis(end_time=END_TIME)
    events = agent.engine.world_events.recent(100)
    memories = agent.engine.memory.memories
    henry = next(
        item for item in agent.engine.actor_registry.records.values()
        if item.stable_key == "genesis:henry frankenstein"
    )
    tower = next(item for item in memories if "span_years:29" in item.tags)

    assert result["end_time"] - result["start_time"] > 180 * 365 * 86400
    assert max(event.timestamp for event in events) - min(event.timestamp for event in events) > 180 * 365 * 86400
    assert "chapter_summary" in tower.tags
    assert f"actor:{henry.actor_id:08x}" in {
        tag for memory in memories for tag in memory.tags
    }
    assert len(agent.engine.actor_relationships.values) == 1
    assert result["events_created"] == 23
    assert result["events_missed"] == 1


def test_actor_relationships_are_private_but_inspectable(tmp_path):
    agent = _agent(tmp_path)
    for speaker_id in ("henry-a", "henry-b"):
        agent.say(
            "Hello.", visible_context={"speaker_id": speaker_id, "speaker_name": "Henry"}
        )

    public = agent.public_status()
    inspector = agent.debug_snapshot()["life_inspector"]

    assert "actors" not in public
    assert "actor_relationships" not in public
    assert {
        item["display_label"] for item in inspector["actors"]
        if item["display_name"] == "Henry"
    } == {"Henry-A", "Henry-B"}
    assert inspector["active_actor_id"] == agent.engine.active_actor_id
