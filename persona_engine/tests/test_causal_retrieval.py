from persona_engine.core.causal_retrieval import expand_causal_neighbors


def _event(event_uuid, sequence, *, parents=(), subject_uuid="subject-a", event_type="input", canonicality="canonical_event"):
    return {
        "event_uuid": event_uuid,
        "subject_uuid": subject_uuid,
        "subject_sequence": sequence,
        "event_type": event_type,
        "canonicality": canonicality,
        "causal_parents": list(parents),
        "payload": {},
    }


def test_direct_parent_is_recovered_without_recursive_traversal():
    events = [
        _event("cause", 1, event_type="world_fact"),
        _event("seed", 2, parents=("cause",)),
        _event("grandparent", 0),
    ]
    result = expand_causal_neighbors(events, ["seed"], max_neighbors=4)
    assert [item.event_uuid for item in result] == ["cause"]
    assert result[0].relation == "parent"


def test_direct_child_is_recovered():
    events = [
        _event("seed", 1),
        _event("effect", 2, parents=("seed",), event_type="world_fact"),
    ]
    result = expand_causal_neighbors(events, ["seed"], max_neighbors=4)
    assert [item.event_uuid for item in result] == ["effect"]
    assert result[0].relation == "child"


def test_expansion_is_one_hop_only():
    events = [
        _event("a", 1),
        _event("b", 2, parents=("a",)),
        _event("c", 3, parents=("b",)),
    ]
    result = expand_causal_neighbors(events, ["c"], max_neighbors=4)
    assert [item.event_uuid for item in result] == ["b"]


def test_cross_subject_links_fail_closed():
    events = [
        _event("foreign", 1, subject_uuid="subject-b"),
        _event("seed", 2, parents=("foreign",), subject_uuid="subject-a"),
    ]
    assert expand_causal_neighbors(events, ["seed"], max_neighbors=4) == []


def test_noncanonical_neighbor_is_not_returned():
    events = [
        _event("diagnostic", 1, canonicality="noncanonical"),
        _event("seed", 2, parents=("diagnostic",)),
    ]
    assert expand_causal_neighbors(events, ["seed"], max_neighbors=4) == []


def test_neighbor_budget_is_deterministic_and_bounded():
    events = [
        _event("parent-old", 1),
        _event("parent-new", 5),
        _event("seed", 6, parents=("parent-old", "parent-new")),
        _event("child", 7, parents=("seed",)),
    ]
    result = expand_causal_neighbors(events, ["seed"], max_neighbors=2)
    assert [item.event_uuid for item in result] == ["parent-new", "parent-old"]
    assert len(result) == 2
