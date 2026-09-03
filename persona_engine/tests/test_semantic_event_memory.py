from pathlib import Path

from persona_engine.agent import CharacterAgent
from persona_engine.core.subject_appraisal import SemanticEventAnnotation


CARTRIDGE = Path("persona_engine/cartridges/pretorius.snp")


def make_agent(tmp_path, name):
    return CharacterAgent(
        cartridge_path=str(CARTRIDGE),
        user_id=name,
        db_path=str(tmp_path / f"{name}.db"),
    )


def cancellation():
    return SemanticEventAnnotation(
        event_id="cancel-1",
        event_type="plan_change",
        topic="plans tonight",
        interpersonal=0.9,
        goal_bearing=1.0,
        identity_bearing=0.0,
        boundary_pressure=0.0,
        cooperation_signal=-0.1,
        novelty=0.3,
        uncertainty=0.1,
        tags=("cancellation",),
    )


def set_relationship(agent, *, trust, familiarity, attachment, guardedness):
    with agent.engine.state_transaction():
        agent.engine.relationship.trust = trust
        agent.engine.relationship.familiarity = familiarity
        agent.engine.relationship.attachment = attachment
        agent.engine.relationship.guardedness = guardedness
        agent.engine._persist()


def test_same_event_leaves_different_lived_memory_in_different_subject_contexts(tmp_path):
    attached = make_agent(tmp_path, "attached")
    relieved = make_agent(tmp_path, "relieved")
    try:
        set_relationship(attached, trust=0.85, familiarity=0.9, attachment=0.9, guardedness=0.1)
        set_relationship(relieved, trust=0.25, familiarity=0.1, attachment=0.05, guardedness=0.8)

        left = attached.observe_semantic_event(
            cancellation(),
            "Jay cancelled our plans tonight.",
            goal_preference=-1.0,
            perceived_control=0.3,
        )
        right = relieved.observe_semantic_event(
            cancellation(),
            "Jay cancelled our plans tonight.",
            goal_preference=1.0,
            perceived_control=0.6,
        )

        assert left["annotation"] == right["annotation"]
        assert left["appraisal"]["social_meaning"] == "relational_disruption"
        assert right["appraisal"]["social_meaning"] == "relief_or_release"
        assert left["memory_salience"]["relationship_relevance"] > right["memory_salience"]["relationship_relevance"]
        assert left["memory_salience"]["emotional_valence"] < 0
        assert right["memory_salience"]["emotional_valence"] > 0
        assert left["memory_salience"]["unresolved"] is True
        assert right["memory_salience"]["unresolved"] is False
        assert attached.engine.pressures.pressures["fear"].magnitude > 0
        assert relieved.engine.pressures.pressures["curiosity"].magnitude > 0
    finally:
        attached.engine.persistence.close()
        relieved.engine.persistence.close()


def test_subjective_memory_trace_survives_restart(tmp_path):
    db_path = tmp_path / "restart.db"
    agent = CharacterAgent(
        cartridge_path=str(CARTRIDGE),
        user_id="restart",
        db_path=str(db_path),
    )
    set_relationship(agent, trust=0.8, familiarity=0.85, attachment=0.75, guardedness=0.1)
    payload = agent.observe_semantic_event(
        cancellation(),
        "Jay cancelled our plans tonight.",
        goal_preference=-1.0,
    )
    memory_id = payload["memory_id"]
    agent.engine.persistence.close()

    restored = CharacterAgent(
        cartridge_path=str(CARTRIDGE),
        user_id="restart",
        db_path=str(db_path),
    )
    try:
        memory = next(item for item in restored.engine.memory.memories if item.id == memory_id)
        assert "meaning:relational_disruption" in memory.tags
        assert memory.relationship_relevance > 0.5
        assert memory.unresolved is True
    finally:
        restored.engine.persistence.close()
