"""Slow consolidation loop for belief drift.

DreamEngine reads only new evidence since the belief ledger's last consolidation
and applies cartridge-defined threshold rules. This prevents old events from
being counted repeatedly.
"""

from __future__ import annotations

import time
from .belief_ledger import BeliefLedger
from .persistence import Persistence


class DreamEngine:
    def __init__(self, persistence: Persistence, belief_ledger: BeliefLedger):
        self.persistence = persistence
        self.belief_ledger = belief_ledger

    def consolidate(self, character_id: str, user_id: str, belief_rules: list[dict]) -> list[str]:
        since = float(self.belief_ledger.last_consolidated or 0.0)
        counts = self.persistence.event_counts_since(character_id, user_id, since)
        changed = self.belief_ledger.evaluate_rules(belief_rules, counts)
        watermark = time.time()
        self.belief_ledger.last_consolidated = watermark
        # Persist the new watermark before pruning its source evidence. A crash
        # after save but before prune is harmless because those rows fall behind
        # the persisted watermark; pruning before save could lose evidence.
        self.persistence.save(character_id, user_id, "belief_ledger", self.belief_ledger.to_state())
        self.persistence.prune_consolidation_evidence(character_id, user_id, watermark)
        return changed

    def run_idle_pass(self, character_id: str, user_id: str, belief_rules: list[dict], min_interval_seconds: int = 3600) -> list[str]:
        now = time.time()
        if self.belief_ledger.last_consolidated and now - self.belief_ledger.last_consolidated < min_interval_seconds:
            return []
        return self.consolidate(character_id, user_id, belief_rules)
