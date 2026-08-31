"""Semantic resident-memory policy regressions."""

from persona_engine.core.memory import KnowledgeSource, MemoryStore, MemoryUnit
from persona_engine.core.memory_policy import POLICY_VERSION, apply_resident_memory_policy
from persona_engine.core.relationship import RelationshipState


def _memory(source: KnowledgeSource, created_at: float, *, unresolved: bool = False, relationship_relevance: float = 0.0, token: str = "x") -> MemoryUnit:
    return MemoryUnit(
        content=f"I remember {token}",
        created_at=created_at,
        id=f"{source.value}-{token}",
        unresolved=unresolved,
        relationship_relevance=relationship_relevance,
        emotional_intensity=0.8 if unresolved else 0.1,
        source=source,
    )


def test_semantic_policy_never_converts_non_user_sources_into_a_numeric_budget():
    store = MemoryStore()
    relationship = RelationshipState(user_id="alice")
    relationship.unresolved_conflict = 0.6

    # Older neutral autobiography is recoverable from canonical input history.
    for index in range(10):
        store.add(_memory(KnowledgeSource.USER_TOLD, float(index + 1), token=f"neutral-{index}"))
    active = _memory(
        KnowledgeSource.USER_TOLD,
        50.0,
        unresolved=True,
        relationship_relevance=0.9,
        token="active-conflict",
    )
    store.add(active)

    pinned = [
        _memory(KnowledgeSource.OBSERVED, 20.0, token="observation"),
        _memory(KnowledgeSource.REFLECTION, 21.0, token="reflection"),
        _memory(KnowledgeSource.INFERRED, 22.0, token="inferred"),
        _memory(KnowledgeSource.CORE_IDENTITY, 23.0, token="identity"),
    ]
    for memory in pinned:
        store.add(memory)

    report = apply_resident_memory_policy(store, relationship)
    resident_ids = {memory.id for memory in store.memories}

    assert report["policy"] == POLICY_VERSION
    assert report["numeric_capacity"] is None
    assert active.id in resident_ids
    assert all(memory.id in resident_ids for memory in pinned)
    assert report["pinned_non_user_told"] == {
        "core_identity": 1,
        "inferred": 1,
        "observed": 1,
        "reflection": 1,
    }
    # At least one old USER_TOLD row must have been evicted, but the test does
    # not bless the resulting count as a universal capacity.
    assert report["user_told"]["evicted_user_told"] > 0


def test_repaired_history_does_not_keep_old_user_told_conflict_for_a_dead_causal_role():
    store = MemoryStore()
    relationship = RelationshipState(user_id="alice")
    relationship.unresolved_conflict = 0.0
    relationship.last_conflict_resolved_at = 100.0

    old_conflict = _memory(
        KnowledgeSource.USER_TOLD,
        50.0,
        unresolved=True,
        relationship_relevance=0.9,
        token="old-conflict",
    )
    store.add(old_conflict)
    for index in range(8):
        store.add(_memory(KnowledgeSource.USER_TOLD, 101.0 + index, token=f"recent-{index}"))
    observation = _memory(KnowledgeSource.OBSERVED, 40.0, token="old-observation")
    store.add(observation)

    apply_resident_memory_policy(store, relationship)
    resident_ids = {memory.id for memory in store.memories}

    assert old_conflict.id not in resident_ids
    assert observation.id in resident_ids
