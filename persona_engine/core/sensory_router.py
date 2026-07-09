"""Routes bounded sensor observations into world-authority facts."""

from __future__ import annotations

from dataclasses import dataclass
from .audio_sensor import AudioObservation
from .vision_sensor import VisionObservation
from .world_authority import WorldAuthority, WorldResolution


@dataclass
class RoutedSensoryEvent:
    sensor_type: str
    resolution: WorldResolution


class SensoryRouter:
    """Converts audio and vision observations into objective world facts.

    The router never mutates pressures, relationship, identity, or memory.
    """

    def route_audio(self, observation: AudioObservation, authority: WorldAuthority) -> RoutedSensoryEvent:
        payload = observation.to_safe_payload()
        resolution = authority.apply_sensor_event("audio", payload, confidence=observation.confidence)
        return RoutedSensoryEvent("audio", resolution)

    def route_vision(self, observation: VisionObservation, authority: WorldAuthority) -> RoutedSensoryEvent:
        payload = observation.to_safe_payload()
        resolution = authority.apply_sensor_event("vision", payload, confidence=observation.confidence)
        return RoutedSensoryEvent("vision", resolution)
