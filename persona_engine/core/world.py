"""Generic artificial world state.

World mechanics are character-agnostic. Character-specific preferences such as
preferred light, noise, and absence sensitivity are loaded from the cartridge as
WorldProfile. The mutable WorldState belongs to a running session.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field, asdict
from typing import Any


@dataclass
class WorldProfile:
    preferred_light: str = "neutral"
    preferred_noise: str = "low"
    absence_sensitivity: float = 0.50
    ambient_change_sensitivity: float = 0.50
    routine_disruption_sensitivity: float = 0.50
    default_zone: str = "room"
    default_objects: list[str] = field(default_factory=list)
    ambient_change_bias: str = "cautious_attention"

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> "WorldProfile":
        data = dict(data or {})
        allowed = {field for field in cls.__dataclass_fields__}
        return cls(**{k: v for k, v in data.items() if k in allowed})


@dataclass
class WorldEvent:
    kind: str
    detail: str
    intensity: float
    created_at: float
    visible_to_character: bool = True


@dataclass
class WorldState:
    zone: str = "room"
    light_level: str = "neutral"
    noise_level: str = "low"
    user_presence: str = "unknown"
    last_user_seen_at: float = 0.0
    ambient_events: list[WorldEvent] = field(default_factory=list)
    objects: list[str] = field(default_factory=list)
    routine_state: str = "stable"
    time_of_day: str = "unknown"

    @classmethod
    def from_profile(cls, profile: WorldProfile) -> "WorldState":
        return cls(zone=profile.default_zone, light_level=profile.preferred_light, noise_level=profile.preferred_noise, objects=list(profile.default_objects))

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None, profile: WorldProfile) -> "WorldState":
        if not data:
            return cls.from_profile(profile)
        base = asdict(cls.from_profile(profile))
        base.update({k: v for k, v in data.items() if k in cls.__dataclass_fields__})
        events = []
        for ev in base.get("ambient_events", []) or []:
            if isinstance(ev, WorldEvent):
                events.append(ev)
            elif isinstance(ev, dict):
                events.append(WorldEvent(**{k: ev[k] for k in ev if k in WorldEvent.__dataclass_fields__}))
        base["ambient_events"] = events
        return cls(**base)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["ambient_events"] = [asdict(e) for e in self.ambient_events]
        return data

    def apply_host_facts(self, server_truth: dict[str, Any], visible_context: dict[str, Any], now: float | None = None) -> list[WorldEvent]:
        """Update world from host/server facts and return newly observed events."""

        now = now or time.time()
        events: list[WorldEvent] = []
        merged = {**(server_truth or {}), **(visible_context or {})}
        if "user_presence" in merged:
            presence = str(merged["user_presence"])
            if presence != self.user_presence:
                events.append(WorldEvent("presence_change", f"user_presence changed to {presence}", 0.45, now))
            self.user_presence = presence
            if presence in {"present", "returned", "active"}:
                self.last_user_seen_at = now
        if "light_level" in merged:
            light = str(merged["light_level"])
            if light != self.light_level:
                events.append(WorldEvent("light_change", f"light_level is {light}", 0.30, now))
            self.light_level = light
        if "noise_level" in merged:
            noise = str(merged["noise_level"])
            if noise != self.noise_level:
                events.append(WorldEvent("noise_change", f"noise_level is {noise}", 0.35, now))
            self.noise_level = noise
        for key in ("ambient_event", "sound", "movement", "room_sound"):
            if key in merged:
                detail = str(merged[key])[:160]
                events.append(WorldEvent("ambient_event", detail, 0.55, now))
        if "routine_state" in merged:
            routine = str(merged["routine_state"])
            if routine != self.routine_state:
                events.append(WorldEvent("routine_change", f"routine_state is {routine}", 0.45, now))
            self.routine_state = routine
        if "time_of_day" in merged:
            self.time_of_day = str(merged["time_of_day"])
        if "zone" in merged:
            self.zone = str(merged["zone"])
        for ev in events:
            self.ambient_events.append(ev)
        self.ambient_events = self.ambient_events[-50:]
        return events

    def idle_events(self, elapsed_seconds: float, profile: WorldProfile, now: float | None = None) -> list[WorldEvent]:
        """Generate world events that arise from absence or quiet time."""

        now = now or time.time()
        events: list[WorldEvent] = []
        if elapsed_seconds >= 60 and self.user_presence not in {"present", "active"}:
            minutes = int(elapsed_seconds / 60)
            intensity = min(1.0, profile.absence_sensitivity * min(1.0, minutes / 60.0))
            events.append(WorldEvent("user_absence", f"user absent for {minutes} minutes", intensity, now))
        if self.noise_level == "high":
            events.append(WorldEvent("sensory_load", "noise_level is high", profile.ambient_change_sensitivity, now))
        if self.light_level not in {profile.preferred_light, "neutral"}:
            events.append(WorldEvent("comfort_mismatch", f"light_level is {self.light_level}", 0.25 * profile.ambient_change_sensitivity, now))
        for ev in events:
            self.ambient_events.append(ev)
        self.ambient_events = self.ambient_events[-50:]
        return events

    def summary(self) -> str:
        return (
            f"World zone is {self.zone}; light is {self.light_level}; noise is {self.noise_level}; "
            f"user presence is {self.user_presence}; routine is {self.routine_state}; time of day is {self.time_of_day}."
        )
