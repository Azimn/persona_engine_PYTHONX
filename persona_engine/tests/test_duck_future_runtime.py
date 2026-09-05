from persona_engine.duck.capabilities import CapabilityDescriptor, CapabilityRegistry
from persona_engine.duck.embodiment_port import Affordance, BodySnapshot, EmbodimentOutcome
from persona_engine.duck.future_runtime import FutureDuckRuntime, FutureRuntimeConfig
from persona_engine.duck.motivation import DriveSystem
from persona_engine.duck.timebase import TemporalAuthority, swatch_beat
from persona_engine.duck.types import CandidateAction, DriveState


class FakeSubject:
    subject_id = "future-duck"

    def __init__(self):
        self.elapsed = 0.0
        self.observed = []

    def snapshot(self):
        return {"subject_id": self.subject_id, "observed": len(self.observed)}

    def observe_event(self, payload):
        self.observed.append(dict(payload))
        return {"accepted": True}

    def advance_time(self, elapsed_seconds):
        self.elapsed += float(elapsed_seconds)
        return {"elapsed": self.elapsed}


class FakeBody:
    body_id = "pond-body"

    def __init__(self):
        self.pending = []
        self.executed = []

    def snapshot(self):
        return BodySnapshot(
            body_id=self.body_id,
            location="pond_north",
            orientation="east",
            sensors=("vision", "sound"),
            effectors=("seek_information", "communicate", "wait"),
            state={"energy": 0.8},
        )

    def observe(self, *, tick):
        del tick
        values, self.pending = self.pending, []
        return values

    def affordances(self):
        return [Affordance("seek_information"), Affordance("communicate"), Affordance("wait")]

    def supports(self, action_type):
        return action_type in self.snapshot().effectors

    def execute(self, action, simulation, context):
        del context
        self.executed.append(action.action_type)
        return EmbodimentOutcome(True, "body_executed", dict(simulation.predicted_world_effects), dict(simulation.predicted_self_effects))


def urgent_certainty():
    return DriveSystem({
        "certainty": DriveState(
            name="certainty", target=1.0, level=0.0, urgency=0.8,
            persistence=1.0, decay_per_tick=0.0,
        )
    })


def test_swatch_internet_time_uses_bmt_and_never_requires_host_clock():
    authority = TemporalAuthority()
    midnight_utc = 0.0
    stamp = authority.observe(midnight_utc, logical_tick=7)
    assert stamp.beat == 41.667
    assert stamp.logical_tick == 7
    assert stamp.utc_iso == "1970-01-01T00:00:00Z"
    assert swatch_beat(midnight_utc) == 41.667


def test_backward_civil_clock_is_diagnostic_not_negative_subject_time():
    authority = TemporalAuthority()
    authority.observe(200.0, logical_tick=1)
    stamp = authority.observe(150.0, logical_tick=2)
    assert stamp.clock_regression_seconds == 50.0
    assert stamp.logical_tick == 2


def test_future_runtime_routes_execution_through_replaceable_body():
    subject = FakeSubject()
    body = FakeBody()
    runtime = FutureDuckRuntime(subject, embodiment=body)
    runtime.organism.drives = urgent_certainty()
    runtime.organism.state.drive_state = runtime.organism.drives.drives
    runtime.organism.action_selector.drives = runtime.organism.drives
    runtime.ingest_observation({"description": "quiet pond", "salience": 0.01}, event_id="e1")
    trace = runtime.step()
    assert trace is not None
    assert trace.selected_intention["action"]["action_type"] == "seek_information"
    assert body.executed[-1] == "seek_information"
    assert runtime.subject_id == "future-duck"


def test_embodiment_sensor_events_enter_normal_cognitive_cycle():
    subject = FakeSubject()
    body = FakeBody()
    body.pending.append({"kind": "observation", "payload": {"description": "a splash", "salience": 0.7}})
    runtime = FutureDuckRuntime(subject, embodiment=body)
    trace = runtime.step()
    assert trace is not None
    assert trace.trigger["payload"]["description"] == "a splash"
    assert trace.trigger["payload"]["temporal_stamp"]["logical_tick"] == 0


def test_capability_registry_produces_execution_firewall():
    registry = CapabilityRegistry([
        CapabilityDescriptor("speak", "communicate", "body", requires_confirmation=False),
        CapabilityDescriptor("danger", "dangerous_action", "plugin", enabled=False),
    ])
    policy = registry.execution_policy()
    assert "communicate" in policy.allowed_actions
    assert "wait" in policy.allowed_actions
    assert "dangerous_action" in policy.denied_actions


def test_endogenous_reflection_can_open_private_cycle_without_direct_speech():
    subject = FakeSubject()
    runtime = FutureDuckRuntime(
        subject,
        runtime_config=FutureRuntimeConfig(endogenous_threshold=0.2, endogenous_cooldown_ticks=1),
    )
    runtime.organism.state.situation.unresolved.append("Why did the gate fail?")
    trace = runtime.step()
    assert trace is not None
    assert trace.trigger["kind"] == "internal_reflection"
    assert trace.trigger["payload"]["private"] is True
    assert runtime.organism.current_state().tick == 1


def test_explicit_civil_time_is_carried_as_memory_ready_event_metadata():
    subject = FakeSubject()
    runtime = FutureDuckRuntime(subject)
    event = runtime.observe_civil_time(0.0)
    assert event.payload["temporal_stamp"]["beat"] == 41.667
    assert event.payload["temporal_stamp"]["bmt_date"] == "1970-01-01"
