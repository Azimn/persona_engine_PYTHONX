"""Independent execution and embodiment policy for DUCK actions."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol

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


class ActionPreparer(Protocol):
    def prepare(self, action: CandidateAction, context: dict[str, Any]) -> tuple[CandidateAction, dict[str, Any]]: ...


@dataclass(frozen=True)
class ExecutionResult:
    executed: bool
    reason: str
    world_effects: dict[str, float]
    self_effects: dict[str, float]
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "executed": self.executed,
            "reason": self.reason,
            "world_effects": dict(self.world_effects),
            "self_effects": dict(self.self_effects),
            "metadata": dict(self.metadata),
        }


class ActionExecutor:
    def __init__(
        self,
        world_model: RuleWorldModel,
        *,
        policy: ExecutionPolicy | None = None,
        embodiment: EmbodimentCapabilities | None = None,
        action_preparer: ActionPreparer | None = None,
    ):
        self.world_model = world_model
        self.policy = policy or ExecutionPolicy()
        self.embodiment = embodiment or EmbodimentCapabilities()
        self.action_preparer = action_preparer

    def execute(self, action: CandidateAction, simulation: SimulationResult, context: dict) -> ExecutionResult:
        if action.action_type in self.policy.denied_actions:
            return ExecutionResult(False, "policy_denied", {"execution_rejected": 1.0}, {})
        if self.policy.allowed_actions is not None and action.action_type not in self.policy.allowed_actions:
            return ExecutionResult(False, "not_allowlisted", {"execution_rejected": 1.0}, {})
        if action.action_type in self.policy.confirmation_required and not bool(context.get("confirmed", False)):
            return ExecutionResult(False, "confirmation_required", {"execution_rejected": 1.0}, {})
        if not self.embodiment.supports(action.action_type):
            return ExecutionResult(False, "effector_unavailable", {"execution_rejected": 1.0}, {})

        prepared = action
        preparation_metadata: dict[str, Any] = {}
        if self.action_preparer is not None:
            try:
                prepared, preparation_metadata = self.action_preparer.prepare(action, context)
            except Exception as exc:
                return ExecutionResult(
                    False,
                    "action_preparation_failed",
                    {"execution_rejected": 1.0},
                    {},
                    {"preparation_error": type(exc).__name__},
                )
            if prepared.action_id != action.action_id or prepared.action_type != action.action_type:
                return ExecutionResult(
                    False,
                    "action_preparer_changed_decision",
                    {"execution_rejected": 1.0},
                    {},
                    {"original_action": action.to_dict(), "prepared_action": prepared.to_dict()},
                )

        world, self_effects = self.world_model.execute(prepared, simulation, context)
        model_metadata = dict(getattr(self.world_model, "last_execution_metadata", {}) or {})
        metadata = {
            **preparation_metadata,
            **model_metadata,
            "realized_action": prepared.to_dict(),
        }
        return ExecutionResult(True, "executed", dict(world), dict(self_effects), metadata)
