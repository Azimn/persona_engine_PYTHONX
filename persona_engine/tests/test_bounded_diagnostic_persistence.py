import json
import os
import sqlite3
import tempfile
import uuid

from persona_engine.agent import CharacterAgent
from persona_engine.core.belief_ledger import BeliefLedger
from persona_engine.core.dream_engine import DreamEngine
from persona_engine.core.persistence import (
    DEFAULT_RUNTIME_DIAGNOSTIC_EVENT_LIMIT,
    Persistence,
)


def _count(path, table):
    conn = sqlite3.connect(path)
    try:
        return int(conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0])
    finally:
        conn.close()


def test_direct_persistence_keeps_legacy_unlimited_diagnostics_by_default():
    with tempfile.TemporaryDirectory() as d:
        path = os.path.join(d, "state.db")
        p = Persistence(path)
        for index in range(600):
            p.log_event("K", "u", index, "diagnostic", {"memory_types": ["neutral"]})
        assert _count(path, "event_log") == 600
        assert _count(path, "consolidation_evidence") == 600


def test_bounded_diagnostics_do_not_bound_semantic_consolidation_evidence():
    with tempfile.TemporaryDirectory() as d:
        path = os.path.join(d, "state.db")
        p = Persistence(path, diagnostic_event_limit=3)
        p.bind_subject("K", "u", str(uuid.uuid4()))
        for index in range(10):
            p.log_event("K", "u", index, "turn", {"memory_types": ["repair"]})
        assert _count(path, "event_log") == 3
        assert _count(path, "consolidation_evidence") == 10
        assert p.event_counts_since("K", "u", 0.0)["repair"] == 10


def test_canonical_continuity_survives_diagnostic_pruning():
    with tempfile.TemporaryDirectory() as d:
        path = os.path.join(d, "state.db")
        p = Persistence(path, diagnostic_event_limit=3)
        p.bind_subject("K", "u", str(uuid.uuid4()))
        for index in range(10):
            p.log_event("K", "u", index, "input", {"user_text": f"event {index}", "memory_types": ["user_input"]})
        assert _count(path, "event_log") == 3
        assert len(p.load_continuity_events("K", "u")) == 10


def test_legacy_canonical_rows_are_backfilled_before_bounded_runtime_prunes_them():
    with tempfile.TemporaryDirectory() as d:
        path = os.path.join(d, "state.db")
        seed = Persistence(path)
        subject = str(uuid.uuid4())
        seed.bind_subject("K", "u", subject)
        conn = sqlite3.connect(path)
        try:
            for index in range(10):
                conn.execute(
                    "INSERT INTO event_log(character_id,user_id,timestep,event_type,payload,created_at) VALUES(?,?,?,?,?,?)",
                    ("K", "u", index, "input", json.dumps({"user_text": f"legacy {index}"}), float(index + 1)),
                )
            conn.commit()
        finally:
            conn.close()
        runtime = Persistence(path, diagnostic_event_limit=3)
        runtime.bind_subject("K", "u", subject)
        assert len(runtime.load_continuity_events("K", "u")) == 10
        assert _count(path, "event_log") == 3
        assert _count(path, "consolidation_evidence") == 10


def test_dream_engine_uses_compact_evidence_and_prunes_committed_window():
    beliefs = [{"id": "trust", "initial": 0.0, "min": -1.0, "max": 1.0, "decay_rate": 0.0, "description": "trust"}]
    rules = [{"belief_id": "trust", "trigger_memory_type": "repair", "threshold_count": 2, "delta": 0.25}]
    with tempfile.TemporaryDirectory() as d:
        path = os.path.join(d, "state.db")
        p = Persistence(path, diagnostic_event_limit=2)
        led = BeliefLedger(beliefs)
        dream = DreamEngine(p, led)
        for index in range(8):
            p.log_event("K", "u", index, "turn", {"memory_types": ["repair"]})
        assert _count(path, "event_log") == 2
        assert dream.consolidate("K", "u", rules) == ["trust"]
        assert led.get("trust") == 0.25
        assert _count(path, "consolidation_evidence") == 0
        assert dream.consolidate("K", "u", rules) == []


def test_character_runtime_uses_explicit_bounded_telemetry_profile():
    with tempfile.TemporaryDirectory() as d:
        cart = os.path.join(os.path.dirname(__file__), "..", "cartridges", "pretorius.snp")
        agent = CharacterAgent(cartridge_path=cart, user_id="u", db_path=os.path.join(d, "state.db"))
        assert agent.engine.persistence.diagnostic_event_limit == DEFAULT_RUNTIME_DIAGNOSTIC_EVENT_LIMIT == 512


def test_normal_runtime_pruning_is_amortized_but_stays_inside_operational_slack():
    with tempfile.TemporaryDirectory() as d:
        path = os.path.join(d, "state.db")
        p = Persistence(path, diagnostic_event_limit=512)
        p.bind_subject("K", "u", str(uuid.uuid4()))
        for index in range(2000):
            p.log_event("K", "u", index, "diagnostic", {"memory_types": ["neutral"]})
        retained = _count(path, "event_log")
        assert 512 <= retained < 512 + 128
        assert p._diagnostic_prune_stride() == 128
        assert _count(path, "consolidation_evidence") == 2000
