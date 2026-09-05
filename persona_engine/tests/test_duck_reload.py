from persona_engine.duck.motivation import DriveSystem
from persona_engine.duck.organism import DuckOrganism
from persona_engine.duck.persistence import DuckPersistence
from persona_engine.duck.types import DriveState, ExternalEvent


class Subject:
    subject_id = "same-subject"
    def snapshot(self): return {}
    def observe_event(self, payload): return None
    def advance_time(self, elapsed_seconds): return {}


def test_duck_classmethod_load_restores_organism_without_changing_subject(tmp_path):
    store = DuckPersistence(tmp_path / "duck")
    organism = DuckOrganism(
        Subject(),
        organism_id="container",
        drives=DriveSystem({"certainty": DriveState(name="certainty", target=0.0, level=0.0, decay_per_tick=0.0)}),
        persistence=store,
    )
    organism.ingest(ExternalEvent("e", "observation", {"salience": 0.5}, "world", 1.0))
    organism.step()

    restored = DuckOrganism.load(Subject(), store)

    assert restored.current_state().subject_id == "same-subject"
    assert restored.current_state().organism_id == "container"
    assert restored.current_state().tick == organism.current_state().tick
