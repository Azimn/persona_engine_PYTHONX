"""Contracts for Long Sleep null consolidation and reflection checkpoints."""

from __future__ import annotations

import os
import tempfile
import time
from pathlib import Path

from persona_engine.agent import CharacterAgent
from persona_engine.core.belief_ledger import BeliefLedger
from persona_engine.core.dream_engine import DreamEngine
from persona_engine.core.memory import KnowledgeSource, MemoryUnit
from persona_engine.core.persistence import Persistence


ROOT = Path(__file__).resolve().parents[1]
PRET = ROOT / "cartridges" / "pretorius.snp"

BELIEFS = [
    {"id": "trust", "initial": 0.0, "min": -1.0, "max": 1.0, "decay_rate": 0.0, "description": "trust"},
    {"id": "fixed", "initial": 1.0, "min": 0.0, "max": 1.0, "decay_rate": 0.0, "description": "fixed", "fixed": True},
]
RULES = [
    {"belief_id": "trust", "trigger_memory_type": "repair", "threshold_count": 2, "delta": 0.25},
    {"belief_id": "fixed", "trigger_memory_type": "repair", "threshold_count": 2, "delta": -0.50},
]


def _dream():
    tempdir = tempfile.TemporaryDirectory()
    persistence = Persistence(os.path.join(tempdir.name, "state.db"))
    ledger = BeliefLedger(BELIEFS)
    return tempdir, persistence, ledger, DreamEngine(persistence, ledger)


def test_run_idle_pass_returns_empty_when_minimum_interval_has_not_elapsed():
    tempdir, persistence, ledger, dream = _dream()
    try:
        ledger.last_consolidated = time.time()
        persistence.log_event("C", "u", 1, "turn", {"memory_types": ["repair", "repair"]})

        changed = dream.run_idle_pass("C", "u", RULES, min_interval_seconds=3600)

        assert changed == []
        assert ledger.values == {"trust": 0.0, "fixed": 1.0}
    finally:
        tempdir.cleanup()


def test_null_consolidation_updates_checkpoint_without_belief_value_change():
    tempdir, persistence, ledger, dream = _dream()
    try:
        before_values = dict(ledger.values)
        before_checkpoint = ledger.last_consolidated
        persistence.log_event("C", "u", 1, "turn", {"memory_types": ["neutral_turn"]})

        changed = dream.consolidate("C", "u", RULES)

        assert changed == []
        assert ledger.values == before_values
        assert ledger.last_consolidated > before_checkpoint
    finally:
        tempdir.cleanup()


def test_fixed_belief_records_do_not_mutate_even_when_rules_match():
    tempdir, persistence, ledger, dream = _dream()
    try:
        persistence.log_event("C", "u", 1, "turn", {"memory_types": ["repair"]})
        persistence.log_event("C", "u", 2, "turn", {"memory_types": ["repair"]})

        changed = dream.consolidate("C", "u", RULES)

        assert changed == ["trust"]
        assert ledger.get("trust") == 0.25
        assert ledger.get("fixed") == 1.0
    finally:
        tempdir.cleanup()


def test_reflection_low_confidence_does_not_mutate_belief_ledger(tmp_path):
    agent = CharacterAgent(cartridge_path=str(PRET), user_id="reflect", db_path=str(tmp_path / "state.db"))
    before_values = dict(agent.engine.belief_ledger.values)
    agent.engine.memory.add(MemoryUnit(
        content="User made a low-salience ordinary remark.",
        created_at=time.time(),
        source=KnowledgeSource.USER_TOLD,
        emotional_intensity=0.0,
        relationship_relevance=0.0,
        identity_relevance=0.0,
        unresolved=False,
    ))

    agent.engine._trigger_reflection(time.time() + 301)

    assert agent.engine.belief_ledger.values == before_values
