"""Habit tracking for recurring behavioral signatures.

A habit is not prose flavor. It is a stateful tendency: when a trigger type
recurs, the character becomes more likely to use a stable response pattern.
"""

from dataclasses import dataclass, field
from typing import Dict, Optional
import time

from .cognition_schemas import EVIDENCE_WEIGHTS, HabitEvidenceSource


@dataclass
class Habit:
    name: str
    trigger: str
    response_pattern: str
    strength: float = 0.1
    uses: int = 0
    last_used: float = 0.0
    evidence_log: list[tuple[HabitEvidenceSource, float]] = field(default_factory=list)


class HabitTracker:
    def __init__(self):
        self.habits: Dict[str, Habit] = {}

    def add_or_strengthen(self, name: str, trigger: str, response_pattern: str, delta: float = 0.03):
        habit = self.habits.get(name)
        now = time.time()
        if habit is None:
            self.habits[name] = Habit(name, trigger, response_pattern, max(0.0, min(1.0, delta)), 1, now)
        else:
            habit.strength = max(0.0, min(1.0, habit.strength + delta))
            habit.uses += 1
            habit.last_used = now

    def add_evidence(self, name: str, trigger: str, response_pattern: str, source: HabitEvidenceSource):
        delta = EVIDENCE_WEIGHTS[source]
        self.add_or_strengthen(name, trigger, response_pattern, delta=delta)
        habit = self.habits[name]
        habit.evidence_log.append((source, delta))

    def most_relevant(self, trigger: str) -> Optional[Habit]:
        candidates = [h for h in self.habits.values() if h.trigger == trigger]
        if not candidates:
            return None
        return max(candidates, key=lambda h: h.strength + min(0.2, h.uses * 0.01))

    def decay_all(self, amount: float = 0.001):
        for h in self.habits.values():
            h.strength = max(0.0, h.strength - amount)

    def adjust_after_outcome(self, *, name: str, delta: float, now: float) -> Habit | None:
        habit = self.habits.get(name)
        if habit is None:
            return None
        habit.strength = max(0.0, min(1.0, habit.strength + max(-0.025, min(0.025, float(delta)))))
        habit.last_used = float(now)
        return habit
