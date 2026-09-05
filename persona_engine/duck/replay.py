"""Deterministic external-event replay helpers."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

from .persistence import DuckPersistence
from .types import ExternalEvent


@dataclass
class ReplayTape:
    events: list[dict] = field(default_factory=list)

    def record(self, event: ExternalEvent) -> None:
        self.events.append(event.to_dict())

    def replay(self, factory: Callable[[], object]):
        organism = factory()
        for raw in self.events:
            organism.ingest(ExternalEvent.from_dict(raw))
            organism.run_until_idle()
        return organism

    def replay_digest(self, factory: Callable[[], object]) -> str:
        organism = self.replay(factory)
        return DuckPersistence.digest_state(organism.current_state())
