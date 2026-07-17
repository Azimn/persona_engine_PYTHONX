"""Deterministic contracts for the lean simulated-life extension."""

from __future__ import annotations

import time
import subprocess
import sys
from pathlib import Path

from fastapi.testclient import TestClient

from persona_engine.agent import CharacterAgent
from persona_engine.core.capability_artifacts import CapabilityArtifactStore
from persona_engine.core.embedding import HashEmbeddingProvider
from persona_engine.core.imperfect_action import ImperfectActionEngine
from persona_engine.core.lived_experience import ExperienceStore, WorldEventLedger
from persona_engine.core.memory import MemoryStore, MemoryUnit
from persona_engine.core.vitality import LifeState, VitalityEventEngine
from persona_engine.ui import create_app


ROOT = Path(__file__).resolve().parents[1]
CARTRIDGES = ROOT / "cartridges"


def _event():
    return WorldEventLedger().create(
        tick=1, timestamp=100.0, event_type="departure", actors=("actor",),
        location="room", action="left", outcome="an actor left the room", source="host",
    )


def test_one_objective_event_can_produce_different_subjective_experiences():
    event = _event()
    store = ExperienceStore()
    first = store.perceive(event, "first", attention=0.9, interpretation="abrupt departure", emotional_residue="hurt")
    second = store.perceive(event, "second", attention=0.9, interpretation="quiet exit", emotional_residue="relief")
    assert first.world_event_id == second.world_event_id == event.event_id
    assert first.interpretation != second.interpretation


def test_character_can_miss_event_entirely():
    assert ExperienceStore().perceive(_event(), "observer", attention=0.0) is None


def test_emotion_survives_after_factual_detail_decays():
    store = ExperienceStore()
    experience = store.perceive(_event(), "observer", attention=0.8, emotional_residue="hurt")
    original_summary = experience.perceived_summary
    store.decay(100.0 + 90000.0, detail_after=10.0)
    assert experience.perceived_summary == original_summary
    assert experience.emotional_residue == "hurt"
    assert "hurt" in experience.recall_surface()
    assert "little factual detail remains" in experience.recall_surface()


def test_memory_retrieval_explains_selection():
    store = MemoryStore(HashEmbeddingProvider(32))
    store.add(MemoryUnit("I remember a difficult departure.", created_at=90.0, salience=0.8, tags={"relationship"}))
    result = store.retrieve_explained("departure", 100.0, top_k=1, relationship_tags={"relationship"})[0]
    assert result.reasons["semantic_similarity"] >= 0.0
    assert result.reasons["relationship_relevance"] > 0.0
    assert result.reasons["embedding_provider"] == "available"


def test_embedding_provider_failure_falls_back_cleanly():
    class BrokenProvider:
        def available(self): return True
        def embed_text(self, text): raise RuntimeError("offline")

    store = MemoryStore(BrokenProvider())
    store.add(MemoryUnit("I noticed a departure.", created_at=90.0))
    result = store.retrieve_explained("departure", 100.0, top_k=1)[0]
    assert result.memory.content == "I noticed a departure."
    assert result.reasons["embedding_provider"] == "fallback"


def test_reasonable_decision_can_fail_during_execution():
    attempt = ImperfectActionEngine(7).attempt(
        decision="use the correct control", objectively_reasonable=True, skill=1.0, distraction=0.0,
        fatigue=0.0, observed_outcome="nothing changed", objective_cause="timing",
        artifacts=CapabilityArtifactStore(), now=1.0, force_execution_failure=True,
    )
    assert attempt.objectively_reasonable and not attempt.succeeded and attempt.failure_reason


def test_successful_outcome_can_create_incorrect_learning_and_later_evidence_weakens_it():
    artifacts = CapabilityArtifactStore()
    attempt = ImperfectActionEngine(8).attempt(
        decision="strike the control", objectively_reasonable=False, skill=0.8, distraction=0.0,
        fatigue=0.0, observed_outcome="the device worked", objective_cause="a loose connection shifted",
        artifacts=artifacts, now=1.0, force_wrong_learning=True,
    )
    learned = artifacts.artifacts[0]
    before = learned.confidence
    artifacts.challenge(attempt.learned_artifact_id, 0.8)
    assert learned.provenance["may_be_wrong"] is True
    assert learned.confidence < before
    assert learned.verification_state == "challenged"


def test_whim_is_weighted_and_limitation_produces_ordinary_mistake():
    engine = VitalityEventEngine(11)
    whim = engine.tick(LifeState(), 1, force_category="whim", whim_weights={"daydream": 1000.0})[0]
    limitation = engine.tick(LifeState(), 1, force_category="limitation")[0]
    assert whim.action == "daydream"
    assert limitation.action in {"attention_drift", "minor_mistake", "forget_detail", "choose_easier_action", "miss_obvious_detail"}


def test_true_chaos_is_independent_and_seeded_replay_is_stable():
    def sequence(seed):
        engine = VitalityEventEngine(seed)
        state = LifeState()
        return [engine.tick(state, index, force_category="chaos")[0].action for index in range(6)]
    assert sequence(19) == sequence(19)
    assert sequence(19) != sequence(20)
    event = VitalityEventEngine(19).tick(LifeState(), 1, force_category="chaos")[0]
    assert event.origin == "chaos"


def test_idle_catch_up_is_bounded_and_does_not_simulate_each_second():
    state = LifeState()
    VitalityEventEngine(21).catch_up(state, 0, elapsed_seconds=86400.0, max_steps=12)
    assert state.last_catch_up_steps == 12


def test_player_message_interrupts_and_activity_can_resume_or_be_abandoned():
    engine = VitalityEventEngine(22)
    state = LifeState(current_activity="rehearsing a plan")
    interruption = engine.interrupt(state, "hello")
    assert interruption["previous_activity"] == "rehearsing a plan"
    assert engine.resolve_interruption(state, pressure=0.2) == "resumed"
    state.current_activity = "sorting notes"
    engine.interrupt(state, "urgent")
    assert engine.resolve_interruption(state, pressure=0.9) == "abandoned"


def test_tier_three_artifact_remains_available_at_tier_zero():
    store = CapabilityArtifactStore()
    artifact = store.add(
        kind="research", content="A verified procedure", source_tier=3,
        provenance={"model": "test"}, confidence=0.9, verification_state="verified",
        supporting_event_ids=("event_1",), canonicality="objective", created_at=1.0,
    )
    assert artifact in store.available(0)


def test_tier_three_artifact_enters_offline_expression_context(tmp_path):
    agent = CharacterAgent(cartridge_path=str(CARTRIDGES / "neutral.snp"), user_id="tier", db_path=str(tmp_path / "tier.db"))
    agent.engine.add_capability_artifact(
        kind="research", content="The verified reset procedure uses control B.", source_tier=3,
        provenance={"tool": "reviewed_test"}, confidence=0.95, verification_state="verified",
        supporting_event_ids=("event_1",), canonicality="objective", created_at=1.0,
    )
    response = agent.say("What procedure did you research?")["response"]
    assert "control B" in response


def test_renderer_text_cannot_create_world_truth_or_canonical_memory(tmp_path):
    agent = CharacterAgent(cartridge_path=str(CARTRIDGES / "neutral.snp"), user_id="u", db_path=str(tmp_path / "state.db"))
    class Renderer:
        def generate(self, messages, **kwargs): return "A fabricated moonbase exists."
    agent.engine.set_renderer(Renderer())
    before_events = len(agent.engine.world_events.to_list())
    agent.say("hello")
    assert len(agent.engine.world_events.to_list()) == before_events + 1
    assert not any("moonbase" in memory.content.lower() for memory in agent.engine.memory.memories)
    assert not any("moonbase" in event.outcome.lower() for event in agent.engine.world_events.recent())


def test_ui_inspection_is_read_only(tmp_path):
    app = create_app(
        cartridge_path=str(CARTRIDGES / "neutral.snp"),
        cartridges_dir=str(CARTRIDGES),
        db_path=str(tmp_path),
        user_id="life_inspector",
        debug=True,
    )
    client = TestClient(app)
    client.post("/api/chat", json={"text": "hello"})
    before = client.get("/api/debug").json()
    inspected = client.get("/api/debug").json()
    after = client.get("/api/debug").json()
    assert inspected["life_inspector"]
    assert before == after


def test_existing_cartridges_load_without_vitality_schema_changes(tmp_path):
    for cartridge in sorted(CARTRIDGES.glob("*.snp")):
        agent = CharacterAgent(cartridge_path=str(cartridge), user_id="compat", db_path=str(tmp_path / f"{cartridge.stem}.db"))
        assert agent.engine.life_state.current_activity


def test_lived_experience_simulator_scenario_runs():
    completed = subprocess.run(
        [
            sys.executable, str(ROOT / "simulator.py"),
            "--script", str(ROOT / "simulator_scripts" / "lived_experience_v02.yaml"),
            "--cartridge", str(CARTRIDGES / "neutral.snp"),
        ],
        capture_output=True, text=True, check=False,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
