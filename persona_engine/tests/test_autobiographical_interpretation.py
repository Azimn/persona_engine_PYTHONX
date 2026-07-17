"""Non-destructive autobiographical meaning contracts."""

from dataclasses import replace

import pytest

from persona_engine.core.lived_experience import (
    AutobiographicalInterpretationStore, ExperienceStore, ReinterpretationCandidate,
    SubjectiveExperience, WorldEventLedger,
)


def _experience() -> SubjectiveExperience:
    event = WorldEventLedger().create(
        tick=1, timestamp=100.0, event_type="failure", actors=("character",),
        outcome="the shared task failed", source="test",
    )
    item = ExperienceStore().perceive(
        event, "character", attention=1.0, confidence=0.8, salience=0.8,
        emotional_residue="hurt", interpretation="I believed the work was abandoned.",
    )
    assert item
    return item


def _candidate(prior, **overrides):
    values = dict(
        schema_version=1, candidate_id="candidate-1", experience_id=prior.experience_id,
        prior_interpretation_id=prior.interpretation_id, trigger_type="contradictory_evidence",
        proposed_meaning_kind="reconciled_meaning",
        proposed_meaning="I now understand that missing information caused the failure.",
        confidence=0.8, supporting_memory_ids=(), contradicting_memory_ids=("memory-2",),
        supporting_world_event_ids=(), contradicting_world_event_ids=("world-2",),
        conflict_strength=0.8, emotional_charge_delta=0.2, eligible_after_tick=10,
        provenance_ids=(prior.interpretation_id, "world-2"),
    )
    values.update(overrides)
    return ReinterpretationCandidate(**values)


def test_decay_preserves_original_experience_and_changes_recall_surface():
    experience = _experience()
    original = (experience.perceived_summary, experience.interpretation, experience.emotional_residue)
    store = ExperienceStore([experience])
    store.decay(100.0 + 86400.0 * 14, detail_after=86400.0)
    assert (experience.perceived_summary, experience.interpretation, experience.emotional_residue) == original
    assert "little factual detail" in experience.recall_surface()
    assert experience.confidence < 0.8


def test_legacy_destructive_decay_loads_without_inventing_lost_text():
    payload = _experience().to_dict()
    payload["perceived_summary"] = "I remember feeling hurt, but the factual detail has faded."
    loaded = SubjectiveExperience.from_dict(payload)
    assert loaded.distortion["legacy_destructive_decay"] is True
    assert loaded.perceived_summary == payload["perceived_summary"]


def test_initial_interpretation_is_idempotent_and_history_is_append_only():
    experience = _experience()
    store = AutobiographicalInterpretationStore()
    first = store.create_initial(experience=experience, tick=1, meaning_kind="mistaken_attribution")
    assert store.create_initial(experience=experience, tick=2) is first
    second = store.append_revision(experience=experience, prior=first, candidate=_candidate(first), tick=10)
    assert [item.version for item in store.for_experience(experience.experience_id)] == [1, 2]
    assert store.current(experience.experience_id) == second
    assert first.current_meaning == "I believed the work was abandoned."


def test_revision_must_be_sequential_and_supersede_latest():
    experience = _experience()
    store = AutobiographicalInterpretationStore()
    first = store.create_initial(experience=experience, tick=1)
    invalid = replace(first, interpretation_id="bad", version=2, supersedes="not-latest")
    with pytest.raises(ValueError, match="supersede"):
        store.append(invalid)


def test_version_and_global_bounds_refuse_without_deleting_history():
    experience = _experience()
    store = AutobiographicalInterpretationStore()
    prior = store.create_initial(experience=experience, tick=1)
    for version in range(2, 9):
        candidate = _candidate(prior, candidate_id=f"candidate-{version}")
        prior = store.append_revision(experience=experience, prior=prior, candidate=candidate, tick=version * 10)
    before = store.to_list()
    with pytest.raises(ValueError, match="versions"):
        store.append_revision(experience=experience, prior=prior, candidate=_candidate(prior, candidate_id="overflow"), tick=100)
    assert store.to_list() == before
