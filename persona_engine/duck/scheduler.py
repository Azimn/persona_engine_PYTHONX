"""Bounded event and endogenous-cognition scheduling."""

from __future__ import annotations

from collections import deque

from .motivation import DriveSystem
from .types import ExternalEvent, OrganismState


class CognitiveScheduler:
    def __init__(self, *, drive_threshold: float = 0.22, max_consecutive_endogenous: int = 4):
        self.external = deque()
        self.drive_threshold = float(drive_threshold)
        self.max_consecutive_endogenous = int(max_consecutive_endogenous)
        self.consecutive_endogenous = 0

    def ingest(self, event: ExternalEvent) -> None:
        self.external.append(event)

    def next_trigger(self, state: OrganismState, drives: DriveSystem) -> ExternalEvent | None:
        if self.external:
            self.consecutive_endogenous = 0
            return self.external.popleft()
        if self.consecutive_endogenous >= self.max_consecutive_endogenous:
            return None

        due = [item for item in state.commitments if item.status == "pending" and item.due_tick <= state.tick]
        if due:
            due.sort(key=lambda item: (-item.importance, item.commitment_id))
            item = due[0]
            self.consecutive_endogenous += 1
            return ExternalEvent(
                event_id=f"internal:commitment:{state.tick}:{item.commitment_id}",
                kind="internal_commitment_due",
                payload={
                    "commitment_id": item.commitment_id,
                    "target": item.target,
                    "salience": item.importance,
                    "self_relevance": 1.0,
                    "drive_relevance": item.importance,
                },
                source="scheduler",
                timestamp=float(state.tick),
            )

        urgent = [drive for drive in drives.drives.values() if drive.urgency >= self.drive_threshold]
        if urgent:
            urgent.sort(key=lambda drive: (-drive.urgency, drive.name))
            drive = urgent[0]
            self.consecutive_endogenous += 1
            return ExternalEvent(
                event_id=f"internal:drive:{state.tick}:{drive.name}",
                kind="internal_drive",
                payload={
                    "drive": drive.name,
                    "salience": drive.urgency,
                    "self_relevance": 1.0,
                    "drive_relevance": drive.urgency,
                },
                source="scheduler",
                timestamp=float(state.tick),
            )
        return None

    def snapshot(self) -> dict:
        return {
            "queued_external": len(self.external),
            "consecutive_endogenous": self.consecutive_endogenous,
            "drive_threshold": self.drive_threshold,
            "max_consecutive_endogenous": self.max_consecutive_endogenous,
        }
