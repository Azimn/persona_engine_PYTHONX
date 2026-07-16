"""Simulated-week proof of non-destructive autobiographical change."""

from persona_engine.core.autobiographical_reconsolidation import ReconsolidationContext
from persona_engine.tests.test_autobiographical_persistence import _agent


def test_missed_correction_defers_then_calm_reconsideration_revises(tmp_path):
    agent = _agent(tmp_path, "weeks")
    event = agent.engine.record_world_event(
        event_type="ambiguous_failure", outcome="the shared task failed", source="test", timestamp=100.0,
    )
    experience = agent.engine.perceive_world_event(
        event.event_id, attention=1.0, confidence=0.85, salience=0.9,
        emotional_residue="hurt", interpretation="I believed the work was deliberately abandoned.",
        distortion={"missing_cause": True, "attributed_intent": "dismissal"},
    )
    original = experience.to_dict()
    agent.engine.experiences.decay(100.0 + 86400 * 14)
    correction = agent.engine.record_world_event(
        event_type="corrective_evidence", outcome="missing information caused the failure",
        source="test", payload={"corrects_world_event_id": event.event_id}, timestamp=100.0 + 86400 * 14,
    )
    strained = ReconsolidationContext(
        tick=10, trigger_type="contradictory_evidence", integration_capacity=0.25,
        perceived_capacity=0.2, conflict_noticed=False, conflict_strength=0.9,
        dominant_pressure=0.9, contradicting_world_event_ids=(correction.event_id,),
        proposed_meaning_kind="reconciled_meaning",
        proposed_meaning_code="I now understand the failure as incomplete information rather than deliberate abandonment.",
    )
    assert agent.engine.reconsider_experience(experience.experience_id, strained) is None
    assert len(agent.engine.deferred_reinterpretations) == 1
    calm = ReconsolidationContext(**{
        **strained.__dict__, "tick": 20, "integration_capacity": 0.8,
        "perceived_capacity": 0.7, "conflict_noticed": True, "dominant_pressure": 0.1,
    })
    revised = agent.engine.reconsider_experience(experience.experience_id, calm)
    assert revised and revised.version == 2
    assert revised.emotional_residue == "hurt"
    assert agent.engine.deferred_reinterpretations == []
    assert experience.perceived_summary == original["perceived_summary"]
    assert experience.interpretation == original["interpretation"]
    assert agent.engine.world_events.fetch(event.event_id).outcome == "the shared task failed"
