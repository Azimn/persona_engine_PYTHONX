"""Small, inspectable semantic priors for situated cognition.

The substrate supplies generic candidates only.  It cannot author world facts,
beliefs, memories, intentions, or actions.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
import json
from pathlib import Path
from typing import Any, Iterable, Mapping


class SemanticValue(str, Enum):
    UNKNOWN = "unknown"
    FALSE = "false"
    TRUE = "true"
    USUALLY = "usually"
    SOMETIMES = "sometimes"


_VALUE_WEIGHT = {
    SemanticValue.FALSE: -127,
    SemanticValue.TRUE: 127,
    SemanticValue.USUALLY: 88,
    SemanticValue.SOMETIMES: 38,
    SemanticValue.UNKNOWN: 0,
}


@dataclass(frozen=True)
class SemanticFeatureAssertion:
    feature_id: int
    feature_name: str
    value: SemanticValue
    confidence: int
    source_id: str


@dataclass(frozen=True)
class SemanticRelationAssertion:
    relation_id: int
    relation_name: str
    target_id: int
    value: SemanticValue
    confidence: int
    source_id: str


@dataclass(frozen=True)
class SemanticAffordanceDefinition:
    action: str
    target_id: int
    relevance: int
    source_id: str


@dataclass(frozen=True)
class SemanticConcept:
    concept_id: int
    name: str
    parent_id: int | None
    features: tuple[SemanticFeatureAssertion, ...] = ()
    relations: tuple[SemanticRelationAssertion, ...] = ()
    affordances: tuple[SemanticAffordanceDefinition, ...] = ()


@dataclass(frozen=True)
class ResolvedFeature:
    feature_id: int
    feature_name: str
    value: SemanticValue
    confidence: int
    asserted_on: int | None
    inherited_from: int | None
    source_id: str | None


@dataclass(frozen=True)
class ActiveConcept:
    concept_id: int
    name: str
    activation: int
    source_kind: str
    source_id: str


@dataclass(frozen=True)
class ActiveFeature:
    feature_id: int
    feature_name: str
    value: SemanticValue
    activation: int
    asserted_on: int
    inherited_from: int | None
    source_id: str


@dataclass(frozen=True)
class SemanticAffordance:
    action: str
    target_id: int
    target_name: str
    relevance: int
    source_id: str


@dataclass(frozen=True)
class SemanticActivationFrame:
    input_concept_ids: tuple[int, ...]
    concepts: tuple[ActiveConcept, ...]
    features: tuple[ActiveFeature, ...]
    affordances: tuple[SemanticAffordance, ...]
    unresolved_questions: tuple[str, ...]
    warnings: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class SemanticSubstrate:
    """Read-only concept graph with compiled sparse feature profiles."""

    def __init__(self, concepts: Iterable[SemanticConcept]):
        ordered = tuple(sorted(concepts, key=lambda item: item.concept_id))
        self.concepts = {item.concept_id: item for item in ordered}
        self.names = {item.name: item.concept_id for item in ordered}
        if len(self.concepts) != len(ordered) or len(self.names) != len(ordered):
            raise ValueError("semantic concept IDs and names must be unique")
        self.profiles = {concept_id: self._compile_profile(concept_id) for concept_id in self.concepts}

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> "SemanticSubstrate":
        concepts = []
        for raw in data.get("concepts", []):
            concept_id = int(raw["id"])
            features = tuple(
                SemanticFeatureAssertion(
                    int(item["id"]), str(item["name"]), SemanticValue(str(item["value"])),
                    _confidence(item.get("confidence", 100)), str(item.get("source_id", "base")),
                )
                for item in raw.get("features", [])
            )
            relations = tuple(
                SemanticRelationAssertion(
                    int(item["id"]), str(item["name"]), int(item["target_id"]),
                    SemanticValue(str(item.get("value", "true"))),
                    _confidence(item.get("confidence", 100)), str(item.get("source_id", "base")),
                )
                for item in raw.get("relations", [])
            )
            affordances = tuple(
                SemanticAffordanceDefinition(
                    str(item["action"]), int(item.get("target_id", concept_id)),
                    _confidence(item.get("relevance", 50)), str(item.get("source_id", "base")),
                )
                for item in raw.get("affordances", [])
            )
            concepts.append(SemanticConcept(
                concept_id, str(raw["name"]),
                int(raw["parent_id"]) if raw.get("parent_id") is not None else None,
                features, relations, affordances,
            ))
        substrate = cls(concepts)
        substrate._validate_references()
        return substrate

    @classmethod
    def from_json(cls, path: str | Path) -> "SemanticSubstrate":
        with Path(path).open("r", encoding="utf-8") as handle:
            data = json.load(handle)
        if not isinstance(data, dict):
            raise ValueError("semantic substrate root must be an object")
        return cls.from_mapping(data)

    def resolve_concept_id(self, value: int | str) -> int | None:
        if isinstance(value, bool):
            return None
        if isinstance(value, int):
            return value if value in self.concepts else None
        text = str(value).strip().lower()
        if text.isdigit() and int(text) in self.concepts:
            return int(text)
        return self.names.get(text)

    def resolve_feature(self, concept_id: int, feature_id: int) -> ResolvedFeature:
        current_id: int | None = int(concept_id)
        inherited = False
        visited: set[int] = set()
        while current_id is not None and current_id not in visited and len(visited) < 16:
            visited.add(current_id)
            concept = self.concepts.get(current_id)
            if concept is None:
                break
            match = next((item for item in concept.features if item.feature_id == int(feature_id)), None)
            if match:
                return ResolvedFeature(
                    match.feature_id, match.feature_name, match.value, match.confidence,
                    asserted_on=current_id,
                    inherited_from=current_id if inherited else None,
                    source_id=match.source_id,
                )
            inherited = True
            current_id = concept.parent_id
        return ResolvedFeature(int(feature_id), "unknown", SemanticValue.UNKNOWN, 0, None, None, None)

    def semantic_overlap(self, first_id: int, second_id: int) -> int:
        first = self.profiles.get(first_id, {})
        second = self.profiles.get(second_id, {})
        shared = set(first) & set(second)
        return sum(min(abs(first[item]), abs(second[item])) for item in shared if first[item] * second[item] > 0)

    def activate(
        self,
        concept_ids: Iterable[int | str],
        *,
        max_concepts: int = 12,
        max_features: int = 16,
        max_affordances: int = 8,
    ) -> SemanticActivationFrame:
        resolved: list[int] = []
        warnings: list[str] = []
        for raw in concept_ids:
            concept_id = self.resolve_concept_id(raw)
            if concept_id is None:
                warnings.append(f"unknown_concept:{str(raw)[:48]}")
            elif concept_id not in resolved:
                resolved.append(concept_id)
        resolved = resolved[:8]
        active: dict[int, ActiveConcept] = {}

        def add(concept_id: int, activation: int, source_kind: str, source_id: str) -> None:
            concept = self.concepts.get(concept_id)
            if not concept:
                return
            candidate = ActiveConcept(concept_id, concept.name, activation, source_kind, source_id)
            current = active.get(concept_id)
            if current is None or candidate.activation > current.activation:
                active[concept_id] = candidate

        for concept_id in resolved:
            add(concept_id, 100, "observed_concept", f"concept:{concept_id}")
            concept = self.concepts[concept_id]
            if concept.parent_id is not None:
                add(concept.parent_id, 72, "parent", f"concept:{concept_id}")
            for relation in concept.relations:
                if relation.value not in {SemanticValue.FALSE, SemanticValue.UNKNOWN}:
                    add(relation.target_id, min(65, relation.confidence * 2 // 3), "one_hop_relation", relation.source_id)

        concepts = tuple(sorted(active.values(), key=lambda item: (-item.activation, item.concept_id))[:max(0, min(12, max_concepts))])
        features: dict[int, ActiveFeature] = {}
        affordances: list[SemanticAffordance] = []
        for active_concept in concepts:
            concept = self.concepts[active_concept.concept_id]
            feature_ids = {item.feature_id for item in concept.features}
            parent_id = concept.parent_id
            while parent_id is not None and parent_id in self.concepts:
                feature_ids.update(item.feature_id for item in self.concepts[parent_id].features)
                parent_id = self.concepts[parent_id].parent_id
            for feature_id in sorted(feature_ids):
                item = self.resolve_feature(concept.concept_id, feature_id)
                if item.value == SemanticValue.UNKNOWN or item.asserted_on is None or item.source_id is None:
                    continue
                activation = active_concept.activation * item.confidence // 100
                candidate = ActiveFeature(
                    item.feature_id, item.feature_name, item.value, activation,
                    item.asserted_on, item.inherited_from, item.source_id,
                )
                current = features.get(feature_id)
                if current is None or candidate.activation > current.activation:
                    features[feature_id] = candidate
            for item in concept.affordances:
                target = self.concepts.get(item.target_id)
                if target:
                    affordances.append(SemanticAffordance(
                        item.action, item.target_id, target.name,
                        item.relevance * active_concept.activation // 100, item.source_id,
                    ))
        ranked_features = tuple(sorted(
            features.values(), key=lambda item: (-item.activation, item.feature_id, item.asserted_on),
        )[:max(0, min(16, max_features))])
        ranked_affordances = tuple(sorted(
            affordances, key=lambda item: (-item.relevance, item.action, item.target_id),
        )[:max(0, min(8, max_affordances))])
        questions = ()
        if any(item.feature_name == "restricted_access" for item in ranked_features):
            questions = ("instance_permission_or_ownership_is_unknown",)
        return SemanticActivationFrame(
            tuple(resolved), concepts, ranked_features, ranked_affordances,
            questions, tuple(warnings),
        )

    def _compile_profile(self, concept_id: int) -> dict[int, int]:
        feature_ids: set[int] = set()
        current_id: int | None = concept_id
        visited: set[int] = set()
        while current_id is not None and current_id not in visited:
            visited.add(current_id)
            concept = self.concepts.get(current_id)
            if not concept:
                break
            feature_ids.update(item.feature_id for item in concept.features)
            current_id = concept.parent_id
        profile = {}
        for feature_id in feature_ids:
            item = self.resolve_feature(concept_id, feature_id)
            profile[feature_id] = _VALUE_WEIGHT[item.value] * item.confidence // 100
        return profile

    def _validate_references(self) -> None:
        for concept in self.concepts.values():
            if concept.parent_id is not None and concept.parent_id not in self.concepts:
                raise ValueError(f"unknown semantic parent: {concept.parent_id}")
            for relation in concept.relations:
                if relation.target_id not in self.concepts:
                    raise ValueError(f"unknown semantic relation target: {relation.target_id}")
            for affordance in concept.affordances:
                if affordance.target_id not in self.concepts:
                    raise ValueError(f"unknown semantic affordance target: {affordance.target_id}")


def _confidence(value: Any) -> int:
    number = int(value)
    if not 0 <= number <= 100:
        raise ValueError("semantic confidence/relevance must be within [0, 100]")
    return number


def load_default_substrate() -> SemanticSubstrate:
    path = Path(__file__).resolve().parents[1] / "semantic_data" / "core_semantics.json"
    return SemanticSubstrate.from_json(path)
