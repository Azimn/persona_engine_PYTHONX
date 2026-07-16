"""Observable actor and accelerated host contracts."""

import json
from pathlib import Path

import pytest

from persona_engine.playtest.actors import (
    ActorContext, ActorMove, HUMAN_POLICIES, OllamaActorConfig, OllamaHumanActor,
    ScriptedHumanActor, assert_observable_only,
)
from persona_engine.playtest.host import DevelopmentalPlaytestHost
from persona_engine.playtest.report import write_reports
from persona_engine.playtest.scenario import load_scenario


ROOT = Path(__file__).resolve().parents[1]


def test_actor_context_rejects_private_fields_recursively():
    with pytest.raises(ValueError, match="private-state"):
        ActorContext("s", "human", "character", 1, 1, {"nested": {"self_monitor": {}}}, (), "goal", "phase", ("speak",), 1)


def test_actor_move_rejects_private_mutation():
    with pytest.raises(ValueError):
        ActorMove("human", "provide_evidence", "Here.", {}, {"memory": "rewrite"}, "bad")


def test_ollama_prompt_contains_observable_context_only():
    fallback = ScriptedHumanActor(actor_id="human", policy=HUMAN_POLICIES["steady_collaborator"])
    actor = OllamaHumanActor(actor_id="human", config=OllamaActorConfig(), fallback=fallback)
    context = ActorContext("s", "human", "character", 1, 1, {"room": "workshop"}, (), "ask", "start", ("speak",), 1)
    prompt = actor._prompt(context)
    assert "workshop" in prompt
    assert all(key not in prompt for key in ("self_monitor", "integration_capacity", "belief_ledger"))


def test_ollama_failure_falls_back_deterministically(monkeypatch):
    import urllib.request
    fallback = ScriptedHumanActor(actor_id="human", policy=HUMAN_POLICIES["steady_collaborator"])
    actor = OllamaHumanActor(actor_id="human", config=OllamaActorConfig(timeout_seconds=.01), fallback=fallback)
    monkeypatch.setattr(urllib.request, "urlopen", lambda *a, **k: (_ for _ in ()).throw(__import__("urllib.error").error.URLError("down")))
    context = ActorContext("s", "human", "character", 1, 1, {}, (), "ask", "start", ("speak",), 17)
    first = actor.next_move(context); second = actor.next_move(context)
    assert first == second
    assert first.rationale_code == "ollama_unavailable"


def test_ollama_malformed_host_event_falls_back_closed(monkeypatch):
    import urllib.request

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def read(self):
            payload = {
                "response": json.dumps({
                    "move_kind": "speak",
                    "text": "I have a question.",
                    "visible_context": {},
                    "host_event": "not-a-record",
                    "rationale_code": "model_move",
                })
            }
            return json.dumps(payload).encode("utf-8")

    fallback = ScriptedHumanActor(actor_id="human", policy=HUMAN_POLICIES["steady_collaborator"])
    actor = OllamaHumanActor(actor_id="human", config=OllamaActorConfig(), fallback=fallback)
    monkeypatch.setattr(urllib.request, "urlopen", lambda *a, **k: FakeResponse())
    context = ActorContext("s", "human", "character", 1, 1, {}, (), "ask", "start", ("speak",), 17)

    move = actor.next_move(context)

    assert move.rationale_code == "ollama_invalid_json"
    assert move.host_event is None


def test_thirty_day_host_writes_observable_separate_from_diagnostics(tmp_path):
    scenario = load_scenario(ROOT / "playtest_scenarios" / "steady_collaborator_30_days.yaml")
    host = DevelopmentalPlaytestHost(scenario=scenario, cartridges_dir=ROOT / "cartridges", db_dir=tmp_path)
    result = host.run()
    assert result.metrics["day_count"] == 30
    assert result.metrics["private_state_leak_count"] == 0
    assert len(result.actor_moves) == 30
    assert all("self_monitor" not in json.dumps(item.to_dict()) for item in result.transcript)
    assert result.diagnostics
    assert "exact_repeat_count_by_speaker" in result.metrics
    assert result.metrics["activity_callback_count"] > 0
    assert result.metrics["conversation_move_diversity"] > 0

    output = tmp_path / "reports"
    write_reports(output, result)
    review = json.loads((output / "illusion_review.json").read_text(encoding="utf-8"))
    assert review["instructions"].startswith("Review the blind transcript")
    assert len(review["questions"]) == 8
    assert all(item["rating"] is None for item in review["questions"])


def test_saved_moves_replay_without_actor_generation(tmp_path):
    scenario = load_scenario(ROOT / "playtest_scenarios" / "boundary_tester_14_days.yaml")
    first = DevelopmentalPlaytestHost(scenario=scenario, cartridges_dir=ROOT / "cartridges", db_dir=tmp_path / "one").run()
    second = DevelopmentalPlaytestHost(scenario=scenario, cartridges_dir=ROOT / "cartridges", db_dir=tmp_path / "two", replay_moves=first.actor_moves).run()
    assert [item.to_dict() for item in first.actor_moves] == [item.to_dict() for item in second.actor_moves]
    assert [item.text for item in first.transcript if item.source == "actor"] == [item.text for item in second.transcript if item.source == "actor"]
    assert [(item.get("action_kind"), item.get("communicative_function")) for item in first.diagnostics] == [
        (item.get("action_kind"), item.get("communicative_function")) for item in second.diagnostics
    ]


def test_character_crossplay_uses_separate_engines(tmp_path):
    scenario = load_scenario(ROOT / "playtest_scenarios" / "kiki_pretorius_crossplay_30_days.yaml")
    host = DevelopmentalPlaytestHost(scenario=scenario, cartridges_dir=ROOT / "cartridges", db_dir=tmp_path)
    assert host.agents["kiki"].engine is not host.agents["pretorius"].engine
    result = host.run()
    assert {item.speaker_id for item in result.transcript} >= {"kiki", "pretorius"}
