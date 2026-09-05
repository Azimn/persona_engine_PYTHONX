"""Typed DUCK organism contracts.

The types in this module are deliberately model-neutral. Generated language and
LLM proposals may populate CognitiveItems or CandidateActions, but none of these
objects become authoritative merely because a model produced them.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


def clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, float(value)))


@dataclass(frozen=True)
class ExternalEvent:
    event_id: str
    kind: str
    payload: dict[str, Any]
    source: str
    timestamp: float
    confidence: float = 1.0

    def to_dict(self) -> dict[str, Any]: return asdict(self)

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "ExternalEvent":
        return cls(str(raw["event_id"]), str(raw["kind"]), dict(raw.get("payload", {})), str(raw.get("source", "unknown")), float(raw.get("timestamp", 0.0)), float(raw.get("confidence", 1.0)))


@dataclass(frozen=True)
class CognitiveItem:
    item_id: str
    tick: int
    kind: str
    source_module: str
    subject_id: str
    payload: dict[str, Any]
    confidence: float = 1.0
    salience: float = 0.0
    self_relevance: float = 0.0
    novelty: float = 0.0
    threat: float = 0.0
    valence: float = 0.0
    arousal: float = 0.0
    attribution_id: int | None = None
    memory_refs: tuple[str, ...] = ()
    provenance: dict[str, Any] = field(default_factory=dict)
    canonical: bool = False

    def to_dict(self) -> dict[str, Any]: return asdict(self)


@dataclass
class DriveState:
    name: str
    target: float = 0.70
    level: float = 0.70
    urgency: float = 0.0
    persistence: float = 0.60
    decay_per_tick: float = 0.01
    satisfaction_history: list[float] = field(default_factory=list)
    frustration_history: list[float] = field(default_factory=list)

    @property
    def deficit(self) -> float: return clamp(self.target - self.level)
    def to_dict(self) -> dict[str, Any]: return asdict(self)
    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "DriveState": return cls(**raw)


@dataclass
class Goal:
    goal_id: str
    description: str
    importance: float
    urgency: float
    provenance: dict[str, Any]
    status: str = "active"
    deadline_tick: int | None = None
    parent_motive: str | None = None
    expected_satisfaction: dict[str, float] = field(default_factory=dict)
    def to_dict(self) -> dict[str, Any]: return asdict(self)


@dataclass
class ProspectiveCommitment:
    commitment_id: str
    kind: str
    target: str
    due_tick: int
    importance: float = 1.0
    status: str = "pending"
    provenance: dict[str, Any] = field(default_factory=dict)
    def to_dict(self) -> dict[str, Any]: return asdict(self)


@dataclass
class SituationModel:
    situation_id: str = "default"
    facts: dict[str, Any] = field(default_factory=dict)
    entities: dict[str, dict[str, Any]] = field(default_factory=dict)
    unresolved: list[str] = field(default_factory=list)
    last_event_id: str | None = None
    def to_dict(self) -> dict[str, Any]: return asdict(self)


@dataclass(frozen=True)
class CandidateAction:
    action_id: str
    action_type: str
    parameters: dict[str, Any] = field(default_factory=dict)
    originating_goal: str | None = None
    expected_world_effects: dict[str, float] = field(default_factory=dict)
    expected_self_effects: dict[str, float] = field(default_factory=dict)
    feasibility: float = 1.0
    cost: float = 0.0
    risk: float = 0.0
    uncertainty: float = 0.0
    reversibility: float = 1.0
    provenance: dict[str, Any] = field(default_factory=dict)
    def to_dict(self) -> dict[str, Any]: return asdict(self)


@dataclass(frozen=True)
class SimulationResult:
    action_id: str
    predicted_world_effects: dict[str, float]
    predicted_self_effects: dict[str, float]
    confidence: float
    provenance: dict[str, Any] = field(default_factory=dict)
    def to_dict(self) -> dict[str, Any]: return asdict(self)


@dataclass(frozen=True)
class Intention:
    intention_id: str
    action: CandidateAction
    selected_at_tick: int
    expected_world_effects: dict[str, float]
    expected_self_effects: dict[str, float]
    selection_score: float
    selection_reasons: dict[str, float]
    def to_dict(self) -> dict[str, Any]: return asdict(self)


@dataclass(frozen=True)
class PredictionRecord:
    prediction_id: str
    intention_id: str
    predicted_world_effects: dict[str, float]
    predicted_self_effects: dict[str, float]
    observed_world_effects: dict[str, float]
    observed_self_effects: dict[str, float]
    world_error: float
    self_error: float
    def to_dict(self) -> dict[str, Any]: return asdict(self)


@dataclass(frozen=True)
class StatePatch:
    domain: str
    key: str
    old_value: Any
    new_value: Any
    source_module: str
    reason: str
    evidence_refs: tuple[str, ...]
    tick: int
    authorization_class: str
    def to_dict(self) -> dict[str, Any]: return asdict(self)


@dataclass(frozen=True)
class WorkspaceBroadcast:
    tick: int
    winner: CognitiveItem
    priority: float
    competing_item_ids: tuple[str, ...]
    score_breakdown: dict[str, float]
    def to_dict(self) -> dict[str, Any]: return asdict(self)


@dataclass
class OrganismState:
    schema_version: str
    organism_id: str
    subject_id: str
    tick: int = 0
    drive_state: dict[str, DriveState] = field(default_factory=dict)
    situation: SituationModel = field(default_factory=SituationModel)
    working_memory: list[dict[str, Any]] = field(default_factory=list)
    active_goals: list[Goal] = field(default_factory=list)
    commitments: list[ProspectiveCommitment] = field(default_factory=list)
    current_intention: Intention | None = None
    action_ledger: list[dict[str, Any]] = field(default_factory=list)
    prediction_ledger: list[dict[str, Any]] = field(default_factory=list)
    scheduler_state: dict[str, Any] = field(default_factory=dict)
    config_fingerprint: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "organism_id": self.organism_id,
            "subject_id": self.subject_id,
            "tick": self.tick,
            "drive_state": {key: value.to_dict() for key, value in self.drive_state.items()},
            "situation": self.situation.to_dict(),
            "working_memory": list(self.working_memory),
            "active_goals": [goal.to_dict() for goal in self.active_goals],
            "commitments": [item.to_dict() for item in self.commitments],
            "current_intention": self.current_intention.to_dict() if self.current_intention else None,
            "action_ledger": list(self.action_ledger),
            "prediction_ledger": list(self.prediction_ledger),
            "scheduler_state": dict(self.scheduler_state),
            "config_fingerprint": self.config_fingerprint,
        }

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "OrganismState":
        current = raw.get("current_intention")
        intention = None
        if current:
            action = CandidateAction(**current["action"])
            intention = Intention(
                intention_id=current["intention_id"], action=action,
                selected_at_tick=int(current["selected_at_tick"]),
                expected_world_effects=dict(current.get("expected_world_effects", {})),
                expected_self_effects=dict(current.get("expected_self_effects", {})),
                selection_score=float(current.get("selection_score", 0.0)),
                selection_reasons=dict(current.get("selection_reasons", {})),
            )
        return cls(
            schema_version=str(raw["schema_version"]), organism_id=str(raw["organism_id"]), subject_id=str(raw["subject_id"]),
            tick=int(raw.get("tick", 0)),
            drive_state={key: DriveState.from_dict(value) for key, value in raw.get("drive_state", {}).items()},
            situation=SituationModel(**raw.get("situation", {})),
            working_memory=list(raw.get("working_memory", [])),
            active_goals=[Goal(**value) for value in raw.get("active_goals", [])],
            commitments=[ProspectiveCommitment(**value) for value in raw.get("commitments", [])],
            current_intention=intention,
            action_ledger=list(raw.get("action_ledger", [])), prediction_ledger=list(raw.get("prediction_ledger", [])),
            scheduler_state=dict(raw.get("scheduler_state", {})), config_fingerprint=str(raw.get("config_fingerprint", "")),
        )


@dataclass(frozen=True)
class CycleTrace:
    tick: int
    trigger: dict[str, Any]
    situation_changes: dict[str, Any]
    drive_changes: dict[str, Any]
    cognitive_items: tuple[dict[str, Any], ...]
    broadcast: dict[str, Any] | None
    action_candidates: tuple[dict[str, Any], ...]
    simulations: tuple[dict[str, Any], ...]
    selected_intention: dict[str, Any] | None
    outcome: dict[str, Any] | None
    prediction: dict[str, Any] | None
    patches: tuple[dict[str, Any], ...]
    service_errors: tuple[str, ...] = ()
    service_proposals: tuple[dict[str, Any], ...] = ()

    def to_dict(self) -> dict[str, Any]: return asdict(self)
