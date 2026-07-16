"""Canonical action ownership and renderer-subordinate performance."""

from pathlib import Path

from persona_engine.agent import CharacterAgent
from persona_engine.core.cognition_schemas import PrivateCognitionProposal
from persona_engine.core.renderer_contract import PrivateCognitionResult


CARTRIDGE = Path(__file__).resolve().parents[1] / "cartridges" / "pretorius.snp"


class FixedRenderer:
    def __init__(self, text: str):
        self.text = text
        self.calls = 0

    def generate_expression(self, request):
        self.calls += 1
        return self.text


class CountingRenderer(FixedRenderer):
    def __init__(self, text: str = "yes.", fail_cognition: bool = False):
        super().__init__(text)
        self.cognition_calls = 0
        self.fail_cognition = fail_cognition

    def generate_private_cognition(self, request):
        self.cognition_calls += 1
        if self.fail_cognition:
            raise TimeoutError("bounded test timeout")
        return PrivateCognitionResult(PrivateCognitionProposal(
            prose="", attention_targets=[], pressure_deltas={}, impulse_candidates=[],
            memory_activation_requests=[], cognitive_theme_ids=[],
        ))


def _agent(tmp_path, user: str, renderer=None) -> CharacterAgent:
    agent = CharacterAgent(
        cartridge_path=str(CARTRIDGE),
        user_id=user,
        db_path=str(tmp_path / f"{user}.db"),
    )
    if renderer is not None:
        agent.engine.set_renderer(renderer)
    return agent


def test_turn_has_one_canonical_action_and_one_linked_performance_plan(tmp_path):
    result = _agent(tmp_path, "one-action").say("Hello.")

    action = result["action_decision"]
    performance = result["performance_plan"]
    assert result["decision_payload"]["action_decision"] == action
    assert performance["decision_id"] == action["decision_id"]
    assert result["observable_action"]["decision_id"] == action["decision_id"]
    assert action["record_authority"] == "canonical_cognitive_record"
    assert performance["record_authority"] == "deterministic_performance_record"
    assert performance["replay_authoritative"] is True

    events = _agent_events(tmp_path, "one-action")
    action_events = [event for event in events if event["event_type"] == "action_decision"]
    assert len(action_events) == 1
    assert action_events[0]["payload"]["decision_id"] == action["decision_id"]


def test_voice_and_avatar_realize_the_same_performance_plan(tmp_path):
    result = _agent(tmp_path, "shared-plan").say("Hello.")
    plan_id = result["performance_plan"]["plan_id"]

    assert result["voice_plan"]["performance_plan_id"] == plan_id
    assert result["avatar_projection"]["performance_plan_id"] == plan_id


def test_renderer_wording_cannot_change_organism_state(tmp_path):
    first_renderer = FixedRenderer("yes.")
    second_renderer = FixedRenderer("no.")
    first = _agent(tmp_path, "wording-a", first_renderer)
    second = _agent(tmp_path, "wording-b", second_renderer)

    first_result = first.say("Hello.")
    second_result = second.say("Hello.")

    assert first_renderer.calls == second_renderer.calls == 1
    assert first_result["response"] != second_result["response"]
    assert first_result["action_decision"]["action_kind"] == second_result["action_decision"]["action_kind"]
    assert {
        key: value for key, value in first_result["relationship"].items() if key != "user_id"
    } == {
        key: value for key, value in second_result["relationship"].items() if key != "user_id"
    }
    assert first_result["energy"] == second_result["energy"]
    assert first.engine.intrinsic_state.to_dict() == second.engine.intrinsic_state.to_dict()
    assert {
        key: value.magnitude for key, value in first.engine.pressures.pressures.items()
    } == {
        key: value.magnitude for key, value in second.engine.pressures.pressures.items()
    }


def test_speech_with_deterministic_cognition_makes_one_renderer_call(tmp_path):
    renderer = CountingRenderer()
    result = _agent(tmp_path, "one-model-call", renderer).say("Hello.")

    assert result["action_decision"]["action_kind"] == "speak"
    assert renderer.cognition_calls == 0
    assert renderer.calls == 1
    assert result["model_calls"]["total_model_calls"] == 1


def test_optional_private_cognition_records_call_reason(tmp_path):
    renderer = CountingRenderer()
    agent = _agent(tmp_path, "optional-cognition", renderer)
    agent.set_private_cognition_mode("model_optional", optional_threshold=0.0)
    result = agent.say("Hello.")

    assert renderer.cognition_calls == 1
    assert result["model_calls"]["private_cognition_renderer_called"] is True
    assert "met threshold" in result["model_calls"]["private_cognition_reason"]


def test_optional_private_cognition_below_threshold_does_not_call_renderer(tmp_path):
    renderer = CountingRenderer()
    agent = _agent(tmp_path, "optional-not-needed", renderer)
    agent.set_private_cognition_mode("model_optional", optional_threshold=1.0)
    result = agent.say("Hello.")

    assert renderer.cognition_calls == 0
    assert result["model_calls"]["private_cognition_renderer_called"] is False
    assert "below threshold" in result["model_calls"]["private_cognition_reason"]


def test_private_cognition_failure_falls_back_to_zero_effects(tmp_path):
    renderer = CountingRenderer(fail_cognition=True)
    agent = _agent(tmp_path, "failed-cognition", renderer)
    agent.set_private_cognition_mode("model_required")
    result = agent.say("Hello.")

    assert result["model_calls"]["private_cognition_fallback_used"] is True
    assert result["cognitive_application_report"]["applied_pressure_deltas"] == {}
    assert result["model_calls"]["total_model_calls"] == 2


def _agent_events(tmp_path, user: str) -> list[dict]:
    agent = _agent(tmp_path, user)
    return agent.engine.persistence.load_events_since(agent.engine.identity.name, user, 0)
