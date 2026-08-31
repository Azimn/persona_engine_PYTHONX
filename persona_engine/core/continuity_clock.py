"""Linear subject-time authority for Project Wayfarer.

The clock answers one question only: how much elapsed time has the continuing
subject actually accumulated? It does not decide what that duration means
psychologically. Body, affect, relationship, memory, and scheduler systems may
consume elapsed time only through their own explicit contracts.

Wall-clock regressions never make subject time run backward. Timezone metadata is
portable context, not part of elapsed-time arithmetic.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ClockAdvance:
    elapsed_seconds: float
    subject_elapsed_seconds: float
    prior_wall_time: float
    observed_wall_time: float
    backward_correction_seconds: float = 0.0
    source: str = "wall_clock"

    @property
    def duration_bucket(self) -> str:
        seconds = self.elapsed_seconds
        if seconds < 60.0:
            return "seconds"
        if seconds < 3600.0:
            return "minutes"
        if seconds < 86400.0:
            return "hours"
        return "days"

    def to_payload(self) -> dict:
        return {
            "elapsed_seconds": round(float(self.elapsed_seconds), 6),
            "subject_elapsed_seconds": round(float(self.subject_elapsed_seconds), 6),
            "prior_wall_time": float(self.prior_wall_time),
            "observed_wall_time": float(self.observed_wall_time),
            "backward_correction_seconds": round(float(self.backward_correction_seconds), 6),
            "duration_bucket": self.duration_bucket,
            "source": self.source,
        }


@dataclass
class ContinuityClock:
    """Monotonic elapsed subject time plus a fallible wall-clock anchor."""

    subject_elapsed_seconds: float = 0.0
    last_wall_time: float = 0.0
    timezone_name: str = "unknown"
    correction_count: int = 0

    @classmethod
    def from_dict(cls, data: dict | None) -> "ContinuityClock":
        data = dict(data or {})
        return cls(
            subject_elapsed_seconds=max(0.0, float(data.get("subject_elapsed_seconds", 0.0))),
            last_wall_time=float(data.get("last_wall_time", 0.0)),
            timezone_name=str(data.get("timezone_name", "unknown") or "unknown"),
            correction_count=max(0, int(data.get("correction_count", 0))),
        )

    def to_dict(self) -> dict:
        """Return the canonical persisted clock representation.

        Subject elapsed time uses the same six-decimal precision as canonical
        time-advance payloads so restart and host handoff reconstruct exactly
        the state that was digested at the persistence boundary. Live elapsed
        arithmetic remains full Python float precision between writes.
        """
        return {
            "subject_elapsed_seconds": round(float(self.subject_elapsed_seconds), 6),
            "last_wall_time": float(self.last_wall_time),
            "timezone_name": str(self.timezone_name or "unknown"),
            "correction_count": max(0, int(self.correction_count)),
        }

    def observe_wall(self, observed_wall_time: float, *, source: str = "wall_clock_catchup") -> ClockAdvance:
        observed = float(observed_wall_time)
        prior = float(self.last_wall_time or observed)
        raw_delta = observed - prior
        if raw_delta < 0.0:
            self.correction_count += 1
            self.last_wall_time = observed
            return ClockAdvance(
                elapsed_seconds=0.0,
                subject_elapsed_seconds=self.subject_elapsed_seconds,
                prior_wall_time=prior,
                observed_wall_time=observed,
                backward_correction_seconds=abs(raw_delta),
                source=source,
            )
        elapsed = max(0.0, raw_delta)
        self.subject_elapsed_seconds += elapsed
        self.last_wall_time = observed
        return ClockAdvance(
            elapsed_seconds=elapsed,
            subject_elapsed_seconds=self.subject_elapsed_seconds,
            prior_wall_time=prior,
            observed_wall_time=observed,
            source=source,
        )

    def advance_by(self, elapsed_seconds: float, *, observed_wall_time: float, source: str = "explicit") -> ClockAdvance:
        elapsed = max(0.0, float(elapsed_seconds))
        prior = float(self.last_wall_time or observed_wall_time)
        self.subject_elapsed_seconds += elapsed
        self.last_wall_time = float(observed_wall_time)
        return ClockAdvance(
            elapsed_seconds=elapsed,
            subject_elapsed_seconds=self.subject_elapsed_seconds,
            prior_wall_time=prior,
            observed_wall_time=float(observed_wall_time),
            source=source,
        )
