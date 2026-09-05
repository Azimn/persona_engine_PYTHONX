from persona_engine.duck.attribution import AttributionBridge
from persona_engine.duck.types import ExternalEvent


def test_attribution_separates_agency_from_mineness():
    bridge = AttributionBridge()
    acted = bridge.attribute(
        ExternalEvent(
            "e1",
            "observation",
            {"actor_subject_id": "s", "target_subject_id": "other"},
            "world",
            1.0,
        ),
        subject_id="s",
        tick=0,
    )
    received = bridge.attribute(
        ExternalEvent(
            "e2",
            "observation",
            {"actor_subject_id": "other", "target_subject_id": "s"},
            "world",
            1.0,
        ),
        subject_id="s",
        tick=0,
    )

    assert acted.agency > received.agency
    assert received.mineness > acted.mineness
    assert acted.autobiographical_belonging > 0.0
    assert received.autobiographical_belonging > 0.0


def test_internal_event_has_high_mineness_without_claiming_high_causal_agency():
    frame = AttributionBridge().attribute(
        ExternalEvent("e", "internal_drive", {"modality": "internal"}, "scheduler", 0.0),
        subject_id="s",
        tick=4,
    )
    assert frame.mineness >= 0.9
    assert frame.agency < 0.5
