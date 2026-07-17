"""Layer 4: persistent intentions and open loops."""

from dataclasses import dataclass
import math
from typing import Optional, List


@dataclass
class Intention:
    name: str
    priority: float
    source: str
    created_at: float
    expires_at: Optional[float] = None
    requires_user_context: bool = True


@dataclass
class OpenLoop:
    topic: str
    emotional_charge: float
    created_at: float
    last_touched: float
    urgency: float
    preferred_resolution: str
    surfaced_count: int = 0
    topic_key: str = ""
    actor_id: int | None = None
    source_event_id: str | None = None
    reason: str = "unresolved_tension"
    required_capability: str = "none"
    status: str = "pending"
    resolution_artifact_id: str | None = None
    character_position: str | None = None

    def __post_init__(self):
        if not self.topic or len(self.topic) > 240:
            raise ValueError("open-loop topic must contain 1..240 characters")
        if len(self.topic_key) > 96:
            raise ValueError("open-loop topic_key must contain at most 96 characters")
        if self.required_capability not in {"none", "language_model", "external_knowledge"}:
            raise ValueError("unsupported open-loop capability")
        if self.status not in {"pending", "ready", "surfaced", "resolved", "abandoned"}:
            raise ValueError("unsupported open-loop status")
        if self.resolution_artifact_id is not None and len(self.resolution_artifact_id) > 120:
            raise ValueError("open-loop resolution artifact id is too long")
        if self.character_position is not None and (
            not self.character_position.strip() or len(self.character_position) > 1200
        ):
            raise ValueError("open-loop character position must contain 1..1200 characters")
        for value in (self.emotional_charge, self.created_at, self.last_touched, self.urgency):
            if not math.isfinite(float(value)):
                raise ValueError("open-loop values must be finite")


class IntentionQueue:
    def __init__(self):
        self.intentions: List[Intention] = []
        self.open_loops: List[OpenLoop] = []

    def add_intention(self, intention: Intention):
        self.intentions = [i for i in self.intentions if i.name != intention.name]
        self.intentions.append(intention)

    def select_top(self, now: float) -> Optional[Intention]:
        active = [i for i in self.intentions if i.expires_at is None or i.expires_at > now]
        self.intentions = active
        if not active:
            return None
        for i in active:
            age = max(0.0, now - i.created_at)
            i.priority = max(0.0, i.priority - min(0.2, age / 3600 * 0.01))
        return max(active, key=lambda i: i.priority)

    def add_open_loop(self, loop: OpenLoop):
        key = loop.topic_key or loop.topic
        self.open_loops = [
            l for l in self.open_loops
            if (l.topic_key or l.topic) != key or l.actor_id != loop.actor_id
        ]
        self.open_loops.append(loop)
        self.open_loops = sorted(
            self.open_loops,
            key=lambda item: (-item.urgency, -item.last_touched, item.topic_key or item.topic),
        )[:64]

    def due_open_loop(
        self, now: float, min_age: float = 60.0, actor_id: int | None = None,
    ) -> Optional[OpenLoop]:
        candidates = [
            l for l in self.open_loops
            if l.status in {"pending", "ready", "surfaced"}
            and (l.actor_id is None or actor_id is None or l.actor_id == actor_id)
            and (now - l.created_at) >= min_age and (now - l.last_touched) >= min_age
        ]
        if not candidates:
            return None
        chosen = max(candidates, key=lambda l: l.urgency * l.emotional_charge / (1 + l.surfaced_count))
        chosen.last_touched = now
        chosen.surfaced_count += 1
        chosen.urgency = max(0.0, chosen.urgency - 0.2)
        return chosen

    def resolve_open_loop(self, loop: OpenLoop):
        key = loop.topic_key or loop.topic
        self.open_loops = [
            item for item in self.open_loops
            if (item.topic_key or item.topic) != key or item.actor_id != loop.actor_id
        ]

    def mark_capability_ready(self, capability: str) -> int:
        changed = 0
        for loop in self.open_loops:
            if loop.required_capability == capability and loop.status == "pending":
                loop.status = "ready"
                changed += 1
        return changed

    def decay_open_loops(self, amount: float = 0.002):
        for l in self.open_loops:
            l.urgency = max(0.0, l.urgency - amount)
        self.open_loops = [l for l in self.open_loops if l.urgency > 0.01]
