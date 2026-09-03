"""Cold biography should restore grounded recall without becoming hot state."""

import os
import tempfile
from pathlib import Path

from persona_engine.agent import CharacterAgent
from persona_engine.core.cold_biography import (
    context_focus_tokens,
    contextual_readthrough_request,
    explicit_recall_request,
    grounded_context_match,
    grounded_recall_match,
    recall_focus_tokens,
)

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


def test_recall_focus_uses_topic_not_retrieval_scaffolding():
    assert recall_focus_tokens(QUERY) == {"observatory", "code", "word"}
    assert grounded_recall_match(
        QUERY,
        "Please remember this neutral detail: the old observatory code word is amber-otter.",
    ) is True
    assert grounded_recall_match(
        "Do you remember the brass telescope serial number I told you?",
        "Please remember this neutral detail: the old observatory code word is amber-otter.",
    ) is False


def test_attributive_recall_preserves_topic_anchors():
    query = "What color did I say the atlas cover was?"
    assert explicit_recall_request(query)
    assert recall_focus_tokens(query) == {"atlas", "cover"}
    assert grounded_recall_match(query, "Remember this: the atlas cover is amber.")
    assert not grounded_recall_match(query, "The telescope cover is amber.")
    assert not grounded_recall_match("What color did I say it was?", "The atlas cover is amber.")
    assert not explicit_recall_request("What color is the atlas cover?")


def test_attributive_recall_survives_restart_and_remains_interlocutor_scoped(tmp_path):
    db = str(tmp_path / "state.db")
    agent = CharacterAgent(cartridge_path=str(CART), user_id="alice", db_path=db)
    agent.say("Remember this: the atlas cover is amber.")
    agent.engine.persistence.close()
    agent = CharacterAgent(cartridge_path=str(CART), user_id="alice", db_path=db)
    result = agent.say("What color did I say the atlas cover was?")
    assert "amber" in result["response"].lower()
    assert any("atlas cover is amber" in item["content"] for item in result["retrieved_memory_trace"])
    negative = agent.say("What color did I say the telescope cover was?")
    assert negative["retrieved_memory_trace"] == []
    agent.engine.persistence.close()
    bob = CharacterAgent(cartridge_path=str(CART), user_id="bob", db_path=db)
    result = bob.say("What color did I say the atlas cover was?")
    assert result["retrieved_memory_trace"] == []
    assert "amber" not in result["response"].lower()
    bob.engine.persistence.close()


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


def test_nonexistent_explicit_recall_fails_closed_instead_of_using_nearest_memory():
    with tempfile.TemporaryDirectory() as d:
        db = os.path.join(d, "state.db")
        _make_history(db)
        agent = CharacterAgent(cartridge_path=str(CART), user_id="alice", db_path=db)
        _project_one(agent)

        result = agent.say("Do you remember the brass telescope serial number I told you?")

        assert result["retrieved_memory_trace"] == []
        assert TARGET not in result["response"].lower()
        assert "grounded memory" in result["response"].lower()


def test_anchorless_explicit_recall_fails_closed():
    with tempfile.TemporaryDirectory() as d:
        db = os.path.join(d, "state.db")
        _make_history(db)
        agent = CharacterAgent(cartridge_path=str(CART), user_id="alice", db_path=db)
        _project_one(agent)

        result = agent.say("Do you remember what I told you?")

        assert result["retrieved_memory_trace"] == []
        assert "grounded memory" in result["response"].lower()


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



def _project_two(agent: CharacterAgent) -> None:
    memories = list(agent.engine.memory.memories)
    agent.engine.memory.memories = sorted(memories, key=_priority, reverse=True)[:2]


def test_contextual_readthrough_requires_continuation_and_multiple_grounded_anchors():
    query = "Is the old observatory code word still the same?"
    assert contextual_readthrough_request(query) is True
    assert context_focus_tokens(query) == {"observatory", "code", "word"}
    assert grounded_context_match(
        query,
        "Please remember this neutral detail: the old observatory code word is amber-otter.",
    ) is True
    assert grounded_context_match(
        "Is the brass telescope serial number still the same?",
        "Please remember this neutral detail: the old observatory code word is amber-otter.",
    ) is False
    assert contextual_readthrough_request("Is it still the same?") is False
    assert contextual_readthrough_request("What is the old observatory code word?") is False


def test_contextual_cold_readthrough_changes_observable_answer_without_rehydrating_hot_memory():
    with tempfile.TemporaryDirectory() as d:
        db = os.path.join(d, "state.db")
        _make_history(db)
        agent = CharacterAgent(cartridge_path=str(CART), user_id="alice", db_path=db)
        _project_two(agent)
        assert all(TARGET not in memory.content.lower() for memory in agent.engine.memory.memories)

        result = agent.say("Is the old observatory code word still the same?")

        assert TARGET in result["response"].lower()
        assert any(
            TARGET in item["content"].lower()
            and "cold_biography" in item["tags"]
            and "contextual_readthrough" in item["tags"]
            for item in result["retrieved_memory_trace"]
        )
        assert all(TARGET not in memory.content.lower() for memory in agent.engine.memory.memories)


def test_contextual_cold_readthrough_fails_closed_for_never_happened_and_anchorless_topics():
    with tempfile.TemporaryDirectory() as d:
        db = os.path.join(d, "state.db")
        _make_history(db)
        agent = CharacterAgent(cartridge_path=str(CART), user_id="alice", db_path=db)
        _project_two(agent)

        negative = agent.say("Is the brass telescope serial number still the same?")
        broad = agent.say("Is it still the same?")

        assert not any("contextual_readthrough" in item["tags"] for item in negative["retrieved_memory_trace"])
        assert not any("contextual_readthrough" in item["tags"] for item in broad["retrieved_memory_trace"])
        assert TARGET not in negative["response"].lower()
        assert TARGET not in broad["response"].lower()


def test_contextual_cold_readthrough_does_not_cross_interlocutor_boundary():
    with tempfile.TemporaryDirectory() as d:
        db = os.path.join(d, "state.db")
        _make_history(db, "alice")
        bob = CharacterAgent(cartridge_path=str(CART), user_id="bob", db_path=db)
        result = bob.say("Is the old observatory code word still the same?")
        assert TARGET not in result["response"].lower()
        assert not any("contextual_readthrough" in item["tags"] for item in result["retrieved_memory_trace"])
