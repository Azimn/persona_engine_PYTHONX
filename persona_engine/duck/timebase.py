"""Explicit temporal observations for the DUCK organism.

Causal order, lived duration, and civil time are different quantities. DUCK's
logical tick orders cognitive transitions. Wayfarer's ContinuityClock owns the
continuing subject's monotonic elapsed duration. This module accepts explicit
civil-time evidence and derives Swatch Internet Time without consulting the host
clock implicitly, which keeps replay deterministic.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any

BEATS_PER_DAY = 1000.0
SECONDS_PER_DAY = 86400.0
SECONDS_PER_BEAT = SECONDS_PER_DAY / BEATS_PER_DAY
BMT_OFFSET_SECONDS = 3600.0


@dataclass(frozen=True)
class TemporalStamp:
    logical_tick: int
    source: str
    utc_epoch: float | None = None
    utc_iso: str | None = None
    bmt_date: str | None = None
    beat: float | None = None
    elapsed_since_prior_utc: float | None = None
    clock_regression_seconds: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class TemporalAuthority:
    """Derive portable civil-time metadata from explicit observations only."""

    def __init__(self, last_utc_epoch: float | None = None):
        self.last_utc_epoch = None if last_utc_epoch is None else float(last_utc_epoch)
        self.last_stamp: TemporalStamp | None = None

    @staticmethod
    def _civil_fields(utc_epoch: float) -> tuple[str, str, float]:
        utc_dt = datetime.fromtimestamp(float(utc_epoch), tz=timezone.utc)
        seconds = utc_dt.hour * 3600.0 + utc_dt.minute * 60.0 + utc_dt.second + utc_dt.microsecond / 1_000_000.0
        beat = ((seconds + BMT_OFFSET_SECONDS) % SECONDS_PER_DAY) / SECONDS_PER_BEAT
        bmt_dt = datetime.fromtimestamp(float(utc_epoch) + BMT_OFFSET_SECONDS, tz=timezone.utc)
        return utc_dt.isoformat().replace("+00:00", "Z"), bmt_dt.date().isoformat(), round(beat, 3)

    @classmethod
    def from_epoch(cls, utc_epoch: float, *, logical_tick: int, source: str = "explicit_utc") -> TemporalStamp:
        utc_iso, bmt_date, beat = cls._civil_fields(float(utc_epoch))
        return TemporalStamp(
            logical_tick=int(logical_tick),
            source=str(source),
            utc_epoch=float(utc_epoch),
            utc_iso=utc_iso,
            bmt_date=bmt_date,
            beat=beat,
        )

    def observe(self, utc_epoch: float, *, logical_tick: int, source: str = "explicit_utc") -> TemporalStamp:
        observed = float(utc_epoch)
        regression = 0.0
        elapsed: float | None = None
        if self.last_utc_epoch is not None:
            delta = observed - self.last_utc_epoch
            if delta < 0.0:
                regression = abs(delta)
                elapsed = 0.0
            else:
                elapsed = delta
        utc_iso, bmt_date, beat = self._civil_fields(observed)
        stamp = TemporalStamp(
            logical_tick=int(logical_tick),
            source=str(source),
            utc_epoch=observed,
            utc_iso=utc_iso,
            bmt_date=bmt_date,
            beat=beat,
            elapsed_since_prior_utc=elapsed,
            clock_regression_seconds=regression,
        )
        self.last_utc_epoch = observed
        self.last_stamp = stamp
        return stamp

    def logical_only(self, *, logical_tick: int, source: str = "logical") -> TemporalStamp:
        stamp = TemporalStamp(logical_tick=int(logical_tick), source=str(source))
        self.last_stamp = stamp
        return stamp

    def to_dict(self) -> dict[str, Any]:
        return {
            "last_utc_epoch": self.last_utc_epoch,
            "last_stamp": self.last_stamp.to_dict() if self.last_stamp else None,
        }

    @classmethod
    def from_dict(cls, raw: dict[str, Any] | None) -> "TemporalAuthority":
        raw = dict(raw or {})
        authority = cls(raw.get("last_utc_epoch"))
        stamp = raw.get("last_stamp")
        if stamp:
            authority.last_stamp = TemporalStamp(**stamp)
        return authority


class TimedSubjectProxy:
    """Give DuckOrganism an explicit elapsed duration for each cognitive cycle.

    DuckOrganism historically advances its SubjectPort by one second per cycle.
    The future runtime wraps that port so an external event can advance Wayfarer
    by the actual observed elapsed duration while purely internal cognition can
    consume zero civil duration. The wrapped subject remains the identity and
    continuity authority.
    """

    def __init__(self, subject, *, default_elapsed_seconds: float = 1.0):
        self.subject = subject
        self.default_elapsed_seconds = max(0.0, float(default_elapsed_seconds))
        self._prepared_elapsed: float | None = None

    @property
    def subject_id(self) -> str:
        return self.subject.subject_id

    def snapshot(self) -> dict:
        return self.subject.snapshot()

    def observe_event(self, payload: dict) -> dict | None:
        return self.subject.observe_event(payload)

    def prepare_elapsed(self, elapsed_seconds: float) -> None:
        self._prepared_elapsed = max(0.0, float(elapsed_seconds))

    def advance_time(self, requested_elapsed_seconds: float) -> dict:
        del requested_elapsed_seconds
        elapsed = self.default_elapsed_seconds if self._prepared_elapsed is None else self._prepared_elapsed
        self._prepared_elapsed = None
        return self.subject.advance_time(float(elapsed))


def swatch_beat(utc_epoch: float) -> float:
    """Return Swatch Internet Time to three decimal places."""
    return float(TemporalAuthority.from_epoch(utc_epoch, logical_tick=0).beat)
