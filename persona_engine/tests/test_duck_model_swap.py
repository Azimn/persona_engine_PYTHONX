from persona_engine.duck.motivation import DriveSystem
from persona_engine.duck.organism import DuckOrganism
from persona_engine.duck.services import ServiceRegistry
from persona_engine.duck.types import CognitiveItem, DriveState, ExternalEvent


class Subject:
    subject_id = "persistent"
    def snapshot(self): return {"identity": "same"}
    def observe_event(self, payload): return None
    def advance_time(self, elapsed_seconds): return {}


class Service:
    def __init__(self, name):
        self.service_name = name
    def propose(self, context):
        return [CognitiveItem(
            item_id=f"{self.service_name}:{context.tick}",
            tick=context.tick,
            kind="hypothesis",
            source_module="llm_service",
            subject_id=context.subject_id,
            payload={"service": self.service_name},
            salience=0.9,
            self_relevance=0.9,
            provenance={"provider": self.service_name},
            canonical=False,
        )]


def test_cognitive_service_swap_does_not_reset_subject_or_organism():
    organism = DuckOrganism(
        Subject(),
        organism_id="container",
        drives=DriveSystem({"certainty": DriveState(name="certainty", target=0.0, level=0.0, decay_per_tick=0.0)}),
        services=ServiceRegistry([Service("model-a")]),
    )
    subject_id = organism.current_state().subject_id
    organism_id = organism.current_state().organism_id
    organism.ingest(ExternalEvent("e1", "observation", {"salience": 0.1}, "world", 1.0))
    first = organism.step()

    organism.set_services(ServiceRegistry([Service("model-b")]))
    organism.ingest(ExternalEvent("e2", "observation", {"salience": 0.1}, "world", 2.0))
    second = organism.step()

    assert organism.current_state().subject_id == subject_id
    assert organism.current_state().organism_id == organism_id
    assert first.broadcast["winner"]["payload"]["service"] == "model-a"
    assert second.broadcast["winner"]["payload"]["service"] == "model-b"
