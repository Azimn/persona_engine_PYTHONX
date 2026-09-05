"""Inspectable DUCK action generation, selection, intention and execution."""

from __future__ import annotations

from dataclasses import replace

from .motivation import DriveSystem
from .types import CandidateAction, Intention, OrganismState, SimulationResult, WorkspaceBroadcast


_DRIVE_ACTIONS = {
    "certainty": ("seek_information", {"drive:certainty": 0.28}),
    "affiliation": ("communicate", {"drive:affiliation": 0.24}),
    "competence": ("practice", {"drive:competence": 0.22}),
    "exploration": ("inspect", {"drive:exploration": 0.26}),
    "autonomy": ("choose_independently", {"drive:autonomy": 0.20}),
    "integrity": ("reaffirm_commitment", {"drive:integrity": 0.24}),
    "viability": ("maintain", {"drive:viability": 0.30}),
}


class ActionGenerator:
    def generate(self, state: OrganismState, broadcast: WorkspaceBroadcast | None) -> list[CandidateAction]:
        actions: list[CandidateAction] = []
        for commitment in state.commitments:
            if commitment.status == "pending" and commitment.due_tick <= state.tick:
                actions.append(CandidateAction(
                    action_id=f"commitment:{state.tick}:{commitment.commitment_id}",
                    action_type="honor_commitment",
                    parameters={"commitment_id": commitment.commitment_id, "target": commitment.target, "kind": commitment.kind},
                    expected_world_effects={"commitment_progress": 1.0},
                    expected_self_effects={"drive:integrity": 0.30},
                    feasibility=1.0,
                    risk=0.05,
                    uncertainty=0.05,
                    provenance={"source": "prospective_commitment", "commitment_id": commitment.commitment_id},
                ))

        if broadcast is not None:
            winner = broadcast.winner
            if winner.kind == "drive_signal":
                drive = str(winner.payload.get("drive", ""))
                action_type, effects = _DRIVE_ACTIONS.get(drive, ("wait", {}))
                actions.append(CandidateAction(
                    action_id=f"drive-action:{state.tick}:{drive}",
                    action_type=action_type,
                    parameters={"drive": drive},
                    originating_goal=f"drive-goal:{drive}",
                    expected_world_effects={"progress": 0.2},
                    expected_self_effects=dict(effects),
                    feasibility=0.95,
                    cost=0.05,
                    risk=0.05,
                    uncertainty=0.10,
                    provenance={"source": "workspace_drive", "broadcast_item": winner.item_id},
                ))
            for index, raw in enumerate(winner.payload.get("action_candidates", []) or []):
                actions.append(CandidateAction(
                    action_id=str(raw.get("action_id", f"event-action:{state.tick}:{index}")),
                    action_type=str(raw.get("action_type", "wait")),
                    parameters=dict(raw.get("parameters", {})),
                    originating_goal=raw.get("originating_goal"),
                    expected_world_effects={key: float(value) for key, value in raw.get("expected_world_effects", {}).items()},
                    expected_self_effects={key: float(value) for key, value in raw.get("expected_self_effects", {}).items()},
                    feasibility=float(raw.get("feasibility", 1.0)),
                    cost=float(raw.get("cost", 0.0)),
                    risk=float(raw.get("risk", 0.0)),
                    uncertainty=float(raw.get("uncertainty", 0.0)),
                    reversibility=float(raw.get("reversibility", 1.0)),
                    provenance={"source": "event_candidate", "broadcast_item": winner.item_id},
                ))

        if not actions:
            actions.append(CandidateAction(
                action_id=f"wait:{state.tick}",
                action_type="wait",
                expected_world_effects={},
                expected_self_effects={},
                feasibility=1.0,
                cost=0.0,
                risk=0.0,
                uncertainty=0.0,
                reversibility=1.0,
                provenance={"source": "deterministic_fallback"},
            ))
        deduped: dict[str, CandidateAction] = {}
        for action in actions:
            deduped[action.action_id] = action
        return [deduped[key] for key in sorted(deduped)]


class ActionSelector:
    def __init__(self, drives: DriveSystem):
        self.drives = drives

    def score(self, action: CandidateAction, simulation: SimulationResult, state: OrganismState) -> tuple[float, dict[str, float]]:
        goal = 0.0
        if action.originating_goal:
            for item in state.active_goals:
                if item.goal_id == action.originating_goal and item.status == "active":
                    goal += item.importance * 0.45 + item.urgency * 0.35
        drive = self.drives.action_value(replace(action, expected_self_effects=simulation.predicted_self_effects))
        integrity = 0.30 if action.action_type == "honor_commitment" else 0.0
        opportunity = sum(max(0.0, float(value)) for value in simulation.predicted_world_effects.values()) * 0.08
        feasibility = action.feasibility * 0.15
        confidence = simulation.confidence * 0.10
        reversibility = action.reversibility * 0.05
        cost = action.cost * -0.18
        risk = action.risk * -0.28
        uncertainty = action.uncertainty * -0.16
        breakdown = {
            "goal": goal,
            "drive": drive,
            "integrity": integrity,
            "opportunity": opportunity,
            "feasibility": feasibility,
            "simulation_confidence": confidence,
            "reversibility": reversibility,
            "cost": cost,
            "risk": risk,
            "uncertainty": uncertainty,
        }
        return sum(breakdown.values()), breakdown

    def select(self, actions: list[CandidateAction], simulations: list[SimulationResult], state: OrganismState) -> tuple[CandidateAction, SimulationResult, float, dict[str, float]]:
        by_id = {item.action_id: item for item in simulations}
        rows = []
        for action in actions:
            simulation = by_id[action.action_id]
            score, breakdown = self.score(action, simulation, state)
            rows.append((score, action.action_id, action, simulation, breakdown))
        rows.sort(key=lambda row: (-row[0], row[1]))
        score, _, action, simulation, breakdown = rows[0]
        return action, simulation, score, breakdown

    def commit(self, action: CandidateAction, simulation: SimulationResult, *, tick: int, score: float, breakdown: dict[str, float]) -> Intention:
        return Intention(
            intention_id=f"intention:{tick}:{action.action_id}",
            action=action,
            selected_at_tick=tick,
            expected_world_effects=dict(simulation.predicted_world_effects),
            expected_self_effects=dict(simulation.predicted_self_effects),
            selection_score=float(score),
            selection_reasons=dict(breakdown),
        )
