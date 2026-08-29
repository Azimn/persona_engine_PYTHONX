"""Body sensorium should represent transitions, not polling frequency."""

from persona_engine.core.body import BodyProfile, BodyState
from persona_engine.core.sensorium import SensoriumProcessor


def test_persistent_depleted_state_is_not_reemitted_as_new_event_every_poll():
    profile = BodyProfile()
    body = BodyState.from_profile(profile)
    sensorium = SensoriumProcessor()

    before = body.to_dict()
    body.fatigue = 0.90
    body.recovery_state = "depleted"
    first = sensorium.derive_from_body(body, 100.0, previous_body_state=before)
    assert any(event.kind == "body_state" for event in first)

    unchanged = body.to_dict()
    second = sensorium.derive_from_body(body, 105.0, previous_body_state=unchanged)
    assert not any(event.kind == "body_state" for event in second)


def test_recovery_then_reentry_creates_a_new_body_event():
    profile = BodyProfile()
    body = BodyState.from_profile(profile)
    sensorium = SensoriumProcessor()

    stable = body.to_dict()
    body.fatigue = 0.90
    body.recovery_state = "depleted"
    assert any(event.kind == "body_state" for event in sensorium.derive_from_body(body, 100.0, previous_body_state=stable))

    depleted = body.to_dict()
    body.fatigue = 0.0
    body.recovery_state = "stable"
    sensorium.derive_from_body(body, 200.0, previous_body_state=depleted)

    recovered = body.to_dict()
    body.fatigue = 0.95
    body.recovery_state = "depleted"
    third = sensorium.derive_from_body(body, 300.0, previous_body_state=recovered)
    assert any(event.kind == "body_state" for event in third)


def test_threshold_channels_emit_only_when_crossing_into_notable_range():
    profile = BodyProfile()
    body = BodyState.from_profile(profile)
    sensorium = SensoriumProcessor()

    before = body.to_dict()
    body.sensory_load = 0.80
    body.need_for_movement = 0.80
    events = sensorium.derive_from_body(body, 100.0, previous_body_state=before)
    kinds = {event.kind for event in events}
    assert "sensory_load" in kinds
    assert "movement_need" in kinds

    same = body.to_dict()
    events = sensorium.derive_from_body(body, 105.0, previous_body_state=same)
    assert not events
