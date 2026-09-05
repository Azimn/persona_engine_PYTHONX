"""Independent execution and embodiment policy for DUCK actions."""

from __future__ import annotations

from dataclasses import dataclass, field

from .simulation import RuleWorldModel
from .types import CandidateAction, SimulationResult


@dataclass(frozen=True)
class EmbodimentCapabilities:
    sensors: frozenset[str] = frozenset()
    effectors: frozenset[str] = frozenset()
    body_state: dict = field(default_factory=dict)

    def supports(self, action_type: str) -> bool:
        return not self.effectors or action_type in self.effectors or action_type == "wait"


@dataclass(frozen=True)
class ExecutionPolicy:
    allowed_actions: frozenset[str] | None = None
    denied_actions: frozenset[str] = frozenset()
    confirmation_required: frozenset[str] = frozenset()


@dataclass(frozen=True)
class ExecutionResult:
    executed: bool
    reason: str
    world_effects: dict[str, float]
    self_effects: dict[str, float]

    def to_dict(self) -> dict:
        return {
            "executed": self.executed,
            "reason": self.reason,
            "world_effects": dict(self.world_effects),
            "self_effects": dict(self.self_effects),
        }


class ActionExecutor:
    def __init__(
        self,
        world_model: RuleWorldModel,
        *,
        policy: ExecutionPolicy | None = None,
        embodiment: EmbodimentCapabilities | None = None,
    ):
        self.world_model = world_model
        self.policy = policy or ExecutionPolicy()
        self.embodiment = embodiment or EmbodimentCapabilities()

    def execute(self, action: CandidateAction, simulation: SimulationResult, context: dict) -> ExecutionResult:
        if action.action_type in self.policy.denied_actions:
            return ExecutionResult(False, "policy_denied", {"execution_rejected": 1.0}, {})
        if self.policy.allowed_actions is not None and action.action_type not in self.policy.allowed_actions:
            return ExecutionResult(False, "not_allowlisted", {"execution_rejected": 1.0}, {})
        if action.action_type in self.policy.confirmation_required and not bool(context.get("confirmed", False)):
            return ExecutionResult(False, "confirmation_required", {"execution_rejected": 1.0}, {})
        if not self.embodiment.supports(action.action_type):
            return ExecutionResult(False, "effector_unavailable", {"execution_rejected": 1.0}, {})
        world, self_effects = self.world_model.execute(action, simulation, context)
        return ExecutionResult(True, "executed", dict(world), dict(self_effects))
