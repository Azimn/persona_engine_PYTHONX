"""Slow evidence-gated consolidation for durable belief development.

A consolidation boundary is path-dependent: even a pass that changes no belief
can consume a rule-relevant evidence window and therefore alter later
development. InteriorEngine may commit such a boundary into canonical continuity.
Direct DreamEngine callers retain the legacy list[str] API.
"""

from __future__ import annotations

from dataclasses import dataclass
import time

from .belief_ledger import BeliefLedger
from .persistence import Persistence


@dataclass(frozen=True)
class ConsolidationPass:
    since: float
    watermark: float
    evidence_counts: dict[str, int]
    changed_beliefs: tuple[str, ...]
    before_values: dict[str, float]
    after_values: dict[str, float]


class DreamEngine:
    def __init__(self, persistence: Persistence, belief_ledger: BeliefLedger):
        self.persistence = persistence
        self.belief_ledger = belief_ledger

    def prepare_consolidation(self, character_id: str, user_id: str, belief_rules: list[dict]) -> ConsolidationPass:
        """Evaluate one pass in memory without choosing its persistence authority."""

        since = float(self.belief_ledger.last_consolidated or 0.0)
        counts = self.persistence.event_counts_since(character_id, user_id, since)
        before = dict(self.belief_ledger.values)
        changed = tuple(self.belief_ledger.evaluate_rules(belief_rules, counts))
        watermark = time.time()
        self.belief_ledger.last_consolidated = watermark
        after = dict(self.belief_ledger.values)
        return ConsolidationPass(
            since=since,
            watermark=watermark,
            evidence_counts=dict(counts),
            changed_beliefs=changed,
            before_values=before,
            after_values=after,
        )

    def persist_prepared(self, character_id: str, user_id: str, result: ConsolidationPass) -> None:
        """Persist a prepared pass through the legacy non-canonical path."""

        self.persistence.save(character_id, user_id, "belief_ledger", self.belief_ledger.to_state())
        self.persistence.prune_consolidation_evidence(character_id, user_id, result.watermark)

    def consolidate(self, character_id: str, user_id: str, belief_rules: list[dict]) -> list[str]:
        result = self.prepare_consolidation(character_id, user_id, belief_rules)
        self.persist_prepared(character_id, user_id, result)
        return list(result.changed_beliefs)

    def prepare_idle_pass(
        self,
        character_id: str,
        user_id: str,
        belief_rules: list[dict],
        min_interval_seconds: int = 3600,
    ) -> ConsolidationPass | None:
        now = time.time()
        if self.belief_ledger.last_consolidated and now - self.belief_ledger.last_consolidated < min_interval_seconds:
            return None
        return self.prepare_consolidation(character_id, user_id, belief_rules)

    def run_idle_pass(self, character_id: str, user_id: str, belief_rules: list[dict], min_interval_seconds: int = 3600) -> list[str]:
        result = self.prepare_idle_pass(character_id, user_id, belief_rules, min_interval_seconds)
        if result is None:
            return []
        self.persist_prepared(character_id, user_id, result)
        return list(result.changed_beliefs)
