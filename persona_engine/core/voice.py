"""Voice planning for TTS hosts.

The voice module receives finished text and an expression envelope. It plans how
speech should be performed, but it never decides what is said and never mutates
organism state.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from .performance import PerformancePlan


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
    performance_plan_id: str | None = None

    def to_dict(self) -> dict:
        return asdict(self)


class VoicePlanner:
    def __init__(self, profile: VoiceProfile | None = None):
        self.profile = profile or VoiceProfile()

    def plan(self, text: str, performance_plan: "PerformancePlan | None", envelope=None) -> VoicePlan:
        # Backward compatibility for hosts that still pass (text, envelope).
        if envelope is None and performance_plan is not None and not hasattr(performance_plan, "acts"):
            envelope = performance_plan
            performance_plan = None
        guarded = float(getattr(envelope, "guardedness", 0.0))
        warmth = float(getattr(envelope, "warmth", 0.5))
        directness = float(getattr(performance_plan, "directness", 0.5)) if performance_plan else 0.5
        rate = self.profile.default_rate
        if guarded > 0.70:
            rate = "slow"
        elif warmth > 0.70 and rate == "normal":
            rate = "fluid"
        volume = self.profile.default_volume
        if guarded > 0.65:
            volume = "low"
        pause_before = int(150 + guarded * 700 + max(0.0, 0.5 - directness) * 180)
        pause_after = int(100 + max(0.0, 1.0 - warmth) * 450)
        hesitation = guarded + self.profile.hesitation_bias > 0.85
        interruptible = self.profile.interruptible
        if performance_plan and performance_plan.acts:
            interruptible = all(act.suppressible for act in performance_plan.acts)
            voice_act = next((act for act in performance_plan.acts if act.channel == "voice"), None)
            timing_act = next((act for act in performance_plan.acts if act.channel == "timing"), None)
            if voice_act:
                rate = {
                    "clipped": "fast",
                    "measured": "slow",
                    "fluid": "fluid",
                    "expansive": "fluid",
                    "quiet": "slow",
                }.get(voice_act.function, rate)
                if voice_act.function == "quiet":
                    volume = "low"
            if timing_act:
                pause_before = max(pause_before, {
                    "immediate": 0,
                    "brief": 250,
                    "delayed": 900,
                    "variable": 500,
                    "delay": 1000,
                    "hesitate": 650,
                    "brief_pause": 450,
                }.get(timing_act.function, pause_before))
        return VoicePlan(
            str(text), rate, volume, pause_before, pause_after, hesitation,
            bool(interruptible),
            getattr(performance_plan, "plan_id", None),
        )


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
