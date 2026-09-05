from persona_engine.duck.organism import DuckOrganism
from persona_engine.duck.services import ServiceRegistry
from persona_engine.duck.types import CognitiveItem, DriveState, ExternalEvent
from persona_engine.duck.motivation import DriveSystem


class FakeSubject:
    subject_id = "subject"
    def snapshot(self): return {"subject_id": self.subject_id}
    def observe_event(self, payload): return None
    def advance_time(self, elapsed_seconds): return {"elapsed": elapsed_seconds}


class IllegalCanonicalService:
    service_name = "bad-model"
    def propose(self, context):
        return [CognitiveItem(
            item_id="illegal",
            tick=context.tick,
            kind="hypothesis",
            source_module="llm",
            subject_id=context.subject_id,
            payload={"claim": "I changed identity"},
            canonical=True,
        )]


class UsefulNoncanonicalService:
    service_name = "semantic-helper"
    def propose(self, context):
        return [CognitiveItem(
            item_id="proposal",
            tick=context.tick,
            kind="hypothesis",
            source_module="llm",
            subject_id=context.subject_id,
            payload={"interpretation": "possible opportunity"},
            confidence=0.7,
            salience=0.9,
            self_relevance=0.9,
            provenance={"model": "fake"},
            canonical=False,
        )]


def neutral_drives():
    return DriveSystem({"certainty": DriveState(name="certainty", target=0.0, level=0.0, decay_per_tick=0.0)})


def test_illegal_canonical_service_output_is_rejected_without_collapsing_cycle():
    organism = DuckOrganism(FakeSubject(), organism_id="o", drives=neutral_drives(), services=ServiceRegistry([IllegalCanonicalService()]))
    organism.ingest(ExternalEvent("e", "observation", {"salience": 0.1}, "test", 0.0))
    trace = organism.step()

    assert trace is not None
    assert trace.service_errors
    assert "canonical proposal" in trace.service_errors[0]
    assert all(item["item_id"] != "illegal" for item in trace.cognitive_items)


def test_noncanonical_service_proposal_can_compete_for_broadcast():
    organism = DuckOrganism(FakeSubject(), organism_id="o", drives=neutral_drives(), services=ServiceRegistry([UsefulNoncanonicalService()]))
    organism.ingest(ExternalEvent("e", "observation", {"salience": 0.1}, "test", 0.0))
    trace = organism.step()

    assert trace.broadcast["winner"]["item_id"] == "proposal"
    assert trace.broadcast["winner"]["canonical"] is False
