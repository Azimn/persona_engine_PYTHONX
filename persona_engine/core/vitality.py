"""Seeded, bounded life events kept separate from deterministic Tide drift."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
import hashlib
from typing import Any


WHIM_ACTIONS = ("wonder", "look_around", "rehearse", "daydream", "investigate")
LIMITATION_ACTIONS = ("attention_drift", "minor_mistake", "forget_detail", "choose_easier_action", "miss_obvious_detail")
CHAOS_ACTIONS = ("strange_association", "sudden_inspiration", "unexplained_impulse", "intrusive_memory", "irrational_preference")


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


@dataclass(frozen=True)
class InterruptionResult:
    previous_activity: str
    current_activity: str
    input_arrived: bool
    attention_capture: float
    activity_interrupted: bool
    response_urgency: float
    previous_activity_interruptible: bool

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def __getitem__(self, key: str) -> Any:
        return self.to_dict()[key]


@dataclass
class LifeEvent:
    event_id: str
    tick: int
    category: str
    action: str
    origin: str
    intensity: float
    provenance: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "LifeEvent":
        return cls(**data)


@dataclass
class LifeState:
    current_activity: str = "quiet observation"
    current_intention: str = "maintain awareness"
    attention_target: str = "immediate surroundings"
    unresolved_concern: str = "none"
    activity_status: str = "active"
    interrupted_activity: str | None = None
    entropy: float = 0.0
    rng_counter: int = 0
    events: list[LifeEvent] = field(default_factory=list)
    last_catch_up_steps: int = 0
    last_catch_up_seconds: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        raw = asdict(self)
        return raw

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> "LifeState":
        if not data:
            return cls()
        raw = dict(data)
        raw["events"] = [LifeEvent.from_dict(item) for item in raw.get("events", [])]
        return cls(**raw)


class VitalityEventEngine:
    """Counter-based randomness makes every draw replayable after persistence."""

    def __init__(self, seed: int, enabled: bool = True, whim_rate: float = 0.22,
                 limitation_rate: float = 0.10, chaos_rate: float = 0.002, entropy_rate: float = 0.08):
        self.seed = int(seed) & 0xFFFFFFFFFFFFFFFF
        self.enabled = bool(enabled)
        self.whim_rate = max(0.0, min(1.0, float(whim_rate)))
        self.limitation_rate = max(0.0, min(1.0, float(limitation_rate)))
        self.chaos_rate = max(0.0, min(0.05, float(chaos_rate)))
        self.entropy_rate = max(0.0, min(1.0, float(entropy_rate)))

    def _draw(self, state: LifeState, channel: str) -> float:
        payload = f"{self.seed}:{state.rng_counter}:{channel}".encode("utf-8")
        state.rng_counter += 1
        value = int.from_bytes(hashlib.blake2b(payload, digest_size=8).digest(), "big")
        return value / float(2**64 - 1)

    def _choose(self, state: LifeState, channel: str, options: tuple[str, ...], weights: dict[str, float] | None = None) -> str:
        weighted = [(item, max(0.0, float((weights or {}).get(item, 1.0)))) for item in options]
        total = sum(weight for _, weight in weighted) or float(len(weighted))
        point = self._draw(state, channel) * total
        cumulative = 0.0
        for item, weight in weighted:
            cumulative += weight or (1.0 if total == len(weighted) else 0.0)
            if point <= cumulative:
                return item
        return weighted[-1][0]

    def tick(self, state: LifeState, tick: int, elapsed_seconds: float = 5.0,
             whim_weights: dict[str, float] | None = None, force_category: str | None = None) -> list[LifeEvent]:
        if not self.enabled:
            return []
        state.entropy = min(1.0, state.entropy + self.entropy_rate * max(0.1, elapsed_seconds / 5.0))
        category = force_category
        if category is None and self._draw(state, "chaos_gate") < self.chaos_rate:
            category = "chaos"
        elif category is None and state.entropy >= 0.65:
            roll = self._draw(state, "ordinary_gate")
            if roll < self.limitation_rate:
                category = "limitation"
            elif roll < self.limitation_rate + self.whim_rate:
                category = "whim"
        if category not in {"whim", "limitation", "chaos"}:
            return []
        options = WHIM_ACTIONS if category == "whim" else LIMITATION_ACTIONS if category == "limitation" else CHAOS_ACTIONS
        action = self._choose(state, f"{category}_choice", options, whim_weights if category == "whim" else None)
        event = LifeEvent(
            event_id=f"life_{tick}_{state.rng_counter}", tick=int(tick), category=category, action=action,
            origin="chaos" if category == "chaos" else "personality_weighted" if category == "whim" else "ordinary_limitation",
            intensity=round(0.15 + self._draw(state, f"{category}_intensity") * 0.35, 4),
            provenance={"seed": self.seed, "counter": state.rng_counter - 1, "forced": force_category is not None},
        )
        state.events.append(event)
        state.events = state.events[-100:]
        state.entropy = max(0.0, state.entropy - (0.55 if category != "chaos" else 0.15))
        if category == "whim":
            state.current_activity = action.replace("_", " ")
            state.activity_status = "active"
        elif category == "limitation":
            state.attention_target = "uncertain"
        return [event]

    def interrupt(
        self,
        state: LifeState,
        interruption: str,
        *,
        previous_activity_interruptible: bool = True,
        interruption_sensitivity: float = 0.5,
        direct_address: bool = False,
    ) -> InterruptionResult:
        previous = state.current_activity
        text = str(interruption).strip()
        lowered = text.lower()
        input_arrived = bool(text)
        urgency_cues = ("urgent", "help", "now", "stop", "listen", "danger", "please answer")
        direct_cues = ("you", "your", "?", "!")
        question_directed = "?" in text or " asks " in f" {lowered} " or lowered.startswith("ask ")
        urgency = _clamp(
            0.18
            + 0.18 * text.count("!")
            + 0.42 * any(cue in lowered for cue in urgency_cues)
            + 0.58 * question_directed
            + 0.60 * bool(direct_address)
        ) if input_arrived else 0.0
        capture = _clamp(
            0.18
            + 0.36 * _clamp(interruption_sensitivity)
            + 0.18 * any(cue in lowered for cue in direct_cues)
            + 0.24 * urgency
        ) if input_arrived else 0.0
        interrupted = bool(previous_activity_interruptible and capture >= 0.55)
        if input_arrived:
            # Preserve the prior activity for the existing resume/abandon
            # resolver even when attention capture did not fully interrupt it.
            state.interrupted_activity = previous
        if interrupted:
            state.current_activity = "responding to interruption"
            state.activity_status = "interrupted"
        if capture >= 0.30:
            state.attention_target = text[:120]
        return InterruptionResult(
            previous_activity=previous,
            current_activity=state.current_activity,
            input_arrived=input_arrived,
            attention_capture=round(capture, 6),
            activity_interrupted=interrupted,
            response_urgency=round(urgency, 6),
            previous_activity_interruptible=bool(previous_activity_interruptible),
        )

    def resolve_interruption(self, state: LifeState, pressure: float, limitation: bool = False) -> str:
        if limitation or pressure > 0.75:
            state.activity_status = "abandoned"
            state.current_activity = "recovering attention"
            outcome = "abandoned"
        elif state.interrupted_activity:
            state.current_activity = state.interrupted_activity
            state.activity_status = "resumed"
            outcome = "resumed"
        else:
            state.current_activity = "quiet observation"
            state.activity_status = "changed"
            outcome = "changed"
        state.interrupted_activity = None
        return outcome

    def catch_up(self, state: LifeState, start_tick: int, elapsed_seconds: float,
                 max_steps: int = 12, whim_weights: dict[str, float] | None = None) -> list[LifeEvent]:
        steps = min(max_steps, max(0, int(elapsed_seconds / 300.0)))
        state.last_catch_up_steps = steps
        state.last_catch_up_seconds = max(0.0, float(elapsed_seconds))
        events: list[LifeEvent] = []
        for offset in range(steps):
            events.extend(self.tick(state, start_tick + offset, elapsed_seconds=max(5.0, elapsed_seconds / max(1, steps)), whim_weights=whim_weights))
        return events
