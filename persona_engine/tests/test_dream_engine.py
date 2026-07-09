"""Tests for slow consolidation over new evidence only."""

import os
import time
import tempfile

from persona_engine.core.belief_ledger import BeliefLedger
from persona_engine.core.dream_engine import DreamEngine
from persona_engine.core.persistence import Persistence

BELIEFS = [{"id":"trust", "initial":0.0, "min":-1.0, "max":1.0, "decay_rate":0.0, "description":"trust"}]
RULES = [{"belief_id":"trust", "trigger_memory_type":"repair", "threshold_count":2, "delta":0.25}]


def make():
    d = tempfile.TemporaryDirectory()
    path = os.path.join(d.name, "state.db")
    p = Persistence(path)
    led = BeliefLedger(BELIEFS)
    return d, p, led, DreamEngine(p, led)


def test_rule_fires_from_new_events():
    d, p, led, dream = make()
    try:
        p.log_event("K", "u", 1, "turn", {"memory_types":["repair"]})
        p.log_event("K", "u", 2, "turn", {"memory_types":["repair"]})
        changed = dream.consolidate("K", "u", RULES)
        assert changed == ["trust"]
        assert led.get("trust") == 0.25
    finally:
        d.cleanup()


def test_does_not_double_count_old_events():
    d, p, led, dream = make()
    try:
        p.log_event("K", "u", 1, "turn", {"memory_types":["repair"]})
        p.log_event("K", "u", 2, "turn", {"memory_types":["repair"]})
        assert dream.consolidate("K", "u", RULES) == ["trust"]
        before = led.get("trust")
        assert dream.consolidate("K", "u", RULES) == []
        assert led.get("trust") == before
    finally:
        d.cleanup()


def test_idle_pass_interval_gate():
    d, p, led, dream = make()
    try:
        led.last_consolidated = time.time()
        p.log_event("K", "u", 1, "turn", {"memory_types":["repair", "repair"]})
        assert dream.run_idle_pass("K", "u", RULES, min_interval_seconds=3600) == []
    finally:
        d.cleanup()
