"""Grounded developmental storage remains bounded and authority-safe."""

from pathlib import Path

from persona_engine.agent import CharacterAgent
from persona_engine.core.autobiographical_evidence import AutobiographicalEvidenceRouter
from persona_engine.core.developmental_learning import RelationshipExpectationStore
from persona_engine.core.dyadic_ritual import DyadicRitualStore
from persona_engine.core.habit import HabitTracker
from persona_engine.core.lived_experience import AutobiographicalInterpretationStore, ExperienceStore, WorldEventLedger
from persona_engine.core.memory import MemoryStore, MemoryUnit
from persona_engine.core.memory_connectivity import MemoryConnectionStore
from persona_engine.core.skills import SkillStore
from persona_engine.core.c99_fixtures import developmental_fixture_bytes


ROOT = Path(__file__).resolve().parents[1]


def _history():
    ledger = WorldEventLedger(); experiences = ExperienceStore(); interpretations = AutobiographicalInterpretationStore()
    event = ledger.create(tick=1, timestamp=1, event_type="failure", outcome="task failed", source="test")
    experience = experiences.perceive(event, "character", attention=1, salience=.8)
    initial = interpretations.create_initial(experience=experience, tick=1)
    return ledger, experiences, interpretations, event, experience, initial


def test_explicit_correction_routes_once_and_unlinked_event_does_not():
    ledger, experiences, interpretations, event, _, initial = _history()
    router = AutobiographicalEvidenceRouter()
    correction = ledger.create(tick=2, timestamp=2, event_type="correction", outcome="cause found", source="test", payload={"corrects_world_event_id": event.event_id})
    links = router.route(event=correction, interpretations=interpretations, experiences=experiences, tick=2)
    assert len(links) == 1 and links[0].interpretation_id == initial.interpretation_id
    unrelated = ledger.create(tick=3, timestamp=3, event_type="correction", outcome="other", source="test")
    assert router.route(event=unrelated, interpretations=interpretations, experiences=experiences, tick=3) == ()
    assert len(interpretations.for_experience(experiences.experiences[0].experience_id)) == 1


def test_memory_connection_boost_is_capped_and_supplements_retrieval():
    store = MemoryConnectionStore(); memory = MemoryStore(); memory.add(MemoryUnit("I remember the task.", id="m1", created_at=1))
    for tick in range(20): store.connect("i1", "m1", "interpretation_context", "ctx", tick, delta=.05)
    boosts = store.boosts_for(("i1",)); assert boosts["m1"] <= .25
    result = memory.retrieve_explained("task", 2, association_boosts=boosts)[0]
    assert 0 < result.reasons["learned_association"] <= .25


def test_supported_skill_improves_more_than_inferred_and_can_misapply():
    skills = SkillStore(); objective = skills.get_or_create("clarify", "speak", "ask_clarification", ("repair",), 1)
    inferred = skills.get_or_create("verify", "speak", "defer_judgment", ("repair",), 1)
    skills.update(objective.skill_id, evidence_tier="objective", succeeded=True, tick=2, episode_id="e1")
    skills.update(inferred.skill_id, evidence_tier="inferred", succeeded=True, tick=2, episode_id="e2")
    assert objective.competence > inferred.competence
    objective.automaticity = .9
    assert skills.forecast(objective, ("unrelated",)).misapplication_risk > 0


def test_habit_and_skill_are_separate_and_outcome_adjustment_is_clamped():
    habits = HabitTracker(); habits.add_or_strengthen("clarify", "repair", "ask first", delta=.2)
    before = habits.habits["clarify"].strength
    habits.adjust_after_outcome(name="clarify", delta=1, now=10)
    assert habits.habits["clarify"].strength == before + .025


def test_relationship_expectation_requires_repetition_and_one_violation_does_not_reset():
    store = RelationshipExpectationStore()
    for episode, day in (("e1", 1), ("e2", 2), ("e3", 3), ("e4", 4), ("e5", 5), ("e6", 6)):
        item = store.observe("returns_to_open_loops", episode, day, True)
    assert item.value == "usually"
    confidence = item.confidence
    store.observe("returns_to_open_loops", "v", 7, False)
    assert item.value == "usually" and 0 < item.confidence < confidence


def test_ritual_requires_three_structural_repetitions_and_stores_no_sentence():
    store = DyadicRitualStore()
    for tick in range(1, 4): item = store.observe("user", "return_to_open_loop", "gesture", None, tick, f"e{tick}")
    assert item.state == "supported"
    assert "hello" not in str(item.to_dict()).lower()


def test_engine_persists_development_without_changing_core_identity(tmp_path):
    agent = CharacterAgent(cartridge_path=str(ROOT / "cartridges" / "pretorius.snp"), user_id="dev", db_path=str(tmp_path / "dev.db"))
    core_before = agent.engine.identity
    for day in range(6): agent.say("I am sorry. Let us repair this carefully.", event_time=1_700_000_000 + day * 86400)
    restarted = CharacterAgent(cartridge_path=str(ROOT / "cartridges" / "pretorius.snp"), user_id="dev", db_path=str(tmp_path / "dev.db"))
    assert restarted.engine.identity == core_before
    assert restarted.engine.skills.skills
    assert restarted.engine.dyadic_rituals.rituals
    assert restarted.engine.relationship_expectations.items
    fixture = developmental_fixture_bytes(restarted.engine)
    assert len(fixture) < 2_000_000
