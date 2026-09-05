from persona_engine.duck.services import ReplayServiceRegistry
from persona_engine.duck.types import CognitiveItem, CycleTrace


def test_recorded_service_proposals_can_be_replayed_without_model_call():
    proposal = CognitiveItem(
        item_id="model:0",
        tick=0,
        kind="interpretation_hypothesis",
        source_module="llm_service",
        subject_id="s",
        payload={"meaning": "maybe"},
        provenance={"model": "captured"},
        canonical=False,
    ).to_dict()
    trace = CycleTrace(
        tick=0, trigger={}, situation_changes={}, drive_changes={}, cognitive_items=(), broadcast=None,
        action_candidates=(), simulations=(), selected_intention=None, outcome=None, prediction=None, patches=(),
        service_proposals=(proposal,),
    )
    registry = ReplayServiceRegistry.from_traces([trace])
    items, errors = registry.proposals(type("Context", (), {"tick": 0, "subject_id": "s"})())
    assert errors == []
    assert items[0].item_id == "model:0"
    assert items[0].provenance["model"] == "captured"
