"""Voice planning for TTS hosts.

The voice module receives finished text and an expression envelope. It plans how
speech should be performed, but it never decides what is said and never mutates
organism state.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any


@dataclass(frozen=True)
class VoiceProfile:
    default_rate: str = "normal"
    default_volume: str = "medium"
    hesitation_bias: float = 0.0
    interruptible: bool = True

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> "VoiceProfile":
        data = dict(data or {})
        allowed = {field for field in cls.__dataclass_fields__}
        return cls(**{k: v for k, v in data.items() if k in allowed})


@dataclass(frozen=True)
class VoicePlan:
    text: str
    rate_bucket: str
    volume_bucket: str
    pause_before_ms: int
    pause_after_ms: int
    hesitation: bool
    interruptible: bool

    def to_dict(self) -> dict:
        return asdict(self)


class VoicePlanner:
    def __init__(self, profile: VoiceProfile | None = None):
        self.profile = profile or VoiceProfile()

    def plan(self, text: str, envelope) -> VoicePlan:
        guarded = float(getattr(envelope, "guardedness", 0.0))
        warmth = float(getattr(envelope, "warmth", 0.5))
        rate = self.profile.default_rate
        if guarded > 0.70:
            rate = "slow"
        elif warmth > 0.70 and rate == "normal":
            rate = "fluid"
        volume = self.profile.default_volume
        if guarded > 0.65:
            volume = "low"
        pause_before = int(150 + guarded * 700)
        pause_after = int(100 + max(0.0, 1.0 - warmth) * 450)
        hesitation = guarded + self.profile.hesitation_bias > 0.85
        return VoicePlan(str(text), rate, volume, pause_before, pause_after, hesitation, bool(self.profile.interruptible))


class TTSAdapter:
    """Host TTS interface. Platform code may implement speak()."""

    def speak(self, plan: VoicePlan):
        raise NotImplementedError


class MockTTSAdapter(TTSAdapter):
    """Deterministic TTS adapter for tests."""

    def __init__(self):
        self.spoken: list[VoicePlan] = []

    def speak(self, plan: VoicePlan):
        self.spoken.append(plan)
        return {"spoken": True, "plan": plan.to_dict()}
