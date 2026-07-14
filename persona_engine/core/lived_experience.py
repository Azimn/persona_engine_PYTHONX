"""Objective events, subjective experience traces, and bounded memory lifecycle."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
import hashlib
from typing import Any

from .memory import KnowledgeSource, MemoryStore, MemoryUnit


def _bounded(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


def _stable_id(prefix: str, *parts: object) -> str:
    payload = "|".join(str(part) for part in parts).encode("utf-8")
    return f"{prefix}_{hashlib.blake2b(payload, digest_size=8).hexdigest()}"


@dataclass(frozen=True)
class WorldEvent:
    event_id: str
    tick: int
    timestamp: float
    event_type: str
    actors: tuple[str, ...]
    location: str
    action: str
    targets: tuple[str, ...]
    outcome: str
    source: str
    canonicality: str = "objective"
    payload: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "WorldEvent":
        raw = dict(data)
        raw["actors"] = tuple(raw.get("actors", ()))
        raw["targets"] = tuple(raw.get("targets", ()))
        return cls(**raw)


class WorldEventLedger:
    def __init__(self, events: list[WorldEvent] | None = None):
        self._events = list(events or [])
        self._ids = {event.event_id for event in self._events}

    def append(self, event: WorldEvent) -> WorldEvent:
        if event.canonicality != "objective":
            raise ValueError("world event canonicality must be objective")
        if event.event_id in self._ids:
            return self.fetch(event.event_id)
        self._events.append(event)
        self._ids.add(event.event_id)
        return event

    def create(self, *, tick: int, timestamp: float, event_type: str, actors=(), location="unknown",
               action="observed", targets=(), outcome="", source="host", payload=None) -> WorldEvent:
        sequence = len(self._events)
        event = WorldEvent(
            event_id=_stable_id("world", tick, event_type, sequence),
            tick=int(tick), timestamp=float(timestamp), event_type=str(event_type),
            actors=tuple(str(item) for item in actors), location=str(location), action=str(action),
            targets=tuple(str(item) for item in targets), outcome=str(outcome), source=str(source),
            payload=dict(payload or {}),
        )
        return self.append(event)

    def fetch(self, event_id: str) -> WorldEvent | None:
        return next((event for event in self._events if event.event_id == event_id), None)

    def by_time(self, start: float, end: float) -> list[WorldEvent]:
        return [event for event in self._events if start <= event.timestamp <= end]

    def recent(self, limit: int = 20) -> list[WorldEvent]:
        return sorted(self._events, key=lambda event: (event.tick, event.timestamp, event.event_id), reverse=True)[:max(0, limit)]

    def to_list(self) -> list[dict[str, Any]]:
        return [event.to_dict() for event in self._events]

    @classmethod
    def from_list(cls, data: list[dict[str, Any]] | None) -> "WorldEventLedger":
        return cls([WorldEvent.from_dict(item) for item in (data or [])])


@dataclass
class SubjectiveExperience:
    experience_id: str
    character_id: str
    world_event_id: str
    perceived_summary: str
    interpretation: str
    emotional_residue: str
    attention_weight: float
    confidence: float
    salience: float
    encoding_strength: float
    source_tier: int
    provenance: dict[str, Any]
    created_at: float
    last_recalled_at: float | None = None
    recall_count: int = 0
    distortion: dict[str, Any] = field(default_factory=dict)
    lifecycle: str = "trace"
    memory_id: str | None = None
    decay_stage: int = 0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SubjectiveExperience":
        return cls(**data)


class ExperienceStore:
    def __init__(self, experiences: list[SubjectiveExperience] | None = None):
        self.experiences = list(experiences or [])

    def perceive(self, event: WorldEvent, character_id: str, *, attention: float, confidence: float = 0.8,
                 salience: float = 0.5, emotional_residue: str = "neutral", interpretation: str = "ordinary",
                 source_tier: int = 0, distortion: dict[str, Any] | None = None) -> SubjectiveExperience | None:
        attention = _bounded(attention)
        if attention < 0.15:
            return None
        summary = event.outcome or " ".join(part for part in (event.action, *event.targets) if part).strip()
        if not summary:
            summary = event.event_type
        experience = SubjectiveExperience(
            experience_id=_stable_id("experience", character_id, event.event_id, len(self.experiences)),
            character_id=str(character_id), world_event_id=event.event_id,
            perceived_summary=f"I noticed {summary}.", interpretation=str(interpretation),
            emotional_residue=str(emotional_residue), attention_weight=attention,
            confidence=_bounded(confidence), salience=_bounded(salience),
            encoding_strength=_bounded((attention + salience) / 2.0), source_tier=max(0, int(source_tier)),
            provenance={"world_event_id": event.event_id, "source": event.source},
            created_at=event.timestamp, distortion=dict(distortion or {}),
        )
        self.experiences.append(experience)
        return experience

    def consolidate(self, experience: SubjectiveExperience, memory: MemoryStore, now: float, force: bool = False) -> MemoryUnit | None:
        score = experience.salience * 0.45 + experience.encoding_strength * 0.35 + min(0.2, experience.recall_count * 0.05)
        if not force and score < 0.42:
            return None
        if experience.memory_id:
            return next((item for item in memory.memories if item.id == experience.memory_id), None)
        unit = MemoryUnit(
            content=experience.perceived_summary,
            created_at=now,
            id=_stable_id("memory", experience.experience_id),
            emotional_intensity=experience.salience,
            source=KnowledgeSource.OBSERVED,
            tags={"autobiographical", "subjective_experience", f"world_event:{experience.world_event_id}"},
            confidence=experience.confidence,
            salience=experience.salience,
            provenance=dict(experience.provenance),
            source_tier=experience.source_tier,
        )
        memory.add(unit)
        experience.memory_id = unit.id
        experience.lifecycle = "memory"
        return unit

    def decay(self, now: float, detail_after: float = 86400.0, prune_after: float = 86400.0 * 30) -> int:
        kept: list[SubjectiveExperience] = []
        pruned = 0
        for experience in self.experiences:
            age = max(0.0, now - experience.created_at)
            target_stage = 2 if age >= detail_after * 7 else 1 if age >= detail_after else 0
            while experience.decay_stage < target_stage:
                experience.confidence = _bounded(experience.confidence - 0.2)
                experience.encoding_strength = _bounded(experience.encoding_strength - 0.1)
                experience.decay_stage += 1
            if target_stage >= 1 and experience.lifecycle != "decayed":
                experience.perceived_summary = f"I remember feeling {experience.emotional_residue}, but the factual detail has faded."
                experience.lifecycle = "decayed"
            if age >= prune_after and experience.salience < 0.2 and experience.recall_count == 0 and not experience.memory_id:
                pruned += 1
            else:
                kept.append(experience)
        self.experiences = kept
        return pruned

    def recall(self, experience_id: str, now: float) -> SubjectiveExperience | None:
        experience = next((item for item in self.experiences if item.experience_id == experience_id), None)
        if experience:
            experience.last_recalled_at = now
            experience.recall_count += 1
            experience.encoding_strength = _bounded(experience.encoding_strength + 0.05)
        return experience

    def recent(self, limit: int = 20) -> list[SubjectiveExperience]:
        return sorted(self.experiences, key=lambda item: (item.created_at, item.experience_id), reverse=True)[:max(0, limit)]

    def to_list(self) -> list[dict[str, Any]]:
        return [item.to_dict() for item in self.experiences]

    @classmethod
    def from_list(cls, data: list[dict[str, Any]] | None) -> "ExperienceStore":
        return cls([SubjectiveExperience.from_dict(item) for item in (data or [])])
