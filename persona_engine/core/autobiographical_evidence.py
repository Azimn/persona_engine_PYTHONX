"""Explicit evidence routing into autobiographical reconsideration."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
import math
from typing import Any, Mapping, Sequence


EVIDENCE_RELATIONS = frozenset({
    "supports", "contradicts", "clarifies", "corrects_cause", "resolves_uncertainty",
    "changes_relationship_meaning", "changes_identity_meaning",
})
EVIDENCE_TIERS = frozenset({"objective", "supported_subjective", "inferred", "uncertain"})
INTERPRETATION_STATUSES = frozenset({"current", "challenged", "unresolved", "superseded"})


def _bounded(value: float) -> float:
    value = float(value)
    if not math.isfinite(value):
        raise ValueError("value must be finite")
    return max(0.0, min(1.0, value))


def _stable(prefix: str, *parts: object) -> str:
    raw = json.dumps([str(item) for item in parts], separators=(",", ":")).encode()
    return prefix + "_" + hashlib.blake2b(raw, digest_size=8).hexdigest()


@dataclass(frozen=True)
class AutobiographicalEvidenceLink:
    schema_version: int
    link_id: str
    evidence_event_id: str
    experience_id: str
    interpretation_id: str
    relation: str
    strength: float
    evidence_tier: str
    source_field: str
    created_tick: int
    provenance_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        if self.relation not in EVIDENCE_RELATIONS or self.evidence_tier not in EVIDENCE_TIERS:
            raise ValueError("unsupported autobiographical evidence classification")
        _bounded(self.strength)

    def to_dict(self) -> dict[str, Any]:
        return {**asdict(self), "record_authority": "canonical_cognitive_record"}

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]):
        raw = {key: data[key] for key in cls.__dataclass_fields__ if key in data}
        raw["provenance_ids"] = tuple(raw.get("provenance_ids", ()))
        return cls(**raw)


@dataclass(frozen=True)
class InterpretationStatusEvent:
    schema_version: int
    status_event_id: str
    interpretation_id: str
    new_status: str
    cause_id: str
    created_tick: int
    provenance_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        if self.new_status not in INTERPRETATION_STATUSES:
            raise ValueError("unsupported interpretation status")

    def to_dict(self):
        return asdict(self)

    @classmethod
    def from_dict(cls, data):
        raw = dict(data); raw["provenance_ids"] = tuple(raw.get("provenance_ids", ()))
        return cls(**raw)


class AutobiographicalEvidenceRouter:
    DIRECT_FIELDS = {
        "corrects_world_event_id": "corrects_cause", "supports_world_event_id": "supports",
        "contradicts_interpretation_id": "contradicts", "supports_interpretation_id": "supports",
        "resolves_uncertainty_id": "resolves_uncertainty",
        "changes_relationship_interpretation_id": "changes_relationship_meaning",
        "changes_identity_interpretation_id": "changes_identity_meaning",
    }
    MAX_LINKS_PER_EVENT = 4

    def route(self, *, event, interpretations, experiences, tick: int) -> tuple[AutobiographicalEvidenceLink, ...]:
        links = []
        for field, relation in self.DIRECT_FIELDS.items():
            value = (event.payload or {}).get(field)
            if not value:
                continue
            for experience, interpretation in self._resolve_targets(str(field), str(value), interpretations, experiences):
                link = AutobiographicalEvidenceLink(
                    1, _stable("autobio_evidence", event.event_id, interpretation.interpretation_id, relation, field),
                    event.event_id, experience.experience_id, interpretation.interpretation_id, relation,
                    .95 if relation in {"corrects_cause", "contradicts"} else .75,
                    "objective" if event.canonicality == "objective" else "supported_subjective",
                    field, int(tick), (event.event_id, experience.experience_id, interpretation.interpretation_id),
                )
                links.append(link)
        return tuple(sorted(links, key=lambda item: item.link_id)[:self.MAX_LINKS_PER_EVENT])

    @staticmethod
    def _resolve_targets(field: str, value: str, interpretations, experiences):
        result = []
        if field.endswith("world_event_id"):
            for experience in experiences.experiences:
                if experience.world_event_id == value:
                    current = interpretations.current(experience.experience_id)
                    if current:
                        result.append((experience, current))
        else:
            interpretation = interpretations.fetch(value)
            if interpretation:
                experience = next((item for item in experiences.experiences if item.experience_id == interpretation.experience_id), None)
                if experience:
                    result.append((experience, interpretation))
        return result


class InterpretationStatusStore:
    MAX_EVENTS = 2048

    def __init__(self, events: Sequence[InterpretationStatusEvent] = ()):
        self.events = list(events)[-self.MAX_EVENTS:]

    def add(self, interpretation_id: str, status: str, cause_id: str, tick: int):
        event = InterpretationStatusEvent(1, _stable("interpretation_status", interpretation_id, status, cause_id, tick),
                                          interpretation_id, status, cause_id, tick, (interpretation_id, cause_id))
        if not any(item.status_event_id == event.status_event_id for item in self.events):
            self.events = [*self.events, event][-self.MAX_EVENTS:]
        return event

    def effective_status(self, interpretation_id: str, default: str = "current") -> str:
        matches = [item for item in self.events if item.interpretation_id == interpretation_id]
        return matches[-1].new_status if matches else default

    def to_list(self): return [item.to_dict() for item in self.events]
    @classmethod
    def from_list(cls, data): return cls([InterpretationStatusEvent.from_dict(item) for item in (data or ())])
