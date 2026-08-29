"""Sensorium conversion layer.

Sensorium events are changes the character can notice, not a sample of the same
persistent condition on every simulation tick. This distinction matters because
sensorium events can influence pressure and autobiographical memory.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any


@dataclass
class SensoriumEvent:
    kind: str
    detail: str
    intensity: float
    created_at: float
    visible_to_character: bool = True
    source: str = "sensorium"

    def to_fact(self, index: int) -> tuple[str, str]:
        return (f"sensorium_{self.kind}_{index}", self.detail)


class SensoriumProcessor:
    """Converts world/body changes into bounded organism facts.

    Body-derived events are transition based. Remaining in the same strained or
    high-load state is state, not a new experience. Re-entering that state after
    recovery is a new event and can therefore influence pressure or memory again.
    """

    def __init__(self):
        self.events: list[SensoriumEvent] = []

    def add(self, event: SensoriumEvent):
        self.events.append(event)
        self.events = self.events[-80:]

    def extend_from_world_events(self, world_events) -> list[SensoriumEvent]:
        made: list[SensoriumEvent] = []
        for ev in world_events:
            item = SensoriumEvent(ev.kind, ev.detail, ev.intensity, ev.created_at, ev.visible_to_character, "world")
            self.add(item)
            made.append(item)
        return made

    def derive_from_body(self, body_state, now: float, previous_body_state: dict[str, Any] | None = None) -> list[SensoriumEvent]:
        """Emit body events only when the meaningful threshold/state changes."""

        previous = dict(previous_body_state or {})
        previous_sensory = float(previous.get("sensory_load", 0.0) or 0.0)
        previous_movement = float(previous.get("need_for_movement", 0.0) or 0.0)
        previous_recovery = str(previous.get("recovery_state", "stable") or "stable")

        made: list[SensoriumEvent] = []
        if body_state.sensory_load >= 0.70 and previous_sensory < 0.70:
            made.append(SensoriumEvent("sensory_load", "sensory load is high", body_state.sensory_load, now, True, "body"))
        if body_state.need_for_movement >= 0.70 and previous_movement < 0.70:
            made.append(SensoriumEvent("movement_need", "stillness is becoming uncomfortable", body_state.need_for_movement, now, True, "body"))
        if body_state.recovery_state in {"strained", "depleted", "restless"} and body_state.recovery_state != previous_recovery:
            made.append(SensoriumEvent("body_state", f"body is {body_state.recovery_state}", max(body_state.tension, body_state.fatigue, body_state.need_for_movement), now, True, "body"))
        for item in made:
            self.add(item)
        return made

    def recent(self, limit: int = 6) -> list[SensoriumEvent]:
        return self.events[-limit:]

    def summary(self) -> str:
        recent = self.recent(4)
        if not recent:
            return "No notable sensorium events."
        return "Recent sensorium: " + " | ".join(f"{e.kind}: {e.detail}" for e in recent)

    def to_dict(self) -> list[dict[str, Any]]:
        return [asdict(e) for e in self.events]

    @classmethod
    def from_list(cls, data: list[dict[str, Any]] | None) -> "SensoriumProcessor":
        proc = cls()
        for item in data or []:
            proc.add(SensoriumEvent(**{k: item[k] for k in item if k in SensoriumEvent.__dataclass_fields__}))
        return proc
