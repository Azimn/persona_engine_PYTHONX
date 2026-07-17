"""Current and historical autobiographical activation remains bounded."""

from persona_engine.core.lived_experience import AutobiographicalInterpretationStore
from persona_engine.tests.test_autobiographical_interpretation import _candidate, _experience


def test_current_meaning_activates_more_than_superseded_history():
    experience = _experience()
    experience.memory_id = "memory-1"
    store = AutobiographicalInterpretationStore()
    first = store.create_initial(experience=experience, tick=1, meaning_kind="mistaken_attribution")
    second = store.append_revision(experience=experience, prior=first, candidate=_candidate(first), tick=10)
    activations = store.activate_for_memories(
        ["memory-1"], relationship_relevance=1.0, identity_relevance=0.0, emotional_match=0.0,
    )
    assert activations[0].interpretation_id == second.interpretation_id
    assert activations[0].activation > activations[1].activation
    assert activations[1].status == "historical"


def test_activation_uses_dynamic_experience_memory_link():
    experience = _experience()
    store = AutobiographicalInterpretationStore()
    first = store.create_initial(experience=experience, tick=1)
    experience.memory_id = "later-memory"
    activation = store.activate_for_memories(
        ["later-memory"], relationship_relevance=0.0, identity_relevance=0.0,
        emotional_match=0.0, memory_links={experience.experience_id: experience.memory_id},
    )
    assert activation[0].interpretation_id == first.interpretation_id
