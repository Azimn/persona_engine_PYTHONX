from persona_engine.duck.motivation import DriveSystem
from persona_engine.duck.organism import DuckOrganism
from persona_engine.duck.simulation import RuleWorldModel
from persona_engine.duck.types import DriveState, ExternalEvent, ProspectiveCommitment


class FakeSubject:
    subject_id = "duck-subject"

    def __init__(self):
        self.observed = []
        self.elapsed = 0.0

    def snapshot(self):
        return {"subject_id": self.subject_id, "observed": len(self.observed)}

    def observe_event(self, payload):
        self.observed.append(dict(payload))
        return {"accepted": True}

    def advance_time(self, elapsed_seconds):
        self.elapsed += float(elapsed_seconds)
        return {"elapsed": self.elapsed}


def urgent_certainty():
    return DriveSystem({
        "certainty": DriveState(
            name="certainty",
            target=1.0,
            level=0.0,
            urgency=0.8,
            persistence=1.0,
            decay_per_tick=0.0,
        )
    })


def test_complete_cycle_broadcasts_simulates_intends_acts_compares_and_learns():
    subject = FakeSubject()
    organism = DuckOrganism(subject, organism_id="organism", drives=urgent_certainty())
    organism.ingest(ExternalEvent(
        event_id="e1",
        kind="observation",
        payload={"salience": 0.05, "self_relevance": 0.0, "description": "A quiet room"},
        source="test",
        timestamp=1.0,
    ))

    trace = organism.step()

    assert trace is not None
    assert trace.broadcast["winner"]["kind"] == "drive_signal"
    assert trace.selected_intention["action"]["action_type"] == "seek_information"
    assert trace.prediction["world_error"] == 0.0
    assert trace.prediction["self_error"] == 0.0
    assert organism.current_state().tick == 1
    assert organism.current_state().working_memory[-1]["kind"] == "drive_signal"
    assert organism.drives.drives["certainty"].level > 0.0
    assert subject.elapsed == 1.0
    assert organism.metacognitive_report()["latest_prediction"] is not None


def test_due_commitment_can_start_cycle_without_external_prompt():
    subject = FakeSubject()
    neutral = DriveSystem({
        "certainty": DriveState(name="certainty", target=0.0, level=0.0, urgency=0.0, decay_per_tick=0.0)
    })
    organism = DuckOrganism(subject, organism_id="organism", drives=neutral)
    organism.add_commitment(ProspectiveCommitment(
        commitment_id="check-sarah",
        kind="follow_up",
        target="Sarah",
        due_tick=0,
    ))

    trace = organism.step()

    assert trace.trigger["kind"] == "internal_commitment_due"
    assert trace.selected_intention["action"]["action_type"] == "honor_commitment"
    assert organism.current_state().commitments[0].status == "completed"


def test_prediction_error_changes_world_model_reliability():
    subject = FakeSubject()
    world = RuleWorldModel()
    organism = DuckOrganism(subject, organism_id="organism", drives=urgent_certainty(), world_model=world)
    organism.ingest(ExternalEvent("e1", "observation", {"salience": 0.01}, "test", 1.0))
    world.set_outcome_override("seek_information", {"progress": -0.5}, {"drive:certainty": 0.0})

    trace = organism.step()

    assert trace.prediction["world_error"] > 0.0
    assert trace.prediction["self_error"] > 0.0
    assert world.reliability["seek_information"] < 0.55
