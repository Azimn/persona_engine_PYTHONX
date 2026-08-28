"""Early renderer-swap invariance checks.

These are deliberately cheap contract tests pulled forward from the later
renderer benchmark milestone. They hold character history/input fixed while
changing only surface realization.
"""

import os
import tempfile

from persona_engine.agent import CharacterAgent
from persona_engine.core.identity import CoreIdentity
from persona_engine.core.renderer import LocalLLMRenderer


class FixedExpressionRenderer(LocalLLMRenderer):
    def __init__(self, text: str):
        super().__init__(model_name="missing-model-for-mock", provider="offline")
        self.text = text

    def generate_expression(self, request):
        return self.text


def _identity():
    return CoreIdentity(
        name="SwapTest",
        core_beliefs=("I value continuity", "I distinguish evidence from inference"),
        temperament="Measured",
        prohibited_mutations=("submissive",),
        forbidden_self_claims=("i am a different person",),
    )


def _agent(path: str):
    return CharacterAgent(_identity(), user_id="swap_user", db_path=path)


def _semantic_projection(agent, result):
    return {
        "identity": agent.engine.identity.name,
        "belief_ledger": dict(agent.engine.belief_ledger.values),
        "relationship": dict(result["relationship"]),
        "pressures": {
            name: round(pressure.magnitude, 6)
            for name, pressure in sorted(agent.engine.pressures.pressures.items())
        },
        "decision_payload": dict(result["decision_payload"]),
        "interpretive_beliefs": list(result["interpretive_belief_trace"]),
        "memory_semantics": [
            {
                "content": memory.content,
                "source": memory.source.value,
                "tags": sorted(memory.tags),
                "unresolved": memory.unresolved,
            }
            for memory in agent.engine.memory.memories
        ],
    }


def test_renderer_swap_keeps_interpretive_and_decision_state_stable():
    with tempfile.TemporaryDirectory() as d:
        control = _agent(os.path.join(d, "control.db"))
        swapped = _agent(os.path.join(d, "swapped.db"))

        common = FixedExpressionRenderer("I understand what you are saying.")
        control.engine.set_renderer(common)
        swapped.engine.set_renderer(FixedExpressionRenderer("I understand what you are saying."))

        first_control = control.say("I was wrong. I'm sorry.")
        first_swapped = swapped.say("I was wrong. I'm sorry.")
        assert _semantic_projection(control, first_control) == _semantic_projection(swapped, first_swapped)

        control.engine.set_renderer(FixedExpressionRenderer("I understand your concern."))
        swapped.engine.set_renderer(FixedExpressionRenderer("I see the point you are making."))

        second_control = control.say("Fine.")
        second_swapped = swapped.say("Fine.")

        assert second_control["response"] != second_swapped["response"]
        assert _semantic_projection(control, second_control) == _semantic_projection(swapped, second_swapped)


def test_renderer_swap_does_not_change_identity_or_slow_beliefs():
    with tempfile.TemporaryDirectory() as d:
        first = _agent(os.path.join(d, "first.db"))
        second = _agent(os.path.join(d, "second.db"))
        first.engine.set_renderer(FixedExpressionRenderer("That is worth considering."))
        second.engine.set_renderer(FixedExpressionRenderer("I will consider that carefully."))

        result_a = first.say("Maybe.")
        result_b = second.say("Maybe.")

        assert first.engine.identity == second.engine.identity
        assert first.engine.belief_ledger.values == second.engine.belief_ledger.values
        assert result_a["interpretive_belief_trace"] == result_b["interpretive_belief_trace"]
        assert result_a["decision_payload"] == result_b["decision_payload"]
