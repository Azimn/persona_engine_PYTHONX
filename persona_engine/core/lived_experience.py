"""Objective events, subjective experience traces, and bounded memory lifecycle."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
import hashlib
import math
from typing import Any, Iterable, Mapping, Sequence

from .memory import KnowledgeSource, MemoryStore, MemoryUnit


def _bounded(value: float) -> float:
    value = float(value)
    if not math.isfinite(value):
        raise ValueError("value must be finite")
    return max(0.0, min(1.0, value))


def _signed_bounded(value: float) -> float:
    value = float(value)
    if not math.isfinite(value):
        raise ValueError("value must be finite")
    return max(-1.0, min(1.0, value))


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

    def recall_surface(self) -> str:
        if self.decay_stage >= 2:
            return f"I remember feeling {self.emotional_residue}, but little factual detail remains."
        if self.decay_stage >= 1:
            return f"I remember the event indistinctly: {self.perceived_summary}"
        return self.perceived_summary

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SubjectiveExperience":
        raw = dict(data)
        summary = str(raw.get("perceived_summary", ""))
        if summary.lower().startswith("i remember feeling") and raw.get("provenance", {}).get("world_event_id"):
            distortion = dict(raw.get("distortion") or {})
            distortion["legacy_destructive_decay"] = True
            raw["distortion"] = distortion
        return cls(**raw)


AUTOBIOGRAPHICAL_TRIGGER_TYPES = frozenset({
    "initial_encoding", "contradictory_evidence", "relationship_phase_change",
    "belief_correction", "resolved_open_loop", "high_salience_recall",
    "dream_consolidation", "failure_reinterpretation", "explicit_reconsideration",
})
AUTOBIOGRAPHICAL_STATUSES = frozenset({"current", "superseded", "challenged", "unresolved"})
MEANING_KINDS = frozenset({
    "ordinary", "mistaken_attribution", "relationship_meaning", "identity_meaning",
    "procedural_lesson", "reconciled_meaning", "resentful_meaning", "uncertain_meaning",
})


@dataclass(frozen=True)
class AutobiographicalInterpretation:
    schema_version: int
    interpretation_id: str
    experience_id: str
    world_event_id: str
    memory_id: str | None
    version: int
    first_person_summary: str
    current_meaning: str
    meaning_kind: str
    confidence: float
    emotional_residue: str
    emotional_charge: float
    relationship_relevance: float
    identity_relevance: float
    supporting_memory_ids: tuple[str, ...]
    contradicting_memory_ids: tuple[str, ...]
    supporting_world_event_ids: tuple[str, ...]
    contradicting_world_event_ids: tuple[str, ...]
    supersedes: str | None
    trigger_type: str
    created_tick: int
    status: str = "current"

    def __post_init__(self) -> None:
        if self.trigger_type not in AUTOBIOGRAPHICAL_TRIGGER_TYPES:
            raise ValueError(f"unsupported autobiographical trigger: {self.trigger_type}")
        if self.status not in AUTOBIOGRAPHICAL_STATUSES:
            raise ValueError(f"unsupported autobiographical status: {self.status}")
        if self.meaning_kind not in MEANING_KINDS:
            raise ValueError(f"unsupported meaning kind: {self.meaning_kind}")
        if self.version < 1:
            raise ValueError("interpretation version must be positive")
        for value in (self.confidence, self.relationship_relevance, self.identity_relevance):
            _bounded(value)
        _signed_bounded(self.emotional_charge)
        if not self.first_person_summary.strip() or not self.current_meaning.strip():
            raise ValueError("autobiographical summary and meaning must not be empty")

    def to_dict(self) -> dict[str, Any]:
        return {**asdict(self), "record_authority": "canonical_cognitive_record"}

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "AutobiographicalInterpretation":
        raw = {key: data[key] for key in cls.__dataclass_fields__ if key in data}
        for key in ("supporting_memory_ids", "contradicting_memory_ids", "supporting_world_event_ids", "contradicting_world_event_ids"):
            raw[key] = tuple(raw.get(key, ()))
        raw.setdefault("memory_id", None)
        raw.setdefault("supersedes", None)
        raw.setdefault("status", "current")
        return cls(**raw)


@dataclass(frozen=True)
class ReinterpretationCandidate:
    schema_version: int
    candidate_id: str
    experience_id: str
    prior_interpretation_id: str
    trigger_type: str
    proposed_meaning_kind: str
    proposed_meaning: str
    confidence: float
    supporting_memory_ids: tuple[str, ...]
    contradicting_memory_ids: tuple[str, ...]
    supporting_world_event_ids: tuple[str, ...]
    contradicting_world_event_ids: tuple[str, ...]
    conflict_strength: float
    emotional_charge_delta: float
    eligible_after_tick: int
    provenance_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        if self.trigger_type not in AUTOBIOGRAPHICAL_TRIGGER_TYPES - {"initial_encoding"}:
            raise ValueError(f"unsupported reinterpretation trigger: {self.trigger_type}")
        if self.proposed_meaning_kind not in MEANING_KINDS:
            raise ValueError(f"unsupported meaning kind: {self.proposed_meaning_kind}")
        _bounded(self.confidence)
        _bounded(self.conflict_strength)
        _signed_bounded(self.emotional_charge_delta)
        if not self.proposed_meaning.strip():
            raise ValueError("proposed meaning must not be empty")

    def to_dict(self) -> dict[str, Any]:
        return {**asdict(self), "record_authority": "canonical_cognitive_record"}

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "ReinterpretationCandidate":
        raw = {key: data[key] for key in cls.__dataclass_fields__ if key in data}
        for key in ("supporting_memory_ids", "contradicting_memory_ids", "supporting_world_event_ids", "contradicting_world_event_ids", "provenance_ids"):
            raw[key] = tuple(raw.get(key, ()))
        return cls(**raw)


@dataclass(frozen=True)
class DeferredReinterpretation:
    schema_version: int
    deferred_id: str
    experience_id: str
    prior_interpretation_id: str
    trigger_type: str
    evidence_ids: tuple[str, ...]
    conflict_strength: float
    deferred_reason: str
    created_tick: int
    eligible_after_tick: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "DeferredReinterpretation":
        raw = dict(data)
        raw["evidence_ids"] = tuple(raw.get("evidence_ids", ()))
        return cls(**raw)


@dataclass(frozen=True)
class AutobiographicalActivation:
    interpretation_id: str
    experience_id: str
    memory_id: str | None
    activation: float
    status: str
    reasons: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class InterpretationUseOutcome:
    schema_version: int
    use_outcome_id: str
    interpretation_id: str
    synthesis_id: str
    decision_id: str
    action_completion_id: str | None
    contribution: str
    usefulness: float
    interference: float
    evidence_tier: str
    created_tick: int
    provenance_ids: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "InterpretationUseOutcome":
        raw = dict(data)
        raw["provenance_ids"] = tuple(raw.get("provenance_ids", ()))
        return cls(**raw)


class AutobiographicalInterpretationStore:
    MAX_INTERPRETATIONS = 1024
    MAX_VERSIONS_PER_EXPERIENCE = 8

    def __init__(self, interpretations: Iterable[AutobiographicalInterpretation] | None = None):
        self.interpretations = list(interpretations or ())
        self._validate_history()

    def for_experience(self, experience_id: str) -> tuple[AutobiographicalInterpretation, ...]:
        return tuple(sorted(
            (item for item in self.interpretations if item.experience_id == experience_id),
            key=lambda item: (item.version, item.created_tick, item.interpretation_id),
        ))

    def fetch(self, interpretation_id: str) -> AutobiographicalInterpretation | None:
        return next((item for item in self.interpretations if item.interpretation_id == interpretation_id), None)

    def current(self, experience_id: str) -> AutobiographicalInterpretation | None:
        versions = self.for_experience(experience_id)
        if not versions:
            return None
        superseded = {item.supersedes for item in versions if item.supersedes}
        active = [item for item in versions if item.interpretation_id not in superseded and item.status in {"current", "unresolved"}]
        return active[-1] if active else versions[-1]

    def append(self, interpretation: AutobiographicalInterpretation) -> AutobiographicalInterpretation:
        existing = next((item for item in self.interpretations if item.interpretation_id == interpretation.interpretation_id), None)
        if existing:
            return existing
        if len(self.interpretations) >= self.MAX_INTERPRETATIONS:
            raise ValueError("maximum autobiographical interpretations reached")
        versions = self.for_experience(interpretation.experience_id)
        if len(versions) >= self.MAX_VERSIONS_PER_EXPERIENCE:
            raise ValueError("maximum autobiographical versions reached")
        if interpretation.version != len(versions) + 1:
            raise ValueError("autobiographical version must be sequential")
        if versions and interpretation.supersedes != versions[-1].interpretation_id:
            raise ValueError("new interpretation must supersede the latest version")
        if not versions and interpretation.supersedes is not None:
            raise ValueError("initial interpretation cannot supersede another")
        self.interpretations.append(interpretation)
        return interpretation

    def create_initial(self, *, experience: SubjectiveExperience, tick: int, meaning_kind: str = "ordinary") -> AutobiographicalInterpretation:
        existing = self.current(experience.experience_id)
        if existing:
            return existing
        return self.append(AutobiographicalInterpretation(
            1, _stable_id("autobio", experience.experience_id, 1, "initial_encoding"),
            experience.experience_id, experience.world_event_id, experience.memory_id, 1,
            experience.perceived_summary, experience.interpretation, meaning_kind,
            experience.confidence, experience.emotional_residue, 0.0, 0.0, 0.0,
            (experience.memory_id,) if experience.memory_id else (), (),
            (experience.world_event_id,), (), None, "initial_encoding", int(tick), "current",
        ))

    def append_revision(self, *, experience: SubjectiveExperience, prior: AutobiographicalInterpretation,
                        candidate: ReinterpretationCandidate, tick: int) -> AutobiographicalInterpretation:
        return self.append(AutobiographicalInterpretation(
            1, _stable_id("autobio", experience.experience_id, prior.version + 1, candidate.candidate_id),
            experience.experience_id, experience.world_event_id, experience.memory_id,
            prior.version + 1, experience.recall_surface(), candidate.proposed_meaning,
            candidate.proposed_meaning_kind, _bounded(candidate.confidence), prior.emotional_residue,
            _signed_bounded(prior.emotional_charge + candidate.emotional_charge_delta),
            max(prior.relationship_relevance, candidate.conflict_strength if candidate.trigger_type == "relationship_phase_change" else 0.0),
            prior.identity_relevance,
            tuple(dict.fromkeys((*prior.supporting_memory_ids, *candidate.supporting_memory_ids)))[-16:],
            tuple(dict.fromkeys((*prior.contradicting_memory_ids, *candidate.contradicting_memory_ids)))[-16:],
            tuple(dict.fromkeys((*prior.supporting_world_event_ids, *candidate.supporting_world_event_ids)))[-16:],
            tuple(dict.fromkeys((*prior.contradicting_world_event_ids, *candidate.contradicting_world_event_ids)))[-16:],
            prior.interpretation_id, candidate.trigger_type, int(tick), "current",
        ))

    def activate_for_memories(self, memory_ids: Sequence[str], *, relationship_relevance: float,
                              identity_relevance: float, emotional_match: float,
                              memory_links: Mapping[str, str] | None = None,
                              max_results: int = 4) -> tuple[AutobiographicalActivation, ...]:
        ids = set(memory_ids)
        links = dict(memory_links or {})
        activations = []
        for item in self.interpretations:
            linked_memory = item.memory_id or links.get(item.experience_id)
            if linked_memory not in ids and not set(item.supporting_memory_ids).intersection(ids):
                continue
            current = self.current(item.experience_id)
            is_current = bool(current and current.interpretation_id == item.interpretation_id)
            status_factor = 1.0 if is_current else 0.25
            score = _bounded(status_factor * (
                0.35 * item.confidence
                + 0.20 * item.relationship_relevance * _bounded(relationship_relevance)
                + 0.20 * item.identity_relevance * _bounded(identity_relevance)
                + 0.25 * max(0.0, 1.0 - abs(item.emotional_charge - _signed_bounded(emotional_match)))
            ))
            activations.append(AutobiographicalActivation(
                item.interpretation_id, item.experience_id, linked_memory, round(score, 6),
                "current" if is_current else "historical",
                (f"confidence:{item.confidence:.3f}", f"meaning:{item.meaning_kind}", f"status:{'current' if is_current else 'historical'}"),
            ))
        return tuple(sorted(activations, key=lambda item: (-item.activation, item.interpretation_id))[:max(0, min(4, int(max_results)))])

    def to_list(self) -> list[dict[str, Any]]:
        return [item.to_dict() for item in self.interpretations]

    @classmethod
    def from_list(cls, data: Sequence[Mapping[str, Any]] | None) -> "AutobiographicalInterpretationStore":
        return cls(AutobiographicalInterpretation.from_dict(item) for item in (data or ()))

    def _validate_history(self) -> None:
        grouped: dict[str, list[AutobiographicalInterpretation]] = {}
        for item in self.interpretations:
            grouped.setdefault(item.experience_id, []).append(item)
        for experience_id, versions in grouped.items():
            ordered = sorted(versions, key=lambda item: item.version)
            for index, item in enumerate(ordered, 1):
                if item.version != index:
                    raise ValueError(f"non-sequential autobiographical history: {experience_id}")
                if index == 1 and item.supersedes is not None:
                    raise ValueError("initial interpretation cannot supersede")
                if index > 1 and item.supersedes != ordered[index - 2].interpretation_id:
                    raise ValueError("broken autobiographical supersession chain")


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
