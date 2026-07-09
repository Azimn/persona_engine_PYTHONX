"""Mockable audio sensor interfaces for semi-embodiment.

Audio sensors report bounded observations only. They do not infer emotion,
mutate pressure, or decide what the character believes.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
import time


@dataclass
class AudioObservation:
    sound_level: str = "low"
    sudden_onset: bool = False
    speech_activity: bool = False
    silence_duration: float = 0.0
    interruption_detected: bool = False
    speaker_present: bool = False
    confidence: float = 1.0
    created_at: float = 0.0

    def __post_init__(self):
        if not self.created_at:
            self.created_at = time.time()
        if self.sound_level not in {"silent", "low", "moderate", "high"}:
            self.sound_level = "moderate"
        self.confidence = max(0.0, min(1.0, float(self.confidence)))

    def to_safe_payload(self) -> dict:
        return asdict(self)


class AudioSensorProvider:
    """Abstract audio provider interface."""

    def poll(self) -> AudioObservation:
        raise NotImplementedError


class MockAudioSensor(AudioSensorProvider):
    """Deterministic audio sensor for tests and mobile-host integration mocks."""

    def __init__(self, observations: list[AudioObservation] | None = None):
        self.observations = list(observations or [])

    def push(self, observation: AudioObservation):
        self.observations.append(observation)

    def poll(self) -> AudioObservation:
        if self.observations:
            return self.observations.pop(0)
        return AudioObservation(sound_level="low", confidence=1.0)


class MicrophoneAdapter(AudioSensorProvider):
    """Host adapter placeholder.

    PC or mobile hosts should subclass this and provide platform microphone
    observations. The core deliberately ships without microphone dependencies.
    """

    def poll(self) -> AudioObservation:
        raise RuntimeError("No microphone backend configured. Use MockAudioSensor or a host adapter.")
