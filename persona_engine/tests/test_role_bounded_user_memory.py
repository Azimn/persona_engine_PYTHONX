"""Production role-bounded USER_TOLD memory residency."""

import os
import tempfile
import time
from pathlib import Path

from persona_engine.agent import CharacterAgent
from persona_engine.core.memory import KnowledgeSource, MemoryUnit, REFLECTION_RETRIEVAL_WIDTH, TURN_RETRIEVAL_WIDTH

ROOT = Path(__file__).resolve().parents[1]
CART = ROOT / "cartridges" / "pretorius.snp"


def _agent(directory: str, user: str = "alice") -> CharacterAgent:
    return CharacterAgent(cartridge_path=str(CART), user_id=user, db_path=os.path.join(directory, "state.db"))


def test_consumer_widths_are_named_and_not_an_unexplained_capacity():
    assert REFLECTION_RETRIEVAL_WIDTH == 3
    assert TURN_RETRIEVAL_WIDTH == 4


def test_compaction_pins_non_user_memories_and_bounds_user_roles():
    with tempfile.TemporaryDirectory() as directory:
        agent = _agent(directory)
        base = time.time()
        # Add four active unresolved user memories directly so the widest current
        # consumer determines the protected count.
        for index in range(4):
            agent.engine.memory.add(MemoryUnit(
                content=f"I heard you say: unresolved episode {index}",
                created_at=base + index,
                source=KnowledgeSource.USER_TOLD,
                unresolved=True,
                relationship_relevance=0.8,
                emotional_intensity=0.8,
            ))
        for index in range(10):
            agent.engine.memory.add(MemoryUnit(
                content=f"I heard you say: ordinary topic {index}",
                created_at=base + 20 + index,
                source=KnowledgeSource.USER_TOLD,
            ))
        observed = MemoryUnit("I noticed a bell.", base + 40, source=KnowledgeSource.OBSERVED)
        reflection = MemoryUnit("I formed a reflection: something changed.", base + 41, source=KnowledgeSource.REFLECTION)
        agent.engine.memory.add(observed)
        agent.engine.memory.add(reflection)
        agent.engine.relationship.unresolved_conflict = 0.4

        stats = agent.engine.memory.compact_user_told_working_set(agent.engine.relationship)

        user = [m for m in agent.engine.memory.memories if m.source == KnowledgeSource.USER_TOLD]
        assert len(user) <= REFLECTION_RETRIEVAL_WIDTH + TURN_RETRIEVAL_WIDTH
        assert observed in agent.engine.memory.memories
        assert reflection in agent.engine.memory.memories
        assert stats["evicted_user_told"] > 0


def test_full_repair_sets_episode_boundary_and_clears_stale_tension_loops():
    with tempfile.TemporaryDirectory() as directory:
        agent = _agent(directory)
        agent.say("You lied to me. This is your fault.")
        agent.say("You lied to me again. This is your fault too.")
        assert agent.engine.relationship.unresolved_conflict > 0.0
        assert any(loop.topic.startswith("unresolved tension from:") for loop in agent.engine.intentions.open_loops)
        agent.say("I was wrong. I'm sorry.")
        assert agent.engine.relationship.unresolved_conflict == 0.0
        assert agent.engine.relationship.last_conflict_resolved_at > 0.0
        assert not any(loop.topic.startswith("unresolved tension from:") for loop in agent.engine.intentions.open_loops)


def test_new_conflict_does_not_reactivate_old_repaired_episode_as_decision_evidence():
    with tempfile.TemporaryDirectory() as directory:
        agent = _agent(directory)
        first = agent.say("You lied to me. This is your fault.")
        old_ids = {m.id for m in agent.engine.memory.memories if m.unresolved}
        agent.say("I was wrong. I'm sorry.")
        cutoff = agent.engine.relationship.last_conflict_resolved_at
        assert cutoff > 0.0
        agent.say("You lied to me again. This is your fault too.")
        result = agent.say("Can you trust me enough to work with me on this?")
        evidence_ids = set(result["decision_payload"]["history_evidence"]["memory_ids"])
        assert result["decision_payload"]["history_evidence"]["active"] is True
        assert evidence_ids
        assert not (evidence_ids & old_ids)
        for memory in agent.engine.memory.memories:
            if memory.id in evidence_ids:
                assert memory.created_at > cutoff


def test_old_evicted_topic_is_recovered_by_grounded_what_about_continuation():
    with tempfile.TemporaryDirectory() as directory:
        agent = _agent(directory)
        agent.say("The workshop door is saffron today.")
        for index in range(8):
            agent.say(f"Current topic {index}: marker {index} is ordinary.")
        assert all("saffron" not in m.content.lower() for m in agent.engine.memory.memories)

        result = agent.say("What about the workshop door?")

        assert any("saffron" in item["content"].lower() and "cold_biography" in item["tags"] for item in result["retrieved_memory_trace"])
        assert "saffron" in result["response"].lower()
        assert all("saffron" not in m.content.lower() for m in agent.engine.memory.memories)


def test_what_about_negative_still_fails_closed():
    with tempfile.TemporaryDirectory() as directory:
        agent = _agent(directory)
        agent.say("The workshop door is saffron today.")
        for index in range(8):
            agent.say(f"Current topic {index}: marker {index} is ordinary.")
        result = agent.say("What about the harbor telescope?")
        assert "saffron" not in result["response"].lower()
        assert not any("cold_biography" in item["tags"] for item in result["retrieved_memory_trace"])


def test_production_residency_stays_small_under_routine_user_history():
    with tempfile.TemporaryDirectory() as directory:
        agent = _agent(directory)
        for index in range(100):
            agent.say(f"Routine production note {index}: shelf marker {index}.")
        user_count = sum(1 for m in agent.engine.memory.memories if m.source == KnowledgeSource.USER_TOLD)
        assert user_count <= TURN_RETRIEVAL_WIDTH
        # Canonical biography remains complete despite hot eviction.
        inputs = list(agent.engine.persistence.iter_continuity_events(agent.engine.identity.name, agent.engine.user_id, event_type="input"))
        assert len(inputs) == 100
