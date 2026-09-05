from persona_engine.agent import CharacterAgent
from persona_engine.core.identity import CoreIdentity
from persona_engine.duck.motivation import DriveSystem
from persona_engine.duck.organism import DuckOrganism
from persona_engine.duck.subject_adapter import WayfarerSubjectAdapter
from persona_engine.duck.types import DriveState, ExternalEvent


SUBJECT_UUID = "22222222-2222-4222-8222-222222222222"


def test_duck_uses_wayfarer_subject_without_replacing_subject_identity(tmp_path):
    identity = CoreIdentity(
        name="DuckSubject",
        core_beliefs=("Evidence matters.",),
        temperament="curious",
        entity_uuid=SUBJECT_UUID,
    )
    agent = CharacterAgent(identity, user_id="jay", db_path=str(tmp_path / "subject.db"))
    adapter = WayfarerSubjectAdapter(agent)
    organism = DuckOrganism(
        adapter,
        organism_id="runtime-container",
        drives=DriveSystem({"certainty": DriveState(name="certainty", target=0.0, level=0.0, decay_per_tick=0.0)}),
    )

    organism.ingest(ExternalEvent(
        event_id="cancelled",
        kind="observation",
        payload={
            "salience": 0.8,
            "observed_text": "Our planned meeting was cancelled.",
            "semantic_annotation": {
                "event_id": "cancelled",
                "event_type": "plan_change",
                "topic": "meeting",
                "interpersonal": 0.8,
                "goal_bearing": 0.7,
                "novelty": 0.5,
                "tags": ("cancellation",),
            },
        },
        source="scene",
        timestamp=10.0,
    ))
    trace = organism.step()

    assert adapter.subject_id == SUBJECT_UUID
    assert organism.current_state().subject_id == SUBJECT_UUID
    assert organism.current_state().organism_id == "runtime-container"
    assert trace.situation_changes["subject_observation"] is not None
    assert trace.situation_changes["subject_observation"]["memory_types"] == ["semantic_event", "subject_appraisal", "episodic"]
    assert agent.writer_status()["subject_uuid"] == SUBJECT_UUID
