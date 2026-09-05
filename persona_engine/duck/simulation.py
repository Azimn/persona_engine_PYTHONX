"""Bounded world-plus-self simulation and prediction comparison."""

from __future__ import annotations

from collections.abc import Callable

from .types import CandidateAction, SimulationResult, clamp


Rule = Callable[[CandidateAction, dict], tuple[dict[str, float], dict[str, float]]]


def effect_error(predicted: dict[str, float], observed: dict[str, float]) -> float:
    keys = sorted(set(predicted) | set(observed))
    if not keys:
        return 0.0
    return sum(abs(float(predicted.get(key, 0.0)) - float(observed.get(key, 0.0))) for key in keys) / len(keys)


class RuleWorldModel:
    """Small inspectable simulation substrate with persistable reliability."""

    def __init__(self, state: dict | None = None):
        self.rules: dict[str, Rule] = {}
        self.reliability: dict[str, float] = {
            str(key): clamp(value) for key, value in (state or {}).get("reliability", {}).items()
        }
        self.outcome_overrides: dict[str, tuple[dict[str, float], dict[str, float]]] = {}

    def snapshot(self) -> dict:
        return {"reliability": {key: float(value) for key, value in sorted(self.reliability.items())}}

    def restore(self, state: dict | None) -> None:
        self.reliability = {str(key): clamp(value) for key, value in (state or {}).get("reliability", {}).items()}

    def register(self, action_type: str, rule: Rule, *, reliability: float = 0.80) -> None:
        self.rules[str(action_type)] = rule
        self.reliability.setdefault(str(action_type), clamp(reliability))

    def set_outcome_override(self, action_type: str, world: dict[str, float], self_effects: dict[str, float]) -> None:
        self.outcome_overrides[str(action_type)] = (dict(world), dict(self_effects))

    def simulate(self, action: CandidateAction, context: dict) -> SimulationResult:
        rule = self.rules.get(action.action_type)
        if rule is None:
            world = dict(action.expected_world_effects)
            self_effects = dict(action.expected_self_effects)
        else:
            world, self_effects = rule(action, context)
        return SimulationResult(
            action_id=action.action_id,
            predicted_world_effects={key: float(value) for key, value in world.items()},
            predicted_self_effects={key: float(value) for key, value in self_effects.items()},
            confidence=self.reliability.get(action.action_type, 0.55),
            provenance={"source": "rule_world_model", "action_type": action.action_type},
        )

    def execute(self, action: CandidateAction, simulation: SimulationResult, context: dict) -> tuple[dict[str, float], dict[str, float]]:
        override = self.outcome_overrides.pop(action.action_type, None)
        if override is not None:
            return dict(override[0]), dict(override[1])
        return dict(simulation.predicted_world_effects), dict(simulation.predicted_self_effects)

    def learn(self, action_type: str, *, world_error: float, self_error: float) -> float:
        observed_quality = clamp(1.0 - ((world_error + self_error) / 2.0))
        previous = self.reliability.get(action_type, 0.55)
        updated = clamp((previous * 0.85) + (observed_quality * 0.15))
        self.reliability[action_type] = updated
        return updated
