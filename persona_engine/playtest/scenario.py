"""Validated YAML scenario records for developmental playtests."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

import yaml


@dataclass(frozen=True)
class ScheduledEvent:
    event_id: str
    day: int
    turn: int | None
    event_type: str
    actors: tuple[str, ...]
    targets: tuple[str, ...]
    action: str
    outcome: str
    payload: Mapping[str, Any]
    visible: bool = True


@dataclass(frozen=True)
class DevelopmentalPlaytestScenario:
    schema_version: int
    scenario_id: str
    description: str
    total_days: int
    max_turns_per_day: int
    participants: tuple[Mapping[str, Any], ...]
    actor_profiles: Mapping[str, Any]
    phases: tuple[Mapping[str, Any], ...]
    scheduled_events: tuple[ScheduledEvent, ...]
    acceptance_rules: tuple[Mapping[str, Any], ...]
    stable_seed: int

    def __post_init__(self) -> None:
        if not 1 <= self.total_days <= 90 or not 1 <= self.max_turns_per_day <= 50:
            raise ValueError("scenario day/turn bounds violated")
        if not 1 <= len(self.participants) <= 3 or len(self.scheduled_events) > 256:
            raise ValueError("scenario participant/event bounds violated")


def load_scenario(path: str | Path) -> DevelopmentalPlaytestScenario:
    raw = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    events = tuple(ScheduledEvent(
        event_id=str(item["event_id"]), day=int(item["day"]),
        turn=int(item["turn"]) if item.get("turn") is not None else None,
        event_type=str(item["event_type"]), actors=tuple(item.get("actors", ())),
        targets=tuple(item.get("targets", ())), action=str(item.get("action", "observed")),
        outcome=str(item.get("outcome", "")), payload=dict(item.get("payload") or {}),
        visible=bool(item.get("visible", True)),
    ) for item in raw.get("scheduled_events", ()))
    return DevelopmentalPlaytestScenario(
        int(raw.get("schema_version", 1)), str(raw["scenario_id"]), str(raw.get("description", ""))[:2000],
        int(raw["total_days"]), int(raw.get("max_turns_per_day", 2)),
        tuple(dict(item) for item in raw.get("participants", ())), dict(raw.get("actor_profiles") or {}),
        tuple(dict(item) for item in raw.get("phases", ())), events,
        tuple(dict(item) for item in raw.get("acceptance_rules", ())), int(raw.get("stable_seed", 17)),
    )
