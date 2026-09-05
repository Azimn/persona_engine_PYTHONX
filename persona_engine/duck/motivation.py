"""Closed-loop drive and goal dynamics for DUCK."""

from __future__ import annotations

from .types import CandidateAction, CognitiveItem, DriveState, Goal, clamp


DEFAULT_DRIVES = {
    "viability": (0.75, 0.75, 0.005),
    "affiliation": (0.65, 0.60, 0.010),
    "competence": (0.65, 0.60, 0.008),
    "certainty": (0.70, 0.62, 0.012),
    "autonomy": (0.70, 0.68, 0.006),
    "integrity": (0.80, 0.78, 0.004),
    "exploration": (0.55, 0.50, 0.015),
}


class DriveSystem:
    def __init__(self, drives: dict[str, DriveState] | None = None):
        self.drives = drives or {
            name: DriveState(name=name, target=target, level=level, decay_per_tick=decay)
            for name, (target, level, decay) in DEFAULT_DRIVES.items()
        }

    def step(self) -> dict[str, dict[str, float]]:
        changes: dict[str, dict[str, float]] = {}
        for name in sorted(self.drives):
            drive = self.drives[name]
            before_level = drive.level
            before_urgency = drive.urgency
            drive.level = clamp(drive.level - drive.decay_per_tick)
            drive.urgency = clamp((drive.urgency * 0.72) + (drive.deficit * drive.persistence))
            if drive.deficit > 0.0:
                drive.frustration_history.append(drive.deficit)
                del drive.frustration_history[:-16]
            changes[name] = {
                "level_before": before_level,
                "level_after": drive.level,
                "urgency_before": before_urgency,
                "urgency_after": drive.urgency,
                "deficit": drive.deficit,
            }
        return changes

    def apply_effects(self, effects: dict[str, float]) -> dict[str, float]:
        applied: dict[str, float] = {}
        for key, value in effects.items():
            if not key.startswith("drive:"):
                continue
            name = key.split(":", 1)[1]
            drive = self.drives.get(name)
            if drive is None:
                continue
            delta = float(value)
            drive.level = clamp(drive.level + delta)
            if delta > 0:
                drive.satisfaction_history.append(delta)
                drive.urgency = clamp(drive.urgency - delta * 0.8)
                del drive.satisfaction_history[:-16]
            elif delta < 0:
                drive.frustration_history.append(abs(delta))
                drive.urgency = clamp(drive.urgency + abs(delta) * 0.5)
                del drive.frustration_history[:-16]
            applied[name] = delta
        return applied

    def cognitive_items(self, *, tick: int, subject_id: str, threshold: float = 0.10) -> list[CognitiveItem]:
        items: list[CognitiveItem] = []
        for name in sorted(self.drives):
            drive = self.drives[name]
            if drive.urgency < threshold:
                continue
            items.append(CognitiveItem(
                item_id=f"drive:{tick}:{name}",
                tick=tick,
                kind="drive_signal",
                source_module="motivation",
                subject_id=subject_id,
                payload={
                    "drive": name,
                    "deficit": drive.deficit,
                    "urgency": drive.urgency,
                    "drive_relevance": drive.urgency,
                },
                confidence=1.0,
                salience=drive.urgency,
                self_relevance=1.0,
                novelty=0.05,
                threat=drive.urgency if name in {"viability", "integrity"} else 0.0,
                arousal=drive.urgency,
                provenance={"authority": "drive_system", "canonical_source": True},
                canonical=False,
            ))
        return items

    def ensure_drive_goals(self, active_goals: list[Goal], *, tick: int, threshold: float = 0.22) -> list[Goal]:
        existing = {goal.goal_id: goal for goal in active_goals}
        for name in sorted(self.drives):
            drive = self.drives[name]
            goal_id = f"drive-goal:{name}"
            if drive.urgency >= threshold:
                if goal_id not in existing:
                    active_goals.append(Goal(
                        goal_id=goal_id,
                        description=f"Regulate {name} deficit",
                        importance=drive.urgency,
                        urgency=drive.urgency,
                        provenance={"source": "drive", "drive": name, "created_tick": tick},
                        parent_motive=name,
                        expected_satisfaction={f"drive:{name}": max(0.1, drive.deficit)},
                    ))
                else:
                    existing[goal_id].importance = drive.urgency
                    existing[goal_id].urgency = drive.urgency
                    existing[goal_id].status = "active"
            elif goal_id in existing and drive.deficit <= 0.04:
                existing[goal_id].status = "satisfied"
        return active_goals

    def action_value(self, action: CandidateAction) -> float:
        value = 0.0
        for key, delta in action.expected_self_effects.items():
            if not key.startswith("drive:") or delta <= 0:
                continue
            name = key.split(":", 1)[1]
            drive = self.drives.get(name)
            if drive is not None:
                value += drive.urgency * float(delta)
        return value
