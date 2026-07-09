"""Proactive event selection for semi-embodied interfaces.

The queue is read-only from the UI's perspective. It inspects organism state and
emits generic event proposals. Delivery must still pass through the normal
engine channel if a host chooses to surface one.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import List


@dataclass(frozen=True)
class ProactiveEvent:
    event_type: str
    priority: str
    public_reason: str
    suggested_channel: str = "chat"
    requires_user_visible_delivery: bool = True

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


class ProactiveQueue:
    """Character-agnostic proactive event proposal logic."""

    def evaluate(self, *, now: float, relationship, body, world, intentions, max_events: int = 3) -> List[ProactiveEvent]:
        events: list[ProactiveEvent] = []
        for loop in getattr(intentions, "open_loops", []):
            age = now - getattr(loop, "created_at", now)
            untouched = now - getattr(loop, "last_touched", now)
            if age >= 60 and untouched >= 60 and getattr(loop, "urgency", 0.0) > 0.25:
                events.append(ProactiveEvent("open_loop_return", "high", "an unresolved matter is still active"))
                break
        if getattr(body, "sensory_load", 0.0) < 0.25 and getattr(relationship, "tension", 0.0) > 0.35:
            events.append(ProactiveEvent("quiet_check_in", "medium", "low sensory load and unresolved tension align"))
        if getattr(body, "need_for_movement", 0.0) > 0.75:
            events.append(ProactiveEvent("movement_pressure", "medium", "body state indicates prolonged stillness"))
        if getattr(world, "user_presence", "unknown") == "returned" and getattr(relationship, "familiarity", 0.0) > 0.25:
            events.append(ProactiveEvent("return_acknowledgement", "low", "user presence changed to returned"))
        priority_rank = {"high": 0, "medium": 1, "low": 2}
        events.sort(key=lambda event: priority_rank.get(event.priority, 9))
        return events[:max_events]
