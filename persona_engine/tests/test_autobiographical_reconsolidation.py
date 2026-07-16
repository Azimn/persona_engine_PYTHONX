"""Evidence and capacity gates for autobiographical reconsideration."""

from persona_engine.core.autobiographical_reconsolidation import (
    AutobiographicalReconsolidator, ReconsolidationContext,
)
from persona_engine.core.lived_experience import AutobiographicalInterpretationStore
from persona_engine.tests.test_autobiographical_interpretation import _experience


def _context(**overrides):
    values = dict(
        tick=10, trigger_type="contradictory_evidence", integration_capacity=0.8,
        perceived_capacity=0.7, conflict_noticed=True, conflict_strength=0.8,
        dominant_pressure=0.1, contradicting_world_event_ids=("world-correction",),
        proposed_meaning_kind="reconciled_meaning",
        proposed_meaning_code="I now understand that missing information caused the failure.",
    )
    values.update(overrides)
    return ReconsolidationContext(**values)


def test_contradiction_requires_notice_capacity_calm_and_evidence():
    experience = _experience()
    current = AutobiographicalInterpretationStore().create_initial(experience=experience, tick=1)
    reconsolidator = AutobiographicalReconsolidator()
    assert reconsolidator.propose(experience=experience, current=current, context=_context())
    assert reconsolidator.propose(experience=experience, current=current, context=_context(conflict_noticed=False)) is None
    assert reconsolidator.deferral_reason(_context(conflict_noticed=False), current) == "conflict_not_noticed"
    assert reconsolidator.propose(experience=experience, current=current, context=_context(integration_capacity=0.2)) is None
    assert reconsolidator.propose(experience=experience, current=current, context=_context(dominant_pressure=0.9)) is None
    assert reconsolidator.propose(experience=experience, current=current, context=_context(contradicting_world_event_ids=())) is None


def test_high_salience_recall_and_dream_cannot_invent_evidence():
    experience = _experience()
    current = AutobiographicalInterpretationStore().create_initial(experience=experience, tick=1)
    reconsolidator = AutobiographicalReconsolidator()
    for trigger in ("high_salience_recall", "dream_consolidation"):
        context = _context(trigger_type=trigger, contradicting_world_event_ids=())
        assert reconsolidator.propose(experience=experience, current=current, context=context) is None


def test_reconsolidation_is_deterministic():
    experience = _experience()
    current = AutobiographicalInterpretationStore().create_initial(experience=experience, tick=1)
    engine = AutobiographicalReconsolidator()
    assert engine.propose(experience=experience, current=current, context=_context()) == engine.propose(
        experience=experience, current=current, context=_context()
    )
