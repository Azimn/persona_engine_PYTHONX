"""Bounded actor identity and per-interlocutor relationship records."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import re
from typing import Any, Mapping, Sequence

from .relationship import RelationshipState


MAX_ACTORS = 256
MAX_ALIASES = 8
ACTOR_KINDS = frozenset({"human", "npc", "character", "historical", "unknown"})


def _normalize(value: str) -> str:
    return " ".join(re.findall(r"[a-z0-9]+", str(value).lower()))[:120]


def _fnv1a_32(value: str) -> int:
    result = 2166136261
    for byte in value.encode("utf-8", errors="ignore"):
        result ^= byte
        result = (result * 16777619) & 0xFFFFFFFF
    return result or 1


def _derived_aliases(display_name: str) -> tuple[str, ...]:
    generic = {"the", "doctor", "professor", "unknown"}
    parts = [
        item for item in re.findall(r"[A-Za-z0-9']+", display_name)
        if len(item) >= 3 and item.casefold() not in generic
    ]
    return tuple(dict.fromkeys((display_name, *parts)))[:MAX_ALIASES]


def _bounded_aliases(display_name: str, aliases: Sequence[object]) -> tuple[str, ...]:
    values = (*_derived_aliases(display_name), *(str(item).strip()[:120] for item in aliases))
    return tuple(dict.fromkeys(item for item in values if item))[:MAX_ALIASES]


@dataclass
class ActorRecord:
    schema_version: int
    actor_id: int
    stable_key: str
    display_name: str
    aliases: tuple[str, ...]
    actor_kind: str
    source: str
    recognition_confidence: float
    first_seen_tick: int
    last_seen_tick: int
    encounter_count: int = 1

    def __post_init__(self) -> None:
        if not 0 < int(self.actor_id) <= 0xFFFFFFFF:
            raise ValueError("actor_id must be a nonzero uint32")
        if self.actor_kind not in ACTOR_KINDS:
            raise ValueError(f"unsupported actor kind: {self.actor_kind}")
        if not 0.0 <= float(self.recognition_confidence) <= 1.0:
            raise ValueError("recognition confidence must be within [0, 1]")
        if not self.stable_key or len(self.stable_key) > 160:
            raise ValueError("actor stable_key must contain 1..160 characters")
        if not self.display_name or len(self.display_name) > 120:
            raise ValueError("actor display_name must contain 1..120 characters")
        if len(self.aliases) > MAX_ALIASES:
            raise ValueError("actor alias bound exceeded")
        if any(not isinstance(item, str) or not item or len(item) > 120 for item in self.aliases):
            raise ValueError("actor aliases must contain 1..120 characters")

    @property
    def reference(self) -> str:
        return f"actor:{self.actor_id:08x}"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "ActorRecord":
        raw = {key: value[key] for key in cls.__dataclass_fields__ if key in value}
        raw["aliases"] = tuple(raw.get("aliases", ()))
        return cls(**raw)


class ActorRegistry:
    def __init__(self, records: Sequence[ActorRecord] = ()):
        if len(records) > MAX_ACTORS:
            raise ValueError("actor registry bound exceeded")
        if len({item.actor_id for item in records}) != len(records):
            raise ValueError("duplicate actor_id in registry")
        if len({item.stable_key for item in records}) != len(records):
            raise ValueError("duplicate actor stable_key in registry")
        self.records = {int(item.actor_id): item for item in records}
        self._keys = {item.stable_key: item.actor_id for item in records}

    def resolve(
        self, *, stable_key: str, display_name: str, tick: int,
        actor_kind: str = "unknown", source: str = "interaction",
        aliases: Sequence[str] = (), recognition_confidence: float = 1.0,
        observe: bool = True,
    ) -> ActorRecord:
        key = str(stable_key)[:160]
        existing_id = self._keys.get(key)
        if existing_id is not None:
            record = self.records[existing_id]
            merged = _bounded_aliases(display_name, (*record.aliases, *aliases))
            record.aliases = merged
            record.recognition_confidence = max(record.recognition_confidence, float(recognition_confidence))
            if observe:
                record.last_seen_tick = max(record.last_seen_tick, int(tick))
                record.encounter_count += 1
            return record
        if len(self.records) >= MAX_ACTORS:
            raise ValueError("actor registry is full")
        actor_id = _fnv1a_32(key)
        while actor_id in self.records and self.records[actor_id].stable_key != key:
            actor_id = (actor_id + 1) & 0xFFFFFFFF or 1
        name = str(display_name).strip()[:120] or "unknown person"
        record = ActorRecord(
            1, actor_id, key, name,
            _bounded_aliases(name, aliases),
            actor_kind, str(source)[:80], max(0.0, min(1.0, float(recognition_confidence))),
            int(tick), int(tick), 1,
        )
        self.records[actor_id] = record
        self._keys[key] = actor_id
        return record

    def fetch(self, actor_id: int) -> ActorRecord | None:
        return self.records.get(int(actor_id))

    def match_text(self, text: str) -> tuple[ActorRecord, ...]:
        lowered = f" {_normalize(text)} "
        matches = []
        for record in self.records.values():
            if any(f" {_normalize(alias)} " in lowered for alias in record.aliases if _normalize(alias)):
                matches.append(record)
        return tuple(sorted(matches, key=lambda item: (-item.recognition_confidence, -item.encounter_count, item.actor_id)))

    def display_label(self, actor_id: int) -> str:
        record = self.fetch(actor_id)
        if record is None:
            return "unknown person"
        same = sorted(
            (item for item in self.records.values() if _normalize(item.display_name) == _normalize(record.display_name)),
            key=lambda item: item.actor_id,
        )
        if len(same) <= 1:
            return record.display_name
        index = same.index(record)
        suffix = chr(ord("A") + index) if index < 26 else str(index + 1)
        return f"{record.display_name}-{suffix}"

    def to_list(self) -> list[dict[str, Any]]:
        return [item.to_dict() for item in sorted(self.records.values(), key=lambda value: value.actor_id)]

    def inspection_list(self) -> list[dict[str, Any]]:
        return [
            {**item.to_dict(), "display_label": self.display_label(item.actor_id)}
            for item in sorted(self.records.values(), key=lambda value: value.actor_id)
        ]

    @classmethod
    def from_list(cls, values: Sequence[Mapping[str, Any]] | None) -> "ActorRegistry":
        return cls(tuple(ActorRecord.from_dict(item) for item in (values or ())))


class ActorRelationshipStore:
    def __init__(self, values: Mapping[int, RelationshipState] | None = None):
        self.values = dict(values or {})

    def for_actor(self, actor_id: int) -> RelationshipState:
        actor_id = int(actor_id)
        if actor_id not in self.values:
            self.values[actor_id] = RelationshipState(user_id=f"actor:{actor_id:08x}")
        return self.values[actor_id]

    def to_list(self) -> list[dict[str, Any]]:
        return [
            {"actor_id": actor_id, "relationship": asdict(state)}
            for actor_id, state in sorted(self.values.items())
        ]

    @classmethod
    def from_list(cls, values: Sequence[Mapping[str, Any]] | None) -> "ActorRelationshipStore":
        result = {}
        for item in values or ():
            raw = dict(item.get("relationship") or {})
            result[int(item["actor_id"])] = RelationshipState(**raw)
        return cls(result)
