from persona_engine.duck.motivation import DriveSystem
from persona_engine.duck.organism import DuckOrganism
from persona_engine.duck.procedures import Procedure, ProcedureRegistry
from persona_engine.duck.types import DriveState, ExternalEvent


class Subject:
    subject_id = "s"
    def snapshot(self): return {}
    def observe_event(self, payload): return None
    def advance_time(self, elapsed_seconds): return {}


def test_procedural_affordance_can_generate_and_learn_from_action():
    procedure = Procedure(
        procedure_id="scan-novel",
        action_type="scan",
        trigger_kinds=("observation",),
        expected_world_effects={"knowledge": 0.6},
        confidence=0.7,
        risk=0.0,
        cost=0.0,
    )
    registry = ProcedureRegistry([procedure])
    organism = DuckOrganism(
        Subject(),
        organism_id="o",
        drives=DriveSystem({"certainty": DriveState(name="certainty", target=0.0, level=0.0, decay_per_tick=0.0)}),
        procedures=registry,
    )
    organism.ingest(ExternalEvent("e", "observation", {"salience": 0.9, "novelty": 0.9}, "world", 1.0))

    trace = organism.step()

    assert any(item["action_type"] == "scan" for item in trace.action_candidates)
    assert trace.selected_intention["action"]["action_type"] == "scan"
    assert registry.procedures["scan-novel"].confidence > 0.7
