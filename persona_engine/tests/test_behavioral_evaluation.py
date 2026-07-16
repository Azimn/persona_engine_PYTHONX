"""Blind paired evaluation preserves character and authority boundaries."""

from pathlib import Path

from persona_engine.behavioral_eval import BehavioralEvaluationHarness, load_scenario


ROOT = Path(__file__).resolve().parents[1]
SCENARIO = ROOT / "simulator_scripts" / "pretorius_kiki_paired.yaml"


def _run(tmp_path, turns: int = 4):
    scenario = load_scenario(SCENARIO)
    scenario["turns"] = turns
    harness = BehavioralEvaluationHarness(
        cartridges_dir=ROOT / "cartridges",
        db_dir=tmp_path / "paired",
    )
    return harness, harness.run_paired(scenario)


def test_paired_scenario_exists_and_runs_offline(tmp_path):
    harness, result = _run(tmp_path)

    assert SCENARIO.is_file()
    assert result.participants == ("pretorius", "kiki")
    assert len(result.blind_transcript) == 4
    assert all(item.text.strip() for item in result.blind_transcript)
    assert all(path.is_file() for path in harness.db_paths.values())


def test_blind_transcript_contains_no_private_causal_fields(tmp_path):
    _harness, result = _run(tmp_path)

    for item in result.to_dict()["blind_transcript"]:
        assert set(item) == {"turn", "speaker_id", "listener_id", "text", "source"}
        assert "memory" not in item
        assert "synthesis" not in item
        assert "pressure" not in item


def test_causal_replay_aligns_with_blind_turns(tmp_path):
    _harness, result = _run(tmp_path)

    assert [item.turn for item in result.blind_transcript] == [item.turn for item in result.causal_turns]
    assert all(item.synthesis.get("synthesis_id") for item in result.causal_turns)
    assert all(item.speech_world_event_ids for item in result.causal_turns)
    assert all(item.intrinsic_action for item in result.causal_turns)


def test_character_private_state_is_isolated(tmp_path):
    harness, _result = _run(tmp_path, turns=2)
    pretorius = harness.agents["pretorius"]
    kiki = harness.agents["kiki"]

    pretorius.add_pressure("private_test_pressure", 0.91)
    pretorius.engine.habits.add_or_strengthen("private_test_habit", "test", "hold the private marker")
    pretorius.engine._persist()

    assert harness.db_paths["pretorius"] != harness.db_paths["kiki"]
    assert "private_test_pressure" in pretorius.engine.pressures.pressures
    assert "private_test_pressure" not in kiki.engine.pressures.pressures
    assert "private_test_habit" not in kiki.engine.habits.habits


def test_observed_speech_is_world_evidence_not_objective_claim_truth(tmp_path):
    harness, result = _run(tmp_path, turns=2)
    first = result.blind_transcript[0]

    for agent in harness.agents.values():
        speech_events = [event for event in agent.engine.world_events.recent(20) if event.event_type == "observed_speech"]
        assert speech_events
        event = next(item for item in speech_events if item.outcome == first.text)
        assert event.payload["canonicality"] == "speech_evidence"
        assert event.source == "behavioral_evaluation_host"


def test_paired_memories_remain_first_person_and_actor_scoped(tmp_path):
    harness, _result = _run(tmp_path, turns=4)

    for participant_id, agent in harness.agents.items():
        assert agent.engine.user_id.startswith("participant:")
        assert participant_id not in agent.engine.user_id
        assert agent.engine.memory.memories
        assert all(memory.content.lower().startswith(("i ", "i'", "my ", "we ")) for memory in agent.engine.memory.memories)


def test_paired_metrics_flag_no_offline_assistant_or_identity_drift(tmp_path):
    _harness, result = _run(tmp_path)

    assert result.metrics["turns"] == 4
    assert result.metrics["assistant_drift_hits"] == 0
    assert result.metrics["identity_bleed_suspicions"] == []
    assert result.metrics["exact_repeats"] == 0
    assert result.metrics["opener_repeats"] == 0
    assert result.metrics["private_cognition_renderer_calls"] == 0
    assert result.metrics["expression_renderer_calls"] == 4
    assert result.metrics["total_model_calls"] == 4


def test_nonverbal_behavior_is_observed_as_performance_not_speech(tmp_path):
    scenario = load_scenario(SCENARIO)
    scenario["turns"] = 1
    scenario["starter"] = "If you cared, you would do it for me."
    harness = BehavioralEvaluationHarness(
        cartridges_dir=ROOT / "cartridges",
        db_dir=tmp_path / "nonverbal",
    )
    result = harness.run_paired(scenario)

    item = result.blind_transcript[0]
    assert item.source == "observed_performance"
    assert item.text.startswith("*")
    for agent in harness.agents.values():
        event = next(event for event in agent.engine.world_events.recent(20) if event.event_type == "observed_performance")
        assert event.payload["canonicality"] == "performance_evidence"
