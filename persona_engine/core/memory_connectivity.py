"""Bounded learned connections among existing canonical records."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
from typing import Any, Mapping, Sequence


CONNECTION_KINDS = frozenset({
    "co_recalled", "supports", "contradicts", "same_pattern", "relationship_context",
    "identity_context", "interpretation_context", "action_context", "skill_source",
    "helpful_guidance", "failed_guidance",
})


@dataclass
class MemoryConnection:
    schema_version: int
    connection_id: str
    source_id: str
    target_id: str
    relation_kind: str
    context_signature: str
    strength: float
    confidence: float
    successful_activations: int
    failed_activations: int
    neutral_activations: int
    created_tick: int
    last_activated_tick: int
    provenance_ids: tuple[str, ...]
    state: str = "tentative"

    def to_dict(self): return asdict(self)
    @classmethod
    def from_dict(cls, data):
        raw = dict(data); raw["provenance_ids"] = tuple(raw.get("provenance_ids", ()))
        return cls(**raw)


class MemoryConnectionStore:
    MAX_CONNECTIONS = 4096
    MAX_ACTIVE_CONNECTIONS_PER_NODE = 8
    MAX_NEW_CONNECTIONS_PER_TURN = 4
    MAX_RETRIEVAL_BOOST = .25

    def __init__(self, connections: Sequence[MemoryConnection] = ()):
        self.connections = list(connections)[:self.MAX_CONNECTIONS]

    def connect(self, source_id: str, target_id: str, relation_kind: str, context_signature: str,
                tick: int, provenance_ids=(), delta: float = .04) -> MemoryConnection | None:
        if relation_kind not in CONNECTION_KINDS or source_id == target_id:
            return None
        key = json.dumps([source_id, target_id, relation_kind, context_signature], separators=(",", ":")).encode()
        cid = "memory_connection_" + hashlib.blake2b(key, digest_size=8).hexdigest()
        existing = next((item for item in self.connections if item.connection_id == cid), None)
        if existing:
            existing.strength = min(1.0, existing.strength + max(-.05, min(.05, delta)))
            existing.confidence = min(1.0, existing.confidence + .02)
            existing.last_activated_tick = tick
            existing.neutral_activations += 1
            existing.state = "strong" if existing.strength >= .75 and existing.confidence >= .75 else "supported" if existing.strength >= .20 else "tentative"
            return existing
        if len(self.connections) >= self.MAX_CONNECTIONS:
            return None
        item = MemoryConnection(1, cid, source_id, target_id, relation_kind, context_signature,
                                max(0.0, min(1.0, delta)), .5, 0, 0, 1, tick, tick,
                                tuple(dict.fromkeys(provenance_ids))[-16:])
        self.connections.append(item)
        return item

    def boosts_for(self, source_ids: Sequence[str]) -> dict[str, float]:
        boosts: dict[str, float] = {}
        for connection in self.connections:
            if connection.source_id in source_ids and connection.state != "pruned":
                boosts[connection.target_id] = min(self.MAX_RETRIEVAL_BOOST,
                                                   boosts.get(connection.target_id, 0.0) + connection.strength * connection.confidence)
        return boosts

    def to_list(self): return [item.to_dict() for item in self.connections]
    @classmethod
    def from_list(cls, data): return cls([MemoryConnection.from_dict(item) for item in (data or ())])
