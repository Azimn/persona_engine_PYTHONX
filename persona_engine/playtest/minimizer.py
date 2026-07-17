"""Bounded deterministic delta minimization for generated failures."""

from __future__ import annotations

import hashlib
import time
from pathlib import Path
from typing import Callable

import yaml


class ScenarioMinimizer:
    def __init__(self, max_runs: int = 40, timeout_seconds: float = 120.0):
        self.max_runs = max_runs
        self.timeout_seconds = timeout_seconds

    def minimize(self, *, scenario, failure_code: str, run_callable: Callable) -> tuple[object, int]:
        candidate, runs, started = scenario, 0, time.monotonic()
        while candidate.total_days > 1 and runs < self.max_runs and time.monotonic() - started < self.timeout_seconds:
            proposed = candidate.__class__(**{**candidate.__dict__, "total_days": max(1, candidate.total_days // 2),
                                               "scheduled_events": tuple(e for e in candidate.scheduled_events if e.day <= max(1, candidate.total_days // 2))})
            runs += 1
            result = run_callable(proposed)
            if any(item.code == failure_code for item in result.failures):
                candidate = proposed
            else:
                break
        return candidate, runs

    @staticmethod
    def export(scenario, failure_code: str, root: str | Path) -> Path:
        digest = hashlib.blake2b(repr(scenario).encode(), digest_size=6).hexdigest()
        path = Path(root) / f"{failure_code}_{digest}.yaml"
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = {**scenario.__dict__, "scheduled_events": [event.__dict__ for event in scenario.scheduled_events]}
        path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")
        return path
