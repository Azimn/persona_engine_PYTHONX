"""Layer 4: persistent intentions and open loops.

Commitments deliberately reuse the intention persistence path. They are not a
second motivational system. Optional commitment metadata marks an intention as
a durable conduct constraint; decision code evaluates those constraints
separately from ordinary intention priority.
"""

from dataclasses import dataclass
from typing import Optional, List


@dataclass
class Intention:
    name: str
    priority: float
    source: str
    created_at: float
    expires_at: Optional[float] = None
    requires_user_context: bool = True
    commitment_kind: Optional[str] = None
    commitment_target: Optional[str] = None


@dataclass
class OpenLoop:
    topic: str
    emotional_charge: float
    created_at: float
    last_touched: float
    urgency: float
    preferred_resolution: str
    surfaced_count: int = 0


class IntentionQueue:
    def __init__(self):
        self.intentions: List[Intention] = []
        self.open_loops: List[OpenLoop] = []

    def add_intention(self, intention: Intention):
        self.intentions = [i for i in self.intentions if i.name != intention.name]
        self.intentions.append(intention)

    def _prune_expired(self, now: float) -> None:
        self.intentions = [i for i in self.intentions if i.expires_at is None or i.expires_at > now]

    def active_commitments(self, now: float) -> List[Intention]:
        """Return active typed commitment constraints without ranking them.

        A commitment is normative state, not merely the highest-priority current
        goal. Priority therefore does not determine whether the constraint exists.
        """

        self._prune_expired(now)
        return [
            intention
            for intention in self.intentions
            if intention.commitment_kind and intention.commitment_target
        ]

    def select_top(self, now: float) -> Optional[Intention]:
        self._prune_expired(now)
        active = list(self.intentions)
        if not active:
            return None
        for i in active:
            age = max(0.0, now - i.created_at)
            i.priority = max(0.0, i.priority - min(0.2, age / 3600 * 0.01))
        return max(active, key=lambda i: i.priority)

    def add_open_loop(self, loop: OpenLoop):
        self.open_loops = [l for l in self.open_loops if l.topic != loop.topic]
        self.open_loops.append(loop)

    def due_open_loop(self, now: float, min_age: float = 60.0) -> Optional[OpenLoop]:
        candidates = [l for l in self.open_loops if (now - l.created_at) >= min_age and (now - l.last_touched) >= min_age]
        if not candidates:
            return None
        chosen = max(candidates, key=lambda l: l.urgency * l.emotional_charge / (1 + l.surfaced_count))
        chosen.last_touched = now
        chosen.surfaced_count += 1
        chosen.urgency = max(0.0, chosen.urgency - 0.2)
        return chosen

    def resolve_open_loop(self, loop: OpenLoop):
        self.open_loops = [l for l in self.open_loops if l.topic != loop.topic]

    def decay_open_loops(self, amount: float = 0.002):
        for l in self.open_loops:
            l.urgency = max(0.0, l.urgency - amount)
        self.open_loops = [l for l in self.open_loops if l.urgency > 0.01]
