"""Deterministic subject-relative attribution bridge for DUCK.

This is a functional fallback around the current Wayfarer subject. A future
Virtual Self adapter may replace the scoring implementation without changing the
organism contract.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass

from .types import CognitiveItem, ExternalEvent, clamp


@dataclass(frozen=True)
class AttributionFrame:
    frame_id: str
    source: str
    mineness: float
    agency: float
    self_relevance: float
    autobiographical_belonging: float
    affective_ownership: float
    binding_confidence: float

    def to_dict(self) -> dict:
        return asdict(self)


class AttributionBridge:
    def attribute(self, event: ExternalEvent, *, subject_id: str, tick: int) -> AttributionFrame:
        payload = event.payload
        actor = str(payload.get("actor_subject_id", ""))
        target = str(payload.get("target_subject_id", ""))
        self_actor = bool(actor and actor == subject_id)
        self_target = bool(target and target == subject_id)
        explicitly_owned = bool(payload.get("owned_by_subject", False))
        internal = event.kind.startswith("internal_") or str(payload.get("modality", "")) == "internal"

        agency = clamp(payload.get("agency", 0.92 if self_actor else 0.08))
        mineness = clamp(payload.get("mineness", 0.92 if (self_target or explicitly_owned or internal) else 0.12))
        self_relevance = clamp(payload.get("self_relevance", max(agency, mineness) if (self_actor or self_target or internal) else 0.20))
        autobiographical = clamp(payload.get("autobiographical_belonging", max(mineness, self_relevance * 0.8)))
        affective_ownership = clamp(payload.get("affective_ownership", max(mineness * 0.8, self_relevance * 0.6)))
        confidence = clamp(payload.get("binding_confidence", event.confidence))
        return AttributionFrame(
            frame_id=f"attribution:{tick}:{event.event_id}",
            source=event.source,
            mineness=mineness,
            agency=agency,
            self_relevance=self_relevance,
            autobiographical_belonging=autobiographical,
            affective_ownership=affective_ownership,
            binding_confidence=confidence,
        )

    def as_cognitive_item(self, frame: AttributionFrame, *, tick: int, subject_id: str) -> CognitiveItem:
        return CognitiveItem(
            item_id=frame.frame_id,
            tick=tick,
            kind="subject_attribution",
            source_module="subject_attribution",
            subject_id=subject_id,
            payload={"attribution": frame.to_dict()},
            confidence=frame.binding_confidence,
            salience=clamp(0.20 + 0.45 * frame.self_relevance + 0.15 * frame.affective_ownership),
            self_relevance=frame.self_relevance,
            novelty=0.05,
            threat=0.0,
            arousal=frame.affective_ownership * 0.4,
            provenance={"authority": "subject_attribution", "frame_id": frame.frame_id},
            canonical=False,
        )
