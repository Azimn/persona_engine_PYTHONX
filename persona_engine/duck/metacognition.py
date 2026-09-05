"""Calibration-oriented metacognition for DUCK."""

from __future__ import annotations

from collections import deque

from .types import clamp


class CalibrationMonitor:
    def __init__(self, width: int = 32, *, state: dict | None = None):
        self.width = max(1, int(width))
        self.world_errors = deque(maxlen=self.width)
        self.self_errors = deque(maxlen=self.width)
        self.last_simulation_confidence = 0.0
        if state:
            self.restore(state)

    def snapshot(self) -> dict:
        return {
            "width": self.width,
            "world_errors": list(self.world_errors),
            "self_errors": list(self.self_errors),
            "last_simulation_confidence": self.last_simulation_confidence,
        }

    def restore(self, state: dict | None) -> None:
        state = state or {}
        self.width = max(1, int(state.get("width", self.width)))
        self.world_errors = deque([max(0.0, float(v)) for v in state.get("world_errors", [])], maxlen=self.width)
        self.self_errors = deque([max(0.0, float(v)) for v in state.get("self_errors", [])], maxlen=self.width)
        self.last_simulation_confidence = clamp(state.get("last_simulation_confidence", 0.0))

    def observe(self, *, world_error: float, self_error: float, simulation_confidence: float) -> None:
        self.world_errors.append(max(0.0, float(world_error)))
        self.self_errors.append(max(0.0, float(self_error)))
        self.last_simulation_confidence = clamp(simulation_confidence)

    @staticmethod
    def _mean(values) -> float:
        return sum(values) / len(values) if values else 0.0

    def report(self) -> dict:
        world_error = self._mean(self.world_errors)
        self_error = self._mean(self.self_errors)
        world_confidence = clamp(1.0 - world_error)
        self_confidence = clamp(1.0 - self_error)
        calibration_gap = abs(self.last_simulation_confidence - ((world_confidence + self_confidence) / 2.0))
        return {
            "world_prediction_confidence": world_confidence,
            "self_prediction_confidence": self_confidence,
            "simulation_reported_confidence": self.last_simulation_confidence,
            "calibration_gap": calibration_gap,
            "uncertainty": clamp(1.0 - ((world_confidence + self_confidence) / 2.0)),
            "observations": max(len(self.world_errors), len(self.self_errors)),
        }
