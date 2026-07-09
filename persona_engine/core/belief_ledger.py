"""Evidence-gated belief ledger.

Fast relationship deltas are handled per turn by relationship.py. This ledger
handles slower permanent belief drift from consolidated evidence. It is intended
for cartridge-defined beliefs, not arbitrary LLM-generated claims.
"""

from __future__ import annotations

from dataclasses import dataclass
import time
from typing import Any


@dataclass
class BeliefRecord:
    id: str
    value: float
    minimum: float
    maximum: float
    decay_rate: float
    description: str
    fixed: bool = False


class BeliefLedger:
    def __init__(self, belief_data: list[dict[str, Any]] | None = None):
        self.records: dict[str, BeliefRecord] = {}
        self.last_decay: float = time.time()
        self.last_consolidated: float = 0.0
        for item in belief_data or []:
            self.records[str(item["id"])] = BeliefRecord(
                id=str(item["id"]),
                value=float(item["initial"]),
                minimum=float(item["min"]),
                maximum=float(item["max"]),
                decay_rate=float(item["decay_rate"]),
                description=str(item["description"]),
                fixed=bool(item.get("fixed", False)),
            )

    @property
    def values(self) -> dict[str, float]:
        return {key: rec.value for key, rec in self.records.items()}

    def set_values(self, values: dict[str, float]) -> None:
        for key, value in values.items():
            if key in self.records and not self.records[key].fixed:
                rec = self.records[key]
                rec.value = max(rec.minimum, min(rec.maximum, float(value)))

    def get(self, belief_id: str) -> float:
        if belief_id not in self.records:
            raise KeyError(f"unknown belief id: {belief_id}")
        return self.records[belief_id].value

    def apply_decay(self, elapsed_seconds: float) -> None:
        if elapsed_seconds <= 0:
            return
        for rec in self.records.values():
            if rec.fixed or rec.decay_rate <= 0:
                continue
            if rec.value > 0:
                rec.value = max(rec.minimum, rec.value - rec.decay_rate * elapsed_seconds)
            elif rec.value < 0:
                rec.value = min(rec.maximum, rec.value + rec.decay_rate * elapsed_seconds)
        self.last_decay += elapsed_seconds

    def evaluate_rules(self, belief_rules: list[dict[str, Any]], memory_counts: dict[str, int]) -> list[str]:
        changed: list[str] = []
        for rule in belief_rules:
            trigger = str(rule["trigger_memory_type"])
            if int(memory_counts.get(trigger, 0)) < int(rule["threshold_count"]):
                continue
            belief_id = str(rule["belief_id"])
            rec = self.records.get(belief_id)
            if rec is None or rec.fixed:
                continue
            before = rec.value
            rec.value = max(rec.minimum, min(rec.maximum, rec.value + float(rule["delta"])))
            if rec.value != before and belief_id not in changed:
                changed.append(belief_id)
        return changed

    def to_state(self) -> dict[str, Any]:
        return {
            "records": {k: rec.__dict__ for k, rec in self.records.items()},
            "last_decay": self.last_decay,
            "last_consolidated": self.last_consolidated,
        }

    @classmethod
    def from_state(cls, state: dict[str, Any], fallback_beliefs: list[dict[str, Any]] | None = None) -> "BeliefLedger":
        led = cls(fallback_beliefs or [])
        if not state:
            return led
        led.last_decay = float(state.get("last_decay", led.last_decay))
        led.last_consolidated = float(state.get("last_consolidated", 0.0))
        records = state.get("records", {})
        for key, item in records.items():
            led.records[key] = BeliefRecord(
                id=item["id"], value=float(item["value"]), minimum=float(item["minimum"]), maximum=float(item["maximum"]),
                decay_rate=float(item["decay_rate"]), description=item.get("description", ""), fixed=bool(item.get("fixed", False)),
            )
        return led
