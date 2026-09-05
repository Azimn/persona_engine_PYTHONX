"""Replaceable body and environment boundary for DUCK.

The cognitive organism must not assume that its world is a chat box. A body is
an adapter that exposes limited observations, affordances, capabilities, and
execution outcomes. The same subject can therefore move between a deterministic
test body, a desktop companion, a game avatar, XR, or a robot without changing
subject identity.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Callable, Protocol

from .services import ServiceContext
from .simulation import RuleWorldModel
from .types import CandidateAction, CognitiveItem, SimulationResult


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
    uncertainty: float = 0.0
    reversibility: float = 1.0
    expected_world_effects: dict[str, float] = field(default_factory=dict)
    expected_self_effects: dict[str, float] = field(default_factory=dict)

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


class EmbodimentCognitiveService:
    """Project body state and affordances into cognition without granting authority.

    The body is both an execution boundary and a source of subject-relevant
    evidence. This specialist returns a noncanonical workspace candidate that
    describes current body state and converts known affordances into ordinary
    action candidates. It cannot select or execute them.
    """

    service_name = "embodiment_state"

    def __init__(self, port_provider: Callable[[], EmbodimentPort]):
        self.port_provider = port_provider

    @staticmethod
    def _body_salience(state: dict[str, Any]) -> float:
        values = [0.05]
        for key in ("fatigue", "sensory_load", "tension", "need_for_movement", "pain", "damage"):
            try:
                values.append(max(0.0, min(1.0, float(state.get(key, 0.0)))))
            except (TypeError, ValueError):
                pass
        try:
            energy = float(state.get("energy", 1.0))
            values.append(max(0.0, min(1.0, 1.0 - energy)))
        except (TypeError, ValueError):
            pass
        return max(values)

    def propose(self, context: ServiceContext) -> list[CognitiveItem]:
        port = self.port_provider()
        snapshot = port.snapshot()
        affordances = list(port.affordances())
        action_candidates = []
        for index, item in enumerate(affordances):
            if not port.supports(item.action_type):
                continue
            action_candidates.append({
                "action_id": f"body-affordance:{context.tick}:{index}:{item.action_type}",
                "action_type": item.action_type,
                "parameters": dict(item.parameters),
                "expected_world_effects": dict(item.expected_world_effects),
                "expected_self_effects": dict(item.expected_self_effects),
                "feasibility": max(0.0, min(1.0, float(item.confidence))),
                "cost": max(0.0, float(item.cost)),
                "risk": max(0.0, float(item.risk)),
                "uncertainty": max(0.0, float(item.uncertainty)),
                "reversibility": max(0.0, min(1.0, float(item.reversibility))),
            })
        payload = {
            "body_id": snapshot.body_id,
            "location": snapshot.location,
            "orientation": snapshot.orientation,
            "sensors": list(snapshot.sensors),
            "effectors": list(snapshot.effectors),
            "body_state": dict(snapshot.state),
            "affordances": [item.to_dict() for item in affordances],
            "action_candidates": action_candidates,
        }
        return [CognitiveItem(
            item_id=f"body:{context.tick}:{snapshot.body_id}",
            tick=context.tick,
            kind="body_signal",
            source_module=self.service_name,
            subject_id=context.subject_id,
            payload=payload,
            confidence=1.0,
            salience=self._body_salience(snapshot.state),
            self_relevance=0.85,
            novelty=0.05,
            provenance={"source": "embodiment_port", "body_id": snapshot.body_id, "proposal_only": True},
            canonical=False,
        )]
