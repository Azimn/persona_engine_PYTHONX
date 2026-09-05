"""Deterministic limited global broadcast for DUCK."""

from __future__ import annotations

from .types import CognitiveItem, WorkspaceBroadcast


DEFAULT_WEIGHTS = {
    "salience": 0.24,
    "self_relevance": 0.20,
    "novelty": 0.10,
    "threat": 0.12,
    "confidence": 0.08,
    "drive_relevance": 0.12,
    "uncertainty": 0.07,
    "prediction_error": 0.07,
}


class GlobalWorkspace:
    def __init__(self, weights: dict[str, float] | None = None):
        self.weights = dict(DEFAULT_WEIGHTS if weights is None else weights)
        self.last_broadcast: WorkspaceBroadcast | None = None

    def score(self, item: CognitiveItem) -> tuple[float, dict[str, float]]:
        values = {
            "salience": item.salience,
            "self_relevance": item.self_relevance,
            "novelty": item.novelty,
            "threat": item.threat,
            "confidence": item.confidence,
            "drive_relevance": float(item.payload.get("drive_relevance", 0.0) or 0.0),
            "uncertainty": float(item.payload.get("uncertainty", 0.0) or 0.0),
            "prediction_error": float(item.payload.get("prediction_error", 0.0) or 0.0),
        }
        breakdown = {key: values[key] * self.weights.get(key, 0.0) for key in values}
        return sum(breakdown.values()), breakdown

    def compete(self, items: list[CognitiveItem], *, tick: int) -> WorkspaceBroadcast | None:
        if not items:
            self.last_broadcast = None
            return None
        scored = []
        for item in items:
            score, breakdown = self.score(item)
            scored.append((score, item.item_id, item, breakdown))
        scored.sort(key=lambda row: (-row[0], row[1]))
        score, _, winner, breakdown = scored[0]
        broadcast = WorkspaceBroadcast(
            tick=tick,
            winner=winner,
            priority=score,
            competing_item_ids=tuple(row[2].item_id for row in scored),
            score_breakdown=breakdown,
        )
        self.last_broadcast = broadcast
        return broadcast
