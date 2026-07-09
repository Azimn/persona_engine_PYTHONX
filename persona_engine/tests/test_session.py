"""Tests for session snapshot checksum import and export."""

import pytest
from persona_engine.core.belief_ledger import BeliefLedger
from persona_engine.core.emotion import PressureSystem, EmotionalPressure
from persona_engine.core.session import export_snapshot, import_snapshot, snapshot_from_json, snapshot_to_json, SessionImportError

BELIEFS = [{"id":"trust", "initial":0.0, "min":-1.0, "max":1.0, "decay_rate":0.0, "description":"trust"}]


def make_state():
    ps = PressureSystem()
    ps.add(EmotionalPressure("shame", 0.7))
    led = BeliefLedger(BELIEFS)
    led.records["trust"].value = 0.4
    return ps, led


def test_snapshot_round_trip():
    ps, led = make_state()
    snap = export_snapshot(ps, led, "Klaus")
    loaded = snapshot_from_json(snapshot_to_json(snap))
    ps2 = PressureSystem()
    led2 = BeliefLedger(BELIEFS)
    import_snapshot(loaded, ps2, led2, "Klaus")
    assert ps2.pressures["shame"].magnitude == 0.7
    assert led2.get("trust") == 0.4


def test_checksum_mismatch_detection():
    ps, led = make_state()
    snap = export_snapshot(ps, led, "Klaus")
    snap.beliefs["trust"] = 0.9
    with pytest.raises(SessionImportError, match="checksum"):
        import_snapshot(snap, ps, led, "Klaus")


def test_entity_mismatch_detection():
    ps, led = make_state()
    snap = export_snapshot(ps, led, "Klaus")
    with pytest.raises(SessionImportError, match="does not match"):
        import_snapshot(snap, ps, led, "Other")
