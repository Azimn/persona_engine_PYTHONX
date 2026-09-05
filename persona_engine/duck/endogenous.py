"""Bounded endogenous cognition for DUCK.

Reflection and outward action are deliberately separate. This module can create
internal workspace candidates and can request that an idle organism open a
cognitive cycle. It cannot speak, mutate canonical state, or bypass action
selection. If a proactive communication candidate is produced, it must win
workspace competition and then survive the ordinary action-selection path.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .services import ServiceContext
from .types import CognitiveItem, OrganismState


@dataclass(frozen=True)
class EndogenousTrigger:
    reason: str
    pressure: float
    payload: dict[str, Any]


class EndogenousTriggerPolicy:
    def __init__(self, *, threshold: float = 0.35, cooldown_ticks: int = 3):
        self.threshold = float(threshold)
        self.cooldown_ticks = max(1, int(cooldown_ticks))
        self.last_trigger_tick = -10**9

    def evaluate(self, state: OrganismState) -> EndogenousTrigger | None:
        if state.tick - self.last_trigger_tick < self.cooldown_ticks:
            return None
        rows: list[tuple[float, str, dict[str, Any]]] = []
        if state.situation.unresolved:
            rows.append((0.55, "unresolved_situation", {"unresolved": list(state.situation.unresolved[:4])}))
        pending = [item for item in state.commitments if item.status == "pending"]
        if pending:
            nearest = min(pending, key=lambda item: (item.due_tick, item.commitment_id))
            distance = nearest.due_tick - state.tick
            if distance <= 5:
                rows.append((0.50, "approaching_commitment", {"commitment_id": nearest.commitment_id, "ticks_until_due": distance}))
        active = [goal for goal in state.active_goals if goal.status == "active"]
        if active:
            goal = max(active, key=lambda item: (item.urgency, item.importance, item.goal_id))
            pressure = min(0.80, max(0.0, goal.urgency * 0.65 + goal.importance * 0.20))
            rows.append((pressure, "active_goal", {"goal_id": goal.goal_id, "goal": goal.description}))
        if state.prediction_ledger:
            latest = state.prediction_ledger[-1]
            error = (float(latest.get("world_error", 0.0)) + float(latest.get("self_error", 0.0))) / 2.0
            if error >= 0.20:
                rows.append((min(0.90, 0.35 + error), "prediction_error", {"prediction_id": latest.get("prediction_id"), "error": error}))
        if not rows:
            return None
        rows.sort(key=lambda row: (-row[0], row[1]))
        pressure, reason, payload = rows[0]
        if pressure < self.threshold:
            return None
        self.last_trigger_tick = state.tick
        return EndogenousTrigger(reason=reason, pressure=pressure, payload=payload)


class EndogenousReflectionService:
    """Deterministic private-reflection specialist returning proposals only."""

    service_name = "endogenous_reflection"

    def propose(self, context: ServiceContext) -> list[CognitiveItem]:
        projection = context.projection
        trigger = dict(projection.get("trigger", {}))
        situation = dict(projection.get("situation", {}))
        goals = list(projection.get("active_goals", []))
        commitments = list(projection.get("commitments", []))
        drives = dict(projection.get("drives", {}))
        reasons: list[str] = []
        salience = 0.0
        self_relevance = 0.0
        action_candidates: list[dict[str, Any]] = []

        unresolved = list(situation.get("unresolved", []) or [])
        if unresolved:
            reasons.append("unresolved_situation")
            salience = max(salience, 0.48)
            self_relevance = max(self_relevance, 0.45)

        if str(trigger.get("kind", "")).startswith("internal_"):
            reasons.append(str(trigger.get("kind")))
            salience = max(salience, float(trigger.get("payload", {}).get("salience", 0.35)))
            self_relevance = max(self_relevance, 0.65)

        urgent_drive = None
        urgent_value = 0.0
        for name, raw in sorted(drives.items()):
            urgency = float(raw.get("urgency", 0.0))
            if urgency > urgent_value:
                urgent_drive = name
                urgent_value = urgency
        if urgent_drive and urgent_value >= 0.35:
            reasons.append(f"drive:{urgent_drive}")
            salience = max(salience, urgent_value)
            self_relevance = max(self_relevance, 0.75)
            if urgent_drive == "affiliation":
                action_candidates.append({
                    "action_id": f"proactive-communicate:{context.tick}",
                    "action_type": "communicate",
                    "parameters": {"reason": "affiliation_pressure", "proactive": True},
                    "originating_goal": "drive-goal:affiliation",
                    "expected_world_effects": {"social_contact": 0.25},
                    "expected_self_effects": {"drive:affiliation": 0.20},
                    "feasibility": 0.90,
                    "cost": 0.08,
                    "risk": 0.08,
                    "uncertainty": 0.20,
                    "reversibility": 0.95,
                })

        if commitments:
            reasons.append("prospective_commitment_active")
            self_relevance = max(self_relevance, 0.70)

        if goals:
            goal = max(goals, key=lambda raw: (float(raw.get("urgency", 0.0)), float(raw.get("importance", 0.0)), str(raw.get("goal_id", ""))))
            reasons.append(f"goal:{goal.get('goal_id', 'unknown')}")
            salience = max(salience, float(goal.get("urgency", 0.0)) * 0.65)

        if not reasons:
            return []

        payload = {
            "reflection_reasons": reasons,
            "unresolved": unresolved[:4],
            "action_candidates": action_candidates,
            "private": True,
            "outward_action_requires_selection": True,
        }
        return [CognitiveItem(
            item_id=f"endogenous:{context.tick}:{reasons[0]}",
            tick=context.tick,
            kind="endogenous_reflection",
            source_module=self.service_name,
            subject_id=context.subject_id,
            payload=payload,
            confidence=0.90,
            salience=min(1.0, salience),
            self_relevance=min(1.0, self_relevance),
            novelty=0.10,
            provenance={"source": self.service_name, "proposal_only": True},
            canonical=False,
        )]
