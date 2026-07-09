"""Tests for slow evidence-gated belief drift."""

from persona_engine.core.belief_ledger import BeliefLedger

BELIEFS = [
    {"id":"trust", "initial":0.0, "min":-1.0, "max":1.0, "decay_rate":0.01, "description":"trust"},
    {"id":"fixed", "initial":1.0, "min":0.0, "max":1.0, "decay_rate":0.01, "description":"fixed", "fixed": True},
]
RULES = [
    {"belief_id":"trust", "trigger_memory_type":"repair", "threshold_count":2, "delta":0.2},
    {"belief_id":"fixed", "trigger_memory_type":"repair", "threshold_count":2, "delta":-0.5},
]


def test_decay_over_time():
    led = BeliefLedger(BELIEFS)
    led.records["trust"].value = 0.5
    led.apply_decay(10)
    assert 0.39 <= led.get("trust") <= 0.41


def test_rule_fires():
    led = BeliefLedger(BELIEFS)
    changed = led.evaluate_rules(RULES, {"repair": 2})
    assert "trust" in changed
    assert led.get("trust") == 0.2


def test_rule_does_not_meet_threshold():
    led = BeliefLedger(BELIEFS)
    assert led.evaluate_rules(RULES, {"repair": 1}) == []
    assert led.get("trust") == 0.0


def test_fixed_belief_resists_rule():
    led = BeliefLedger(BELIEFS)
    led.evaluate_rules(RULES, {"repair": 2})
    assert led.get("fixed") == 1.0
