"""Self-monitor candidates affect behavior only through situated synthesis."""

from pathlib import Path

from persona_engine.agent import CharacterAgent
from persona_engine.core.renderer import LocalLLMRenderer
from persona_engine.core.self_monitor import RegulationCandidate, SelfMonitorResult
from persona_engine.core.synthesis import SynthesisInfluence, synthesize


ROOT = Path(__file__).resolve().parents[1]
CARTRIDGES = ROOT / "cartridges"


class CountingRenderer:
    def __init__(self):
        self.expression_calls = 0

    def generate_expression(self, request):
        self.expression_calls += 1
        return "I need that point clarified."

    def generate_private_cognition(self, request):
        return LocalLLMRenderer(provider="offline").generate_private_cognition(request)


class FixedMonitor:
    def __init__(self, kind: str, strength: float = 1.0, reportable: bool = True):
        candidate = RegulationCandidate("fixed-regulation", kind, strength, "current cognitive task", ("test",), reportable)
        self.result = SelfMonitorResult(
            schema_version=1, monitor_id="fixed-monitor", tick=1,
            actual_capacity=0.45, perceived_capacity=0.32,
            perceived_confidence=0.30, perceived_memory_reliability=0.35,
            perceived_bias=0.25, noticed_conflict_ids=("relationship:current",),
            missed_conflict_ids=("memory:retrieved:0",), attributed_cause="conflicting_evidence",
            regulation_candidates=(candidate,), reportability=0.7,
            provenance_ids=("relationship:current",),
        )

    def evaluate(self, **kwargs):
        return self.result


def _agent(tmp_path, cartridge="neutral.snp", user="monitor"):
    return CharacterAgent(
        cartridge_path=str(CARTRIDGES / cartridge), user_id=user,
        db_path=str(tmp_path / f"{user}.db"),
    )


def test_regulation_candidates_enter_synthesis_without_bypass():
    candidate = RegulationCandidate("candidate", "delay", 0.9, "task", ("low_capacity",), True)
    influences = [
        SynthesisInfluence("evidence:input", "evidence", "input", 0.7, immediate=True),
        SynthesisInfluence(f"regulation:{candidate.candidate_id}", "regulation", candidate.kind, candidate.strength),
    ]
    result = synthesize(influences, 0.55)
    assert any(item.kind == "regulation" for item in result.considered_influences)
    assert result.selected_regulation_candidate_id == candidate.candidate_id


def test_selected_delay_uses_zero_expression_calls(tmp_path):
    renderer = CountingRenderer()
    agent = _agent(tmp_path, user="delay")
    agent.engine.self_monitor = FixedMonitor("delay")
    agent.engine.set_renderer(renderer)
    agent.engine.body.fatigue = 0.8
    result = agent.say("A minor interruption.")
    assert result["action_decision"]["action_kind"] == "delay"
    assert result["model_calls"]["expression_renderer_called"] is False
    assert renderer.expression_calls == 0


def test_selected_clarification_uses_one_expression_call(tmp_path):
    renderer = CountingRenderer()
    agent = _agent(tmp_path, user="clarify")
    agent.engine.self_monitor = FixedMonitor("ask_clarification")
    agent.engine.set_renderer(renderer)
    result = agent.say("It was that thing again.")
    assert result["action_decision"]["communicative_function"] == "ask_clarification"
    assert result["model_calls"]["expression_renderer_called"] is True
    assert renderer.expression_calls == 1


def test_concealed_uncertainty_changes_performance_without_diagnostic_leak(tmp_path):
    renderer = CountingRenderer()
    agent = _agent(tmp_path, user="conceal")
    agent.engine.self_monitor = FixedMonitor("conceal_uncertainty", reportable=False)
    agent.engine.set_renderer(renderer)
    result = agent.say("Tell me what you think.")
    face = next(item for item in result["performance_plan"]["acts"] if item["channel"] == "face")
    assert face["function"] == "controlled"
    assert "actual_capacity" not in result["system_prompt"]
    assert "memory:retrieved:0" not in result["system_prompt"]
    assert "conceal uncertainty" not in result["system_prompt"]


def test_self_monitor_persists_and_reloads(tmp_path):
    db = tmp_path / "persist.db"
    first = CharacterAgent(
        cartridge_path=str(CARTRIDGES / "neutral.snp"),
        user_id="persist-monitor", db_path=str(db),
    )
    result = first.say("Hello.")
    restarted = CharacterAgent(
        cartridge_path=str(CARTRIDGES / "neutral.snp"),
        user_id="persist-monitor", db_path=str(db),
    )
    assert restarted.engine._last_self_monitor.to_dict() == result["self_monitor"]


def test_public_status_exposes_no_private_monitor_values(tmp_path):
    agent = _agent(tmp_path, user="public")
    result = agent.say("Hello.")
    assert "self_monitor" not in result["public_status"]
    assert "actual_capacity" not in result["public_status"]
    assert "perceived_capacity" not in result["public_status"]


def test_debug_snapshot_contains_monitor_provenance_and_authority(tmp_path):
    agent = _agent(tmp_path, user="debug")
    agent.say("Hello.")
    monitor = agent.engine.debug_snapshot()["life_inspector"]["self_monitor"]
    assert monitor["record_authority"] == "canonical_cognitive_record"
    assert "provenance_ids" in monitor


def test_character_profiles_produce_different_monitoring_and_performance(tmp_path):
    pretorius = _agent(tmp_path, "pretorius.snp", "same-cause-p")
    kiki = _agent(tmp_path, "kiki.snp", "same-cause-k")
    for agent in (pretorius, kiki):
        agent.engine.body.fatigue = 0.95
        agent.engine.body.sensory_load = 0.85
        agent.add_pressure("fear", 0.95)
    p_result = pretorius.say("That memory may be wrong.")
    k_result = kiki.say("That memory may be wrong.")
    assert p_result["self_monitor"] != k_result["self_monitor"]
    p_kinds = {item["kind"] for item in p_result["self_monitor"]["regulation_candidates"]}
    k_kinds = {item["kind"] for item in k_result["self_monitor"]["regulation_candidates"]}
    assert p_kinds != k_kinds or (
        p_result["performance_plan"]["certainty"]
        != k_result["performance_plan"]["certainty"]
    )
