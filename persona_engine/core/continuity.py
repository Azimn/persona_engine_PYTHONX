"""Canonical continuity-event semantics for Project Wayfarer.

The continuity ledger is intentionally simpler than an adversarial audit chain.
It provides ordered, inspectable, replay-oriented biography for the local
single-owner threat model. Cryptographic previous-event chaining is not part of
this default profile.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import json
from typing import Any

from .event_classifier import can_promote_to_canonical_memory

CONTINUITY_SCHEMA_VERSION = "1.0"
STATE_DIGEST_SCHEMA_VERSION = "1.0"
SUBJECT_TIME_SEMANTICS = "engine_timestep"


@dataclass(frozen=True)
class ContinuityAuthority:
    source_actor: str
    source_class: str
    authority_class: str
    visibility: str = "character_observed"


@dataclass(frozen=True)
class ContinuityEvent:
    event_uuid: str
    subject_uuid: str
    character_id: str
    user_id: str
    sequence: int
    continuity_epoch: int
    subject_time: float
    wall_time: float
    source_actor: str
    source_class: str
    authority_class: str
    event_type: str
    visibility: str
    canonicality: str
    causal_parents: tuple[str, ...]
    payload_schema: str
    payload: dict[str, Any]
    legacy_event_id: int | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_uuid": self.event_uuid,
            "subject_uuid": self.subject_uuid,
            "character_id": self.character_id,
            "user_id": self.user_id,
            "sequence": self.sequence,
            "continuity_epoch": self.continuity_epoch,
            "subject_time": self.subject_time,
            "subject_time_semantics": SUBJECT_TIME_SEMANTICS,
            "wall_time": self.wall_time,
            "source_actor": self.source_actor,
            "source_class": self.source_class,
            "authority_class": self.authority_class,
            "event_type": self.event_type,
            "visibility": self.visibility,
            "canonicality": self.canonicality,
            "causal_parents": list(self.causal_parents),
            "payload_schema": self.payload_schema,
            "payload": self.payload,
            "legacy_event_id": self.legacy_event_id,
        }


@dataclass
class ContinuityIntegrityReport:
    ok: bool
    event_count: int
    first_sequence: int | None
    last_sequence: int | None
    missing_sequences: list[int] = field(default_factory=list)
    malformed_events: list[str] = field(default_factory=list)
    subject_mismatches: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "event_count": self.event_count,
            "first_sequence": self.first_sequence,
            "last_sequence": self.last_sequence,
            "missing_sequences": list(self.missing_sequences),
            "malformed_events": list(self.malformed_events),
            "subject_mismatches": list(self.subject_mismatches),
        }


def event_authority(event_type: str, payload: dict[str, Any] | None = None) -> ContinuityAuthority:
    """Return default provenance/authority metadata for a canonical event family.

    User speech is authoritative evidence that the user *said something*, not
    authority that the proposition inside the speech is objectively true.
    """

    payload = payload or {}
    explicit_actor = str(payload.get("source_actor", "")).strip()
    if event_type in {"input", "user_statement"}:
        return ContinuityAuthority(explicit_actor or "user", "external_user", "reported_input")
    if event_type in {"sensorium", "sensor_observation", "world_fact", "manual_authorized_fact", "world_action_resolution"}:
        return ContinuityAuthority(explicit_actor or "host", "host_world", "world_authority")
    if event_type == "dream_consolidation":
        return ContinuityAuthority(explicit_actor or "character_core", "internal_core", "consolidation_authority", "private")
    if event_type == "state_transition":
        return ContinuityAuthority(explicit_actor or "character_core", "internal_core", "character_state_authority", "private")
    return ContinuityAuthority(explicit_actor or "unknown", "unspecified", "canonical_event")


def canonical_continuity_eligible(event_type: str, payload: dict[str, Any] | None = None) -> bool:
    """Use existing fail-closed canonicality policy for ledger admission."""

    payload = payload or {}
    if event_type == "world_action_resolution":
        # WorldAuthority resolution is canonical only when the host actually
        # accepted/resolved the proposal. Rejected proposals remain diagnostics.
        return bool(payload.get("accepted"))
    if event_type == "sensor_observation":
        # These payloads are produced only after the bounded sensory router has
        # converted host observation into safe observation/fact structures.
        return isinstance(payload.get("observation"), dict) and payload.get("sensor_type") in {"audio", "vision"}
    return can_promote_to_canonical_memory(event_type, payload)


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def state_digest(value: Any) -> str:
    """Deterministic checkpoint digest, not an event-chain security primitive."""

    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()
