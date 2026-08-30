"""Experience-level guards for memory and repair semantics."""

import os
import tempfile
import time
from pathlib import Path

from persona_engine.agent import CharacterAgent

ROOT = Path(__file__).resolve().parents[1]
CART = ROOT / "cartridges" / "pretorius.snp"


def test_repaired_history_does_not_reenter_reflection_as_current_unresolved_conflict():
    with tempfile.TemporaryDirectory() as directory:
        agent = CharacterAgent(
            cartridge_path=str(CART),
            user_id="repair-reflection",
            db_path=os.path.join(directory, "state.db"),
        )
        agent.say("You lied to me. This is your fault.")
        agent.say("You lied to me again. This is your fault too.")
        assert agent.engine.relationship.unresolved_conflict == 0.2
        agent.say("I was wrong. I'm sorry.")
        assert agent.engine.relationship.unresolved_conflict == 0.0
        assert sum(1 for memory in agent.engine.memory.memories if memory.unresolved) >= 2
        assert "reflective_pattern" not in agent.engine.ledger.earned_traits

        agent.engine.energy = 0.1
        agent.engine.last_reflection_time = 0.0
        agent.engine._trigger_reflection(time.time() + 1_000.0)

        assert "reflective_pattern" not in agent.engine.ledger.earned_traits


def test_grounded_live_memory_is_visible_in_ordinary_followup_question():
    with tempfile.TemporaryDirectory() as directory:
        agent = CharacterAgent(
            cartridge_path=str(CART),
            user_id="live-grounding",
            db_path=os.path.join(directory, "state.db"),
        )
        agent.say("The workshop door is saffron today.")
        result = agent.say("What about the workshop door?")

        assert any("saffron" in item["content"].lower() for item in result["retrieved_memory_trace"])
        assert "saffron" in result["response"].lower()


def test_unrelated_live_memory_is_not_rendered_as_recollection():
    with tempfile.TemporaryDirectory() as directory:
        agent = CharacterAgent(
            cartridge_path=str(CART),
            user_id="live-negative",
            db_path=os.path.join(directory, "state.db"),
        )
        agent.say("The workshop door is saffron today.")
        result = agent.say("What about the harbor telescope?")

        assert "saffron" not in result["response"].lower()


def test_anchorless_question_does_not_turn_background_memory_into_recollection():
    with tempfile.TemporaryDirectory() as directory:
        agent = CharacterAgent(
            cartridge_path=str(CART),
            user_id="live-anchorless",
            db_path=os.path.join(directory, "state.db"),
        )
        agent.say("The workshop door is saffron today.")
        result = agent.say("What about it?")

        assert "saffron" not in result["response"].lower()
