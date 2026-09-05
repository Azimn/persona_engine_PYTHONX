import time

from persona_engine.agent import CharacterAgent
from persona_engine.core.identity import CoreIdentity
from persona_engine.duck.motivation import DriveSystem
from persona_engine.duck.organism import DuckOrganism
from persona_engine.duck.subject_adapter import WayfarerSubjectAdapter
from persona_engine.duck.types import DriveState, ExternalEvent


def test_duck_activation_uses_wayfarer_memory_without_owning_it(tmp_path):
    identity = CoreIdentity(
        name="MemoryDuck",
        core_beliefs=("I keep evidence.",),
        temperament="calm",
        entity_uuid="44444444-4444-4444-8444-444444444444",
    )
    agent = CharacterAgent(identity, user_id="jay", db_path=str(tmp_path / "subject.db"))
    agent.say("The atlas cover is blue.")
    organism = DuckOrganism(
        WayfarerSubjectAdapter(agent),
        organism_id="o",
        drives=DriveSystem({"certainty": DriveState(name="certainty", target=0.0, level=0.0, decay_per_tick=0.0)}),
    )
    organism.ingest(ExternalEvent(
        "atlas",
        "observation",
        {"description": "I notice the atlas cover again.", "salience": 0.3},
        "scene",
        time.time() + 1.0,
    ))

    trace = organism.step()
    memories = [item for item in trace.cognitive_items if item["kind"] == "memory_activation"]

    assert memories
    assert any("atlas cover" in item["payload"]["content"].lower() for item in memories)
    assert all(item["canonical"] is False for item in memories)
    assert all(item["provenance"]["authority"] == "subject_memory" for item in memories)
