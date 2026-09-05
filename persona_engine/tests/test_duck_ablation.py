from persona_engine.duck.motivation import DriveSystem
from persona_engine.duck.organism import DuckConfig, DuckOrganism
from persona_engine.duck.types import DriveState, ExternalEvent


class Subject:
    subject_id = "s"
    def snapshot(self): return {}
    def observe_event(self, payload): return None
    def advance_time(self, elapsed_seconds): return {}


def drives():
    return DriveSystem({
        "certainty": DriveState(name="certainty", target=1.0, level=0.0, urgency=0.9, persistence=1.0, decay_per_tick=0.0)
    })


def event():
    return ExternalEvent("e", "observation", {"salience": 0.05}, "world", 1.0)


def test_workspace_lesion_changes_downstream_action_selection():
    normal = DuckOrganism(Subject(), organism_id="normal", drives=drives())
    normal.ingest(event())
    normal_trace = normal.step()

    lesioned = DuckOrganism(
        Subject(),
        organism_id="lesioned",
        drives=drives(),
        config=DuckConfig(enable_workspace=False),
    )
    lesioned.ingest(event())
    lesioned_trace = lesioned.step()

    assert normal_trace.selected_intention["action"]["action_type"] == "seek_information"
    assert lesioned_trace.broadcast is None
    assert lesioned_trace.selected_intention["action"]["action_type"] == "wait"
    assert lesioned.metacognitive_report()["lesions"]["workspace"] is True


def test_motivation_lesion_prevents_drive_from_starting_endogenous_cycle():
    organism = DuckOrganism(
        Subject(),
        organism_id="o",
        drives=drives(),
        config=DuckConfig(enable_motivation=False),
    )
    assert organism.step() is None
