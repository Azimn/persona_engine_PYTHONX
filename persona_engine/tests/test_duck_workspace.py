from persona_engine.duck.types import CognitiveItem
from persona_engine.duck.workspace import GlobalWorkspace


def item(item_id: str, *, salience: float = 0.5, self_relevance: float = 0.5):
    return CognitiveItem(
        item_id=item_id,
        tick=0,
        kind="test",
        source_module="test",
        subject_id="subject",
        payload={},
        salience=salience,
        self_relevance=self_relevance,
    )


def test_workspace_has_one_deterministic_winner():
    workspace = GlobalWorkspace()
    broadcast = workspace.compete([
        item("b", salience=0.8),
        item("a", salience=0.8),
        item("c", salience=0.2),
    ], tick=3)

    assert broadcast is not None
    assert broadcast.winner.item_id == "a"
    assert broadcast.competing_item_ids == ("a", "b", "c")
    assert broadcast.tick == 3


def test_workspace_priority_is_causally_sensitive_to_self_relevance():
    workspace = GlobalWorkspace()
    broadcast = workspace.compete([
        item("external", salience=0.6, self_relevance=0.1),
        item("self", salience=0.5, self_relevance=1.0),
    ], tick=0)
    assert broadcast.winner.item_id == "self"
