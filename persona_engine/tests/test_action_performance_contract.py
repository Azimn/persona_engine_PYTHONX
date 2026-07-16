"""Canonical action ownership and renderer-subordinate performance."""

from pathlib import Path

from persona_engine.agent import CharacterAgent


CARTRIDGE = Path(__file__).resolve().parents[1] / "cartridges" / "pretorius.snp"


class FixedRenderer:
    def __init__(self, text: str):
        self.text = text
        self.calls = 0

    def generate_expression(self, request):
        self.calls += 1
        return self.text


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


def _agent_events(tmp_path, user: str) -> list[dict]:
    agent = _agent(tmp_path, user)
    return agent.engine.persistence.load_events_since(agent.engine.identity.name, user, 0)
