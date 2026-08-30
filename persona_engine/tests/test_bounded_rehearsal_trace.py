from persona_engine.core.memory import (
    MemoryStore, MemoryUnit, REHEARSAL_TRACE_WIDTH, activation,
)


def test_rehearsal_trace_saturates_at_workspace_width():
    store = MemoryStore()
    memory = MemoryUnit(content="The workshop door is saffron.", created_at=1.0)
    store.add(memory)
    for index in range(100):
        store.retrieve("workshop saffron door", now=100.0 + index, top_k=1)
    assert len(memory.recall_times) == REHEARSAL_TRACE_WIDTH
    assert memory.recall_times == [196.0, 197.0, 198.0, 199.0]


def test_rehearsal_still_strengthens_memory_before_saturation():
    recalled = MemoryUnit(content="The cobalt lighthouse lens.", created_at=1.0)
    plain = MemoryUnit(content="The cobalt lighthouse lens.", created_at=1.0)
    before = activation(recalled, now=100.0)
    recalled.record_recall(90.0)
    recalled.record_recall(95.0)
    assert activation(recalled, now=100.0) > before
    assert activation(recalled, now=100.0) > activation(plain, now=100.0)


def test_legacy_oversized_rehearsal_trace_compacts_on_load_object_creation():
    legacy = MemoryUnit(
        content="legacy",
        created_at=1.0,
        recall_times=[float(i) for i in range(1000)],
    )
    assert len(legacy.recall_times) == REHEARSAL_TRACE_WIDTH
    assert legacy.recall_times == [996.0, 997.0, 998.0, 999.0]


def test_non_numeric_legacy_rehearsal_entries_fail_closed_without_growth():
    legacy = MemoryUnit(
        content="legacy",
        created_at=1.0,
        recall_times=[1.0, "bad", None, 2.0, 3.0, 4.0, 5.0],
    )
    assert legacy.recall_times == [2.0, 3.0, 4.0, 5.0]
    assert len(legacy.recall_times) <= REHEARSAL_TRACE_WIDTH
