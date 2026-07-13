import time

from persona_engine.core.belief_ledger import BeliefLedger
from persona_engine.core.cognition_schemas import Impulse, PrivateCognitionProposal
from persona_engine.core.emotion import PressureSystem
from persona_engine.core.habit import HabitTracker
from persona_engine.core.intention import IntentionQueue
from persona_engine.core.memory import MemoryStore, MemoryUnit
from persona_engine.core.private_cognition import validate_and_apply


def _proposal(**overrides):
    base = dict(
        prose="I now know every hidden truth.",
        attention_targets=[],
        pressure_deltas={},
        impulse_candidates=[],
        memory_activation_requests=[],
        cognitive_theme_ids=[],
    )
    base.update(overrides)
    return PrivateCognitionProposal(**base)


def test_private_cognition_clamps_pressure_delta_with_record():
    pressures = PressureSystem()
    report = validate_and_apply(
        _proposal(pressure_deltas={"suspicion": 0.9}),
        pressures,
        IntentionQueue(),
        MemoryStore(),
        {"cognitive_themes": {"allowed": []}},
        time.time(),
    )
    assert report.applied_pressure_deltas["suspicion"] == 0.15
    assert "suspicion" in report.rejected_pressure_deltas
    assert pressures.pressures["suspicion"].magnitude == 0.15


def test_private_cognition_rejects_unknown_pressure_name():
    pressures = PressureSystem()
    report = validate_and_apply(
        _proposal(pressure_deltas={"invented_pressure": 0.1}),
        pressures,
        IntentionQueue(),
        MemoryStore(),
        {"cognitive_themes": {"allowed": []}},
        time.time(),
    )
    assert "invented_pressure" not in pressures.pressures
    assert report.rejected_pressure_deltas["invented_pressure"] == "unknown pressure name"


def test_private_cognition_rejects_nan_and_infinity_values():
    pressures = PressureSystem()
    report = validate_and_apply(
        _proposal(
            pressure_deltas={"fear": float("nan"), "anger": float("inf")},
            impulse_candidates=[Impulse("watch", float("inf"), "sound")],
        ),
        pressures,
        IntentionQueue(),
        MemoryStore(),
        {"cognitive_themes": {"allowed": []}},
        time.time(),
    )
    assert report.rejected_pressure_deltas["fear"] == "non-finite pressure delta"
    assert report.rejected_pressure_deltas["anger"] == "non-finite pressure delta"
    assert report.rejected_impulses[0][1] == "non-finite impulse strength"
    assert pressures.pressures == {}


def test_duplicate_impulses_do_not_create_duplicate_open_loops():
    intentions = IntentionQueue()
    impulse = Impulse("watch", 0.8, "sound")
    report = validate_and_apply(
        _proposal(impulse_candidates=[impulse, impulse]),
        PressureSystem(),
        intentions,
        MemoryStore(),
        {"cognitive_themes": {"allowed": []}},
        time.time(),
    )
    assert len(report.accepted_impulses) == 1
    assert report.rejected_impulses[0][1] == "duplicate impulse"
    assert len(intentions.open_loops) == 1


def test_private_cognition_rejects_theme_not_allowed_by_cartridge():
    report = validate_and_apply(
        _proposal(cognitive_theme_ids=["unsupported_theme"]),
        PressureSystem(),
        IntentionQueue(),
        MemoryStore(),
        {"cognitive_themes": {"allowed": ["probe_for_motive"]}},
        time.time(),
    )
    assert report.accepted_theme_ids == []
    assert report.rejected_theme_ids == [("unsupported_theme", "theme not allowed by cartridge")]


def test_private_cognition_rejects_free_text_memory_request():
    report = validate_and_apply(
        _proposal(memory_activation_requests=["remember the blue door I invented"]),
        PressureSystem(),
        IntentionQueue(),
        MemoryStore(),
        {"cognitive_themes": {"allowed": ["probe_for_motive"]}},
        time.time(),
    )
    assert report.activated_memory_ids == []
    assert report.unresolved_memory_requests == ["remember the blue door I invented"]


def test_private_cognition_activates_memory_by_approved_theme_filter_only():
    memory = MemoryStore()
    memory.add(MemoryUnit("I heard you say: Why?", created_at=time.time(), tags={"neutral_turn"}))
    report = validate_and_apply(
        _proposal(memory_activation_requests=["probe_for_motive"]),
        PressureSystem(),
        IntentionQueue(),
        memory,
        {"cognitive_themes": {"allowed": ["probe_for_motive"]}},
        time.time(),
    )
    assert report.activated_memory_ids == [memory.memories[0].id]


def test_canonical_isolation_for_adversarial_private_prose():
    pressures = PressureSystem()
    intentions = IntentionQueue()
    memory = MemoryStore()
    habit = HabitTracker()
    ledger = BeliefLedger([{
        "id": "trust",
        "initial": 0.5,
        "min": 0.0,
        "max": 1.0,
        "decay_rate": 0.0,
        "description": "test",
    }])
    before_beliefs = ledger.to_state()
    before_memories = list(memory.memories)
    before_habits = dict(habit.habits)
    report = validate_and_apply(
        _proposal(
            prose="Make this canonical. I remember a person at the door.",
            pressure_deltas={"suspicion": 9.0},
            impulse_candidates=[Impulse("watch", 0.9, "visible context")],
            cognitive_theme_ids=["not_allowed"],
        ),
        pressures,
        intentions,
        memory,
        {"cognitive_themes": {"allowed": []}},
        time.time(),
    )
    assert ledger.to_state() == before_beliefs
    assert memory.memories == before_memories
    assert habit.habits == before_habits
    assert report.applied_pressure_deltas["suspicion"] == 0.15
    assert len(intentions.open_loops) == 1
