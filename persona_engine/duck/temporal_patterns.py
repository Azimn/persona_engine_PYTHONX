"""Learn recurring civil-time expectations using circular Beat Time statistics."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import math
from typing import Any


@dataclass
class RoutineStats:
    count: int = 0
    sum_sin: float = 0.0
    sum_cos: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "RoutineStats":
        return cls(int(raw.get("count", 0)), float(raw.get("sum_sin", 0.0)), float(raw.get("sum_cos", 0.0)))

    @property
    def expected_beat(self) -> float | None:
        if self.count <= 0:
            return None
        angle = math.atan2(self.sum_sin, self.sum_cos)
        if angle < 0.0:
            angle += math.tau
        return (angle / math.tau) * 1000.0

    @property
    def concentration(self) -> float:
        if self.count <= 0:
            return 0.0
        return min(1.0, math.hypot(self.sum_sin, self.sum_cos) / self.count)


class TemporalPatternBank:
    """Persistent learned timing models keyed by relationship/event concept."""

    def __init__(self, routines: dict[str, RoutineStats] | None = None):
        self.routines = dict(routines or {})

    @staticmethod
    def circular_distance_beats(a: float, b: float) -> float:
        delta = abs(float(a) - float(b)) % 1000.0
        return min(delta, 1000.0 - delta)

    def assess(self, key: str, beat: float, *, minimum_observations: int = 3) -> dict[str, Any]:
        stats = self.routines.get(str(key))
        if stats is None or stats.count < minimum_observations or stats.expected_beat is None:
            return {"key": str(key), "learned": False, "observations": 0 if stats is None else stats.count}
        distance = self.circular_distance_beats(float(beat), stats.expected_beat)
        # High concentration means a narrow learned routine. Low concentration
        # deliberately widens the tolerated band instead of manufacturing surprise.
        tolerance = max(30.0, 180.0 * (1.0 - stats.concentration))
        score = min(1.0, distance / max(tolerance, 1.0))
        return {
            "key": str(key),
            "learned": True,
            "observations": stats.count,
            "expected_beat": round(stats.expected_beat, 3),
            "observed_beat": round(float(beat) % 1000.0, 3),
            "distance_beats": round(distance, 3),
            "concentration": round(stats.concentration, 6),
            "anomaly_score": round(score, 6),
            "unexpected": score >= 1.0,
        }

    def observe(self, key: str, beat: float) -> RoutineStats:
        key = str(key)
        stats = self.routines.setdefault(key, RoutineStats())
        angle = (float(beat) % 1000.0) / 1000.0 * math.tau
        stats.count += 1
        stats.sum_sin += math.sin(angle)
        stats.sum_cos += math.cos(angle)
        return stats

    def assess_then_observe(self, key: str, beat: float) -> dict[str, Any]:
        assessment = self.assess(key, beat)
        self.observe(key, beat)
        assessment["observations_after"] = self.routines[str(key)].count
        return assessment

    def to_dict(self) -> dict[str, Any]:
        return {"routines": {key: self.routines[key].to_dict() for key in sorted(self.routines)}}

    @classmethod
    def from_dict(cls, raw: dict[str, Any] | None) -> "TemporalPatternBank":
        raw = dict(raw or {})
        return cls({str(key): RoutineStats.from_dict(value) for key, value in raw.get("routines", {}).items()})
