"""Small procedural-memory/affordance registry for DUCK."""

from __future__ import annotations

from dataclasses import dataclass, field

from .types import CandidateAction, OrganismState, WorkspaceBroadcast, clamp


@dataclass
class Procedure:
    procedure_id: str
    action_type: str
    trigger_kinds: tuple[str, ...] = ()
    trigger_drives: tuple[str, ...] = ()
    parameters: dict = field(default_factory=dict)
    expected_world_effects: dict[str, float] = field(default_factory=dict)
    expected_self_effects: dict[str, float] = field(default_factory=dict)
    confidence: float = 0.70
    cost: float = 0.05
    risk: float = 0.05
    reversibility: float = 0.8


class ProcedureRegistry:
    def __init__(self, procedures: list[Procedure] | None = None):
        self.procedures = {item.procedure_id: item for item in (procedures or [])}

    def add(self, procedure: Procedure) -> None:
        self.procedures[procedure.procedure_id] = procedure

    def candidates(self, state: OrganismState, broadcast: WorkspaceBroadcast | None) -> list[CandidateAction]:
        if broadcast is None:
            return []
        winner = broadcast.winner
        drive = str(winner.payload.get("drive", ""))
        result: list[CandidateAction] = []
        for procedure_id in sorted(self.procedures):
            procedure = self.procedures[procedure_id]
            kind_match = bool(procedure.trigger_kinds and winner.kind in procedure.trigger_kinds)
            drive_match = bool(procedure.trigger_drives and drive in procedure.trigger_drives)
            if not (kind_match or drive_match):
                continue
            result.append(CandidateAction(
                action_id=f"procedure:{state.tick}:{procedure.procedure_id}",
                action_type=procedure.action_type,
                parameters=dict(procedure.parameters),
                expected_world_effects=dict(procedure.expected_world_effects),
                expected_self_effects=dict(procedure.expected_self_effects),
                feasibility=clamp(procedure.confidence),
                cost=procedure.cost,
                risk=procedure.risk,
                uncertainty=1.0 - clamp(procedure.confidence),
                reversibility=procedure.reversibility,
                provenance={"source": "procedural_memory", "procedure_id": procedure.procedure_id},
            ))
        return result

    def learn(self, action: CandidateAction, *, prediction_error: float) -> None:
        procedure_id = str(action.provenance.get("procedure_id", ""))
        procedure = self.procedures.get(procedure_id)
        if procedure is None:
            return
        observed = clamp(1.0 - prediction_error)
        procedure.confidence = clamp(procedure.confidence * 0.85 + observed * 0.15)
