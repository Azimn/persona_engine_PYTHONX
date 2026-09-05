"""Replaceable body and environment boundary for DUCK.

The cognitive organism must not assume that its world is a chat box. A body is
an adapter that exposes limited observations, affordances, capabilities, and
execution outcomes. The same subject can therefore move between a deterministic
test body, a desktop companion, a game avatar, XR, or a robot without changing
subject identity.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Protocol

from .simulation import RuleWorldModel
from .types import CandidateAction, SimulationResult


@dataclass(frozen=True)
class BodySnapshot:
    body_id: str = "none"
    location: str = "unknown"
    orientation: str = "unknown"
    sensors: tuple[str, ...] = ()
    effectors: tuple[str, ...] = ()
    state: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class Affordance:
    action_type: str
    parameters: dict[str, Any] = field(default_factory=dict)
    confidence: float = 1.0
    cost: float = 0.0
    risk: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class EmbodimentOutcome:
    executed: bool
    reason: str
    world_effects: dict[str, float] = field(default_factory=dict)
    self_effects: dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class EmbodimentPort(Protocol):
    @property
    def body_id(self) -> str: ...
    def snapshot(self) -> BodySnapshot: ...
    def observe(self, *, tick: int) -> list[dict[str, Any]]: ...
    def affordances(self) -> list[Affordance]: ...
    def supports(self, action_type: str) -> bool: ...
    def execute(self, action: CandidateAction, simulation: SimulationResult, context: dict[str, Any]) -> EmbodimentOutcome: ...


class NullEmbodimentPort:
    """Deterministic no-hardware body used when no external body is attached."""

    body_id = "null-body"

    def snapshot(self) -> BodySnapshot:
        return BodySnapshot(body_id=self.body_id)

    def observe(self, *, tick: int) -> list[dict[str, Any]]:
        del tick
        return []

    def affordances(self) -> list[Affordance]:
        return []

    def supports(self, action_type: str) -> bool:
        del action_type
        return True

    def execute(self, action: CandidateAction, simulation: SimulationResult, context: dict[str, Any]) -> EmbodimentOutcome:
        del action, context
        return EmbodimentOutcome(
            executed=True,
            reason="simulated_execution",
            world_effects=dict(simulation.predicted_world_effects),
            self_effects=dict(simulation.predicted_self_effects),
        )


class EmbodiedWorldModel(RuleWorldModel):
    """Keep internal simulation separate from execution through a body port."""

    def __init__(self, port: EmbodimentPort, state: dict | None = None):
        super().__init__(state)
        self.port = port

    def execute(self, action: CandidateAction, simulation: SimulationResult, context: dict) -> tuple[dict[str, float], dict[str, float]]:
        override = self.outcome_overrides.pop(action.action_type, None)
        if override is not None:
            return dict(override[0]), dict(override[1])
        outcome = self.port.execute(action, simulation, context)
        if not outcome.executed:
            return {"execution_rejected": 1.0}, {}
        return dict(outcome.world_effects), dict(outcome.self_effects)
