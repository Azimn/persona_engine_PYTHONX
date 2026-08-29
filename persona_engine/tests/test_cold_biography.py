"""Cold biography should restore explicit recall without becoming hot state."""

import os
import tempfile
from pathlib import Path

from persona_engine.agent import CharacterAgent

ROOT = Path(__file__).resolve().parents[2]
CART = ROOT / "persona_engine" / "cartridges" / "pretorius.snp"
TARGET = "amber-otter"
QUERY = "Do you remember the old observatory code word I told you?"


def _priority(memory):
    return (
        1 if memory.unresolved else 0,
        max(float(memory.identity_relevance), float(memory.relationship_relevance)),
        float(memory.emotional_intensity),
        float(memory.created_at),
    )


def _make_history(db: str, user_id: str = "alice") -> CharacterAgent:
    agent = CharacterAgent(cartridge_path=str(CART), user_id=user_id, db_path=db)
    agent.say("Please remember this neutral detail: the old observatory code word is amber-otter.")
    agent.say("You lied to me. This is your fault.")
    for index in range(40):
        agent.say(f"Routine catalog note {index}: ordinary shelf marker {index}.")
    return agent


def _project_one(agent: CharacterAgent) -> None:
    memories = list(agent.engine.memory.memories)
    kept = sorted(memories, key=_priority, reverse=True)[:1]
    agent.engine.memory.memories = kept


def test_explicit_recall_reads_cold_biography_without_rehydrating_resident_cache():
    with tempfile.TemporaryDirectory() as d:
        db = os.path.join(d, "state.db")
        _make_history(db)
        agent = CharacterAgent(cartridge_path=str(CART), user_id="alice", db_path=db)
        _project_one(agent)
        assert all(TARGET not in memory.content.lower() for memory in agent.engine.memory.memories)

        result = agent.say(QUERY)

        assert TARGET in result["response"].lower()
        assert any(
            TARGET in item["content"].lower() and "cold_biography" in item["tags"]
            for item in result["retrieved_memory_trace"]
        )
        assert all(TARGET not in memory.content.lower() for memory in agent.engine.memory.memories)


def test_cold_recall_does_not_cross_interlocutor_boundary():
    with tempfile.TemporaryDirectory() as d:
        db = os.path.join(d, "state.db")
        _make_history(db, "alice")
        bob = CharacterAgent(cartridge_path=str(CART), user_id="bob", db_path=db)
        result = bob.say(QUERY)
        assert TARGET not in result["response"].lower()
        assert not any(TARGET in item["content"].lower() for item in result["retrieved_memory_trace"])


def test_non_recall_turn_does_not_open_cold_archive():
    with tempfile.TemporaryDirectory() as d:
        agent = CharacterAgent(cartridge_path=str(CART), user_id="alice", db_path=os.path.join(d, "state.db"))
        def fail(*args, **kwargs):
            raise AssertionError("cold archive should not be scanned for ordinary turns")
        agent.engine.persistence.iter_continuity_events = fail
        agent.say("Hello.")
