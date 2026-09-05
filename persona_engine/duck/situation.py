"""Bounded current-situation construction from source events."""

from __future__ import annotations

from .types import CognitiveItem, ExternalEvent, SituationModel, clamp


class SituationConstructor:
    def update(self, situation: SituationModel, event: ExternalEvent, *, tick: int, subject_id: str) -> tuple[dict, CognitiveItem]:
        changes: dict = {"last_event_id": event.event_id}
        situation.last_event_id = event.event_id
        payload = event.payload
        if event.kind in {"world_fact", "observation"}:
            key = payload.get("fact_key")
            if key:
                old = situation.facts.get(str(key))
                situation.facts[str(key)] = payload.get("fact_value")
                changes.setdefault("facts", {})[str(key)] = {"old": old, "new": payload.get("fact_value")}
        entity_id = payload.get("entity_id")
        if entity_id:
            old = dict(situation.entities.get(str(entity_id), {}))
            situation.entities[str(entity_id)] = dict(payload.get("entity", {}))
            changes.setdefault("entities", {})[str(entity_id)] = {"old": old, "new": situation.entities[str(entity_id)]}
        unresolved = payload.get("unresolved_question")
        if unresolved and unresolved not in situation.unresolved:
            situation.unresolved.append(str(unresolved))
            situation.unresolved[:] = situation.unresolved[-16:]
            changes.setdefault("unresolved_added", []).append(str(unresolved))

        target = str(payload.get("target_subject_id", ""))
        actor = str(payload.get("actor_subject_id", ""))
        self_relevance = float(payload.get("self_relevance", 0.0) or 0.0)
        if target and target == subject_id:
            self_relevance = max(self_relevance, 0.9)
        if actor and actor == subject_id:
            self_relevance = max(self_relevance, 0.8)
        item = CognitiveItem(
            item_id=f"event:{tick}:{event.event_id}",
            tick=tick,
            kind=event.kind,
            source_module="situation",
            subject_id=subject_id,
            payload=dict(payload),
            confidence=clamp(event.confidence),
            salience=clamp(payload.get("salience", 0.45)),
            self_relevance=clamp(self_relevance),
            novelty=clamp(payload.get("novelty", 0.40)),
            threat=clamp(payload.get("threat", 0.0)),
            valence=max(-1.0, min(1.0, float(payload.get("valence", 0.0) or 0.0))),
            arousal=clamp(payload.get("arousal", 0.0)),
            provenance={"event_id": event.event_id, "source": event.source, "authority": "source_evidence"},
            canonical=False,
        )
        return changes, item
