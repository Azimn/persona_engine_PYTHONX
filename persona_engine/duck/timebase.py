"""Explicit temporal observations for the DUCK organism.

DUCK keeps causal order, subject elapsed time, and civil time separate.
Logical ticks remain the deterministic causal clock. Wayfarer's ContinuityClock
owns monotonic elapsed subject time. This module represents optional observed
civil time and derives Swatch Internet Time without ever consulting the host
clock implicitly.
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
    clock_regression_seconds: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class TemporalAuthority:
    """Derive subject-facing civil-time metadata from explicit observations."""

    def __init__(self, last_utc_epoch: float | None = None):
        self.last_utc_epoch = None if last_utc_epoch is None else float(last_utc_epoch)
        self.last_stamp: TemporalStamp | None = None

    @staticmethod
    def from_epoch(utc_epoch: float, *, logical_tick: int, source: str = "explicit_utc") -> TemporalStamp:
        epoch = float(utc_epoch)
        utc_dt = datetime.fromtimestamp(epoch, tz=timezone.utc)
        seconds = (
            utc_dt.hour * 3600.0
            + utc_dt.minute * 60.0
            + utc_dt.second
            + utc_dt.microsecond / 1_000_000.0
        )
        beat = ((seconds + BMT_OFFSET_SECONDS) % SECONDS_PER_DAY) / SECONDS_PER_BEAT
        bmt_dt = datetime.fromtimestamp(epoch + BMT_OFFSET_SECONDS, tz=timezone.utc)
        return TemporalStamp(
            logical_tick=int(logical_tick),
            source=str(source),
            utc_epoch=epoch,
            utc_iso=utc_dt.isoformat().replace("+00:00", "Z"),
            bmt_date=bmt_dt.date().isoformat(),
            beat=round(beat, 3),
        )

    def observe(self, utc_epoch: float, *, logical_tick: int, source: str = "explicit_utc") -> TemporalStamp:
        observed = float(utc_epoch)
        regression = 0.0
        if self.last_utc_epoch is not None and observed < self.last_utc_epoch:
            regression = self.last_utc_epoch - observed
        stamp = self.from_epoch(observed, logical_tick=logical_tick, source=source)
        if regression:
            stamp = TemporalStamp(**{**stamp.to_dict(), "clock_regression_seconds": regression})
        self.last_utc_epoch = observed
        self.last_stamp = stamp
        return stamp

    def logical_only(self, *, logical_tick: int, source: str = "logical") -> TemporalStamp:
        stamp = TemporalStamp(logical_tick=int(logical_tick), source=str(source))
        self.last_stamp = stamp
        return stamp

    def stamp_payload(
        self,
        payload: dict[str, Any],
        *,
        logical_tick: int,
        source: str,
    ) -> dict[str, Any]:
        """Return a copied payload with an explicit temporal stamp.

        Civil time is recognized only when the caller supplied ``utc_epoch`` or
        ``civil_time_utc_epoch``. Event ``timestamp`` values are intentionally not
        guessed to be Unix time because deterministic simulations often use small
        logical values there.
        """
        result = dict(payload)
        raw = result.get("utc_epoch", result.get("civil_time_utc_epoch"))
        stamp = (
            self.observe(float(raw), logical_tick=logical_tick, source=source)
            if raw is not None
            else self.logical_only(logical_tick=logical_tick, source=source)
        )
        result["temporal_stamp"] = stamp.to_dict()
        return result


def swatch_beat(utc_epoch: float) -> float:
    """Return Swatch Internet Time to three decimal places."""
    return float(TemporalAuthority.from_epoch(utc_epoch, logical_tick=0).beat)
