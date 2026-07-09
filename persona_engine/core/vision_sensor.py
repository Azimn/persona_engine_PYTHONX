"""Mockable vision sensor interfaces for semi-embodiment.

Vision sensors report bounded observations only. They do not identify hidden
motives, mutate relationship state, or infer emotions.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
import time


@dataclass
class VisionObservation:
    face_present: bool = False
    movement_detected: bool = False
    light_level: str = "neutral"
    scene_change: bool = False
    user_presence: str = "unknown"
    attention_estimate: str = "unknown"
    confidence: float = 1.0
    created_at: float = 0.0

    def __post_init__(self):
        if not self.created_at:
            self.created_at = time.time()
        if self.light_level not in {"dark", "dim", "neutral", "bright"}:
            self.light_level = "neutral"
        if self.user_presence not in {"unknown", "absent", "present", "active", "returned"}:
            self.user_presence = "unknown"
        self.confidence = max(0.0, min(1.0, float(self.confidence)))

    def to_safe_payload(self) -> dict:
        return asdict(self)


class VisionSensorProvider:
    """Abstract vision provider interface."""

    def poll(self) -> VisionObservation:
        raise NotImplementedError


class MockVisionSensor(VisionSensorProvider):
    """Deterministic vision sensor for tests and mobile-host integration mocks."""

    def __init__(self, observations: list[VisionObservation] | None = None):
        self.observations = list(observations or [])

    def push(self, observation: VisionObservation):
        self.observations.append(observation)

    def poll(self) -> VisionObservation:
        if self.observations:
            return self.observations.pop(0)
        return VisionObservation(confidence=1.0)


class CameraAdapter(VisionSensorProvider):
    """Host adapter placeholder.

    PC or mobile hosts should subclass this and provide platform camera
    observations. The core deliberately ships without camera dependencies.
    """

    def poll(self) -> VisionObservation:
        raise RuntimeError("No camera backend configured. Use MockVisionSensor or a host adapter.")
