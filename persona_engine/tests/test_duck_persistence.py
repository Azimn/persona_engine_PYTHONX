from persona_engine.duck.motivation import DriveSystem
from persona_engine.duck.organism import DuckOrganism
from persona_engine.duck.persistence import DuckPersistence
from persona_engine.duck.replay import ReplayTape
from persona_engine.duck.types import DriveState, ExternalEvent


class FakeSubject:
    subject_id = "persistent-subject"
    def snapshot(self): return {"subject_id": self.subject_id}
    def observe_event(self, payload): return None
    def advance_time(self, elapsed_seconds): return {"elapsed": elapsed_seconds}


def factory():
    return DuckOrganism(
        FakeSubject(),
        organism_id="fixed-organism",
        drives=DriveSystem({"certainty": DriveState(name="certainty", target=0.0, level=0.0, decay_per_tick=0.0)}),
    )


def test_checkpoint_roundtrip_preserves_subject_and_digest(tmp_path):
    store = DuckPersistence(tmp_path / "duck")
    organism = factory()
    organism.persistence = store
    organism.ingest(ExternalEvent("e", "observation", {"salience": 0.4}, "test", 1.0))
    organism.step()

    loaded = store.load()
    assert loaded.subject_id == "persistent-subject"
    assert loaded.organism_id == "fixed-organism"
    assert DuckPersistence.digest_state(loaded) == DuckPersistence.digest_state(organism.current_state())
    assert store.event_log_path.read_text(encoding="utf-8").count("\n") == 1


def test_external_event_replay_is_deterministic():
    tape = ReplayTape()
    tape.record(ExternalEvent(
        "e",
        "observation",
        {
            "salience": 0.9,
            "action_candidates": [{
                "action_id": "inspect-box",
                "action_type": "inspect",
                "expected_world_effects": {"knowledge": 0.5},
                "expected_self_effects": {},
            }],
        },
        "test",
        1.0,
    ))

    assert tape.replay_digest(factory) == tape.replay_digest(factory)
