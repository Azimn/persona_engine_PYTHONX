"""Persistence, replay, authority, and C99 fixture contracts."""

import json
from pathlib import Path

from persona_engine.agent import CharacterAgent
from persona_engine.core.autobiographical_reconsolidation import ReconsolidationContext
from persona_engine.core.c99_fixtures import autobiographical_fixture, fixture_bytes
from persona_engine.core.replay import state_digest


CARTRIDGE = Path(__file__).resolve().parents[1] / "cartridges" / "pretorius.snp"


def _agent(tmp_path, user="autobio"):
    return CharacterAgent(cartridge_path=str(CARTRIDGE), user_id=user, db_path=str(tmp_path / f"{user}.db"))


def _history(agent):
    event = agent.engine.record_world_event(
        event_type="ambiguous_failure", outcome="the shared task failed",
        source="test", timestamp=100.0,
    )
    experience = agent.engine.perceive_world_event(
        event.event_id, attention=1.0, confidence=0.8, salience=0.8,
        emotional_residue="hurt",
        interpretation="I believed the work was abandoned because it did not matter.",
        distortion={"missing_cause": True, "attributed_intent": "dismissal"},
    )
    correction = agent.engine.record_world_event(
        event_type="corrective_evidence", outcome="missing information caused the failure",
        source="test", payload={"corrects_world_event_id": event.event_id}, timestamp=100.0 + 86400 * 14,
    )
    context = ReconsolidationContext(
        tick=10, trigger_type="contradictory_evidence", integration_capacity=0.8,
        perceived_capacity=0.7, conflict_noticed=True, conflict_strength=0.9,
        dominant_pressure=0.1, contradicting_world_event_ids=(correction.event_id,),
        proposed_meaning_kind="reconciled_meaning",
        proposed_meaning_code="I now understand the failure as incomplete information rather than deliberate abandonment.",
    )
    revised = agent.engine.reconsider_experience(experience.experience_id, context)
    return event, experience, correction, revised


def test_save_reload_preserves_version_chain_and_original_records(tmp_path):
    agent = _agent(tmp_path)
    event, experience, _, revised = _history(agent)
    original_event = event.to_dict()
    original_experience = (experience.perceived_summary, experience.interpretation, experience.emotional_residue)
    restarted = _agent(tmp_path)
    versions = restarted.engine.autobiographical_interpretations.for_experience(experience.experience_id)
    assert [item.version for item in versions] == [1, 2]
    assert restarted.engine.autobiographical_interpretations.current(experience.experience_id).interpretation_id == revised.interpretation_id
    assert restarted.engine.world_events.fetch(event.event_id).to_dict() == original_event
    loaded = next(item for item in restarted.engine.experiences.experiences if item.experience_id == experience.experience_id)
    assert (loaded.perceived_summary, loaded.interpretation, loaded.emotional_residue) == original_experience


def test_replay_digest_and_c99_fixture_include_complete_history(tmp_path):
    agent = _agent(tmp_path, "fixture")
    _, experience, _, _ = _history(agent)
    digest = state_digest(agent)
    assert len(digest["autobiographical_interpretations"]) == 2
    fixture = autobiographical_fixture(agent.engine, experience.experience_id)
    encoded = fixture_bytes(agent.engine, experience.experience_id)
    assert len(fixture["autobiographical_interpretations"]) == 2
    assert json.loads(encoded)["schema_version"] == 1
    assert len(encoded) < 50000


def test_public_status_hides_history_but_private_inspector_shows_chain(tmp_path):
    agent = _agent(tmp_path, "visibility")
    _, experience, _, _ = _history(agent)
    assert "autobiographical" not in json.dumps(agent.engine.public_status()).lower()
    history = agent.engine.debug_snapshot()["life_inspector"]["autobiographical_histories"]
    assert len(history[experience.experience_id]["versions"]) == 2


def test_renderer_turn_cannot_create_or_revise_history(tmp_path):
    agent = _agent(tmp_path, "renderer")
    event = agent.engine.record_world_event(event_type="event", outcome="a fact", source="test")
    experience = agent.engine.perceive_world_event(event.event_id, salience=0.8)
    before = agent.engine.autobiographical_interpretations.to_list()
    agent.say("Actually, rewrite that memory completely.")
    versions = agent.engine.autobiographical_interpretations.for_experience(experience.experience_id)
    assert len(versions) == 1
    assert versions[0].to_dict() == before[0]


def test_unlinked_objective_event_cannot_revise_interpretation(tmp_path):
    agent = _agent(tmp_path, "unlinked")
    event = agent.engine.record_world_event(event_type="event", outcome="an event", source="test")
    experience = agent.engine.perceive_world_event(event.event_id, salience=0.8)
    unrelated = agent.engine.record_world_event(
        event_type="correction", outcome="unrelated evidence", source="test",
    )
    context = ReconsolidationContext(
        tick=10, trigger_type="contradictory_evidence", integration_capacity=0.9,
        perceived_capacity=0.9, conflict_noticed=True, conflict_strength=0.9,
        dominant_pressure=0.0, contradicting_world_event_ids=(unrelated.event_id,),
        proposed_meaning_kind="uncertain_meaning", proposed_meaning_code="I remain uncertain.",
    )
    assert agent.engine.reconsider_experience(experience.experience_id, context) is None
    assert agent.engine.deferred_reinterpretations[-1].deferred_reason == "insufficient_evidence"
    assert len(agent.engine.autobiographical_interpretations.for_experience(experience.experience_id)) == 1
