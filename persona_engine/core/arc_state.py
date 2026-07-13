"""Simplified arc-state modifiers with idempotent earned changes."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ArcState:
    arc_id: str
    old_strategy: str
    emerging_strategy: str
    tensions: dict[str, float]
    threshold_events: dict[str, int]
    applied_changes: set[str] = field(default_factory=set)
    unresolved: bool = True

    def record_threshold_event(self, name: str):
        self.threshold_events[name] = self.threshold_events.get(name, 0) + 1

    def check_earned_changes(self, cartridge) -> dict[str, float]:
        """Return newly applied deltas only."""

        arc_rules = {}
        if isinstance(cartridge, dict):
            arc_rules = cartridge.get("arc", {}).get("earned_changes", {})
        changes: dict[str, float] = {}
        for change_id, rule in arc_rules.items():
            if change_id in self.applied_changes or not isinstance(rule, dict):
                continue
            event_name = str(rule.get("threshold_event", ""))
            required_count = int(rule.get("count", 1))
            if self.threshold_events.get(event_name, 0) < required_count:
                continue
            modifier = str(rule.get("modifier", ""))
            delta = float(rule.get("delta", 0.0))
            if modifier:
                changes[modifier] = delta
                self.applied_changes.add(str(change_id))
        return changes
