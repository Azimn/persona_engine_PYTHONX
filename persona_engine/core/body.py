"""Generic somatic state for the artificial character organism.

The engine owns mechanics. Character-specific body preferences and thresholds
come from cartridge data and are represented as BodyProfile. BodyState is the
mutable instance state: what this running organism is currently undergoing.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any


@dataclass
class BodyProfile:
    """Character-specific somatic parameters loaded from the cartridge."""

    baseline_energy: float = 0.75
    baseline_tension: float = 0.25
    baseline_comfort: float = 0.75
    restlessness_gain: float = 0.015
    stillness_discomfort_threshold_seconds: float = 900.0
    sensory_load_sensitivity: float = 0.50
    fatigue_decay_rate: float = 0.010
    recovery_rate: float = 0.020
    movement_need_gain: float = 0.015
    preferred_posture: str = "settled"
    preferred_orientation: str = "toward_user"

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> "BodyProfile":
        data = dict(data or {})
        allowed = {field for field in cls.__dataclass_fields__}
        return cls(**{k: v for k, v in data.items() if k in allowed})


@dataclass
class BodyState:
    """Mutable somatic state for one character instance."""

    energy: float = 0.75
    tension: float = 0.25
    comfort: float = 0.75
    fatigue: float = 0.0
    sensory_load: float = 0.0
    stillness_seconds: float = 0.0
    posture: str = "settled"
    orientation: str = "toward_user"
    attention_target: str = "none"
    need_for_movement: float = 0.0
    recovery_state: str = "stable"

    @classmethod
    def from_profile(cls, profile: BodyProfile) -> "BodyState":
        return cls(
            energy=profile.baseline_energy,
            tension=profile.baseline_tension,
            comfort=profile.baseline_comfort,
            posture=profile.preferred_posture,
            orientation=profile.preferred_orientation,
        )

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None, profile: BodyProfile) -> "BodyState":
        if not data:
            return cls.from_profile(profile)
        allowed = {field for field in cls.__dataclass_fields__}
        base = asdict(cls.from_profile(profile))
        base.update({k: v for k, v in data.items() if k in allowed})
        return cls(**base)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def apply_idle(self, elapsed_seconds: float, profile: BodyProfile, sensory_delta: float = 0.0):
        """Update body state during silence or background time."""

        elapsed_seconds = max(0.0, elapsed_seconds)
        steps = max(1.0, elapsed_seconds / 5.0)
        self.stillness_seconds += elapsed_seconds
        self.sensory_load = max(0.0, min(1.0, self.sensory_load + sensory_delta * profile.sensory_load_sensitivity))
        self.fatigue = max(0.0, min(1.0, self.fatigue + profile.fatigue_decay_rate * steps * (0.35 + self.sensory_load)))
        self.energy = max(0.0, min(1.0, self.energy - profile.fatigue_decay_rate * steps * 0.25 + profile.recovery_rate * steps * 0.08))
        if self.stillness_seconds > profile.stillness_discomfort_threshold_seconds:
            over = min(1.0, (self.stillness_seconds - profile.stillness_discomfort_threshold_seconds) / max(profile.stillness_discomfort_threshold_seconds, 1.0))
            self.need_for_movement = min(1.0, self.need_for_movement + profile.movement_need_gain * steps + over * 0.02)
            self.tension = min(1.0, self.tension + profile.restlessness_gain * steps * 0.5)
            self.comfort = max(0.0, self.comfort - over * 0.01)
        else:
            self.need_for_movement = max(0.0, self.need_for_movement - profile.recovery_rate * steps)
            self.tension = max(0.0, self.tension - profile.recovery_rate * steps * 0.2)
        self._update_recovery_state()

    def apply_interaction(self, intensity: float = 0.1):
        """Update body state when a fresh interaction happens."""

        self.stillness_seconds = 0.0
        self.attention_target = "user"
        self.orientation = "toward_user"
        self.sensory_load = min(1.0, self.sensory_load + max(0.0, intensity) * 0.15)
        self.need_for_movement = max(0.0, self.need_for_movement - 0.05)
        self._update_recovery_state()

    def apply_ambient_load(self, load: float):
        self.sensory_load = max(0.0, min(1.0, self.sensory_load + load))
        self.tension = max(0.0, min(1.0, self.tension + load * 0.25))
        self._update_recovery_state()

    def _update_recovery_state(self):
        if self.fatigue > 0.75 or self.energy < 0.25:
            self.recovery_state = "depleted"
        elif self.sensory_load > 0.70 or self.tension > 0.70:
            self.recovery_state = "strained"
        elif self.need_for_movement > 0.65:
            self.recovery_state = "restless"
        else:
            self.recovery_state = "stable"

    def summary(self) -> str:
        return (
            f"Body is {self.recovery_state}; posture is {self.posture}; orientation is {self.orientation}; "
            f"attention is on {self.attention_target}; sensory load is {_bucket(self.sensory_load)}; "
            f"movement need is {_bucket(self.need_for_movement)}."
        )


def _bucket(value: float) -> str:
    if value >= 0.70:
        return "high"
    if value >= 0.35:
        return "moderate"
    return "low"
