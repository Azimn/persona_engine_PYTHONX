import pytest

from persona_engine.duck.reducer import CanonicalReducer
from persona_engine.duck.types import OrganismState, StatePatch


def patch(source, domain, value):
    return StatePatch(domain, domain, None, value, source, "test", (), 0, "duck_internal")


def test_llm_or_unknown_module_cannot_write_canonical_organism_state():
    state = OrganismState("v", "o", "s")
    with pytest.raises(PermissionError):
        CanonicalReducer().apply(state, patch("llm_service", "active_goals", []))


def test_learning_can_write_only_learning_domains():
    state = OrganismState("v", "o", "s")
    reducer = CanonicalReducer()
    reducer.apply(state, patch("learning", "world_model_state", {"reliability": {"inspect": 0.8}}))
    assert state.world_model_state["reliability"]["inspect"] == 0.8
    with pytest.raises(PermissionError):
        reducer.apply(state, patch("learning", "commitments", []))
