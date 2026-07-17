"""Deterministic host scheduling, never character cognition."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from .scenario import ScheduledEvent


@dataclass(frozen=True)
class TimeAdvance:
    days: int = 0
    hours: int = 0
    minutes: int = 0

    @property
    def seconds(self) -> int:
        return self.days * 86400 + self.hours * 3600 + self.minutes * 60


@dataclass(frozen=True)
class DirectorBeat:
    beat_id: str
    day: int
    phase: str
    actor_id: str
    goal: str
    required_observable_condition: str | None = None
    event: ScheduledEvent | None = None
    time_advance: TimeAdvance | None = None


class ScenarioDirector:
    def __init__(self, beats: Sequence[DirectorBeat]):
        self.beats = tuple(sorted(beats, key=lambda item: (item.day, item.beat_id)))

    def beats_for_day(self, day: int) -> tuple[DirectorBeat, ...]:
        return tuple(item for item in self.beats if item.day == day)
