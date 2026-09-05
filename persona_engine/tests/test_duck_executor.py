from persona_engine.duck.executor import ActionExecutor, EmbodimentCapabilities, ExecutionPolicy
from persona_engine.duck.simulation import RuleWorldModel
from persona_engine.duck.types import CandidateAction


def action(action_type="inspect"):
    return CandidateAction(
        action_id="a",
        action_type=action_type,
        expected_world_effects={"progress": 0.4},
        expected_self_effects={},
    )


def test_executor_enforces_policy_independently_of_simulator():
    world = RuleWorldModel()
    candidate = action("dangerous_tool")
    simulation = world.simulate(candidate, {})
    executor = ActionExecutor(world, policy=ExecutionPolicy(denied_actions=frozenset({"dangerous_tool"})))

    result = executor.execute(candidate, simulation, {})

    assert result.executed is False
    assert result.reason == "policy_denied"
    assert result.world_effects == {"execution_rejected": 1.0}


def test_executor_enforces_embodiment_effectors():
    world = RuleWorldModel()
    candidate = action("communicate")
    simulation = world.simulate(candidate, {})
    executor = ActionExecutor(world, embodiment=EmbodimentCapabilities(effectors=frozenset({"inspect"})))

    result = executor.execute(candidate, simulation, {})

    assert result.executed is False
    assert result.reason == "effector_unavailable"
