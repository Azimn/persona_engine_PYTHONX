"""Structured schemas for private cognition, deception, and replay.

Generated prose is untrusted. Runtime mutation may only happen from validated
structured fields represented here.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from typing import Literal


@dataclass
class Impulse:
    type: str
    strength: float
    target: str


@dataclass
class PrivateCognitionProposal:
    """Raw model output for the private-cognition task. Untrusted input."""

    prose: str
    attention_targets: list[str]
    pressure_deltas: dict[str, float]
    impulse_candidates: list[Impulse]
    memory_activation_requests: list[str]
    cognitive_theme_ids: list[str]


@dataclass
class CognitiveApplicationReport:
    """Validated private-cognition effects.

    This report is persistable audit data. Raw private prose is not persisted as
    state and must not directly mutate canonical stores.
    """

    applied_pressure_deltas: dict[str, float]
    rejected_pressure_deltas: dict[str, str]
    accepted_impulses: list[Impulse]
    rejected_impulses: list[tuple[Impulse, str]]
    activated_memory_ids: list[str]
    unresolved_memory_requests: list[str]
    accepted_theme_ids: list[str]
    rejected_theme_ids: list[tuple[str, str]]


HabitEvidenceSource = Literal[
    "expressed_action", "expressed_speech", "private_cognition", "observed_outcome"
]

EVIDENCE_WEIGHTS: dict[HabitEvidenceSource, float] = {
    "private_cognition": 0.10,
    "expressed_speech": 0.30,
    "expressed_action": 0.50,
    "observed_outcome": 0.70,
}


@dataclass
class NormalizedClaim:
    subject: str
    predicate: str
    object: str
    polarity: bool
    qualifiers: dict[str, str] = field(default_factory=dict)


@dataclass
class DeceptionAuthorization:
    mode: str
    audience: str
    topic: str
    permitted_claim_scope: list[str]
    may_fabricate_memory: bool = False


@dataclass
class DeceptionClaim:
    claim_id: str
    audience: str
    topic: str
    mode: str
    spoken_claim: str
    normalized_claim: NormalizedClaim
    concealed_belief_id: str | None
    concealed_memory_ids: list[str]
    consistency_obligation: str
    created_at: float
    status: str = "active"


def stable_turn_seed(session_id: str, turn_index: int, cognition_channel: str) -> int:
    payload = f"{session_id}:{turn_index}:{cognition_channel}".encode("utf-8")
    digest = hashlib.blake2b(payload, digest_size=8).digest()
    return int.from_bytes(digest, byteorder="big", signed=False)


def turn_seed(session_id: str, turn_index: int, channel: str) -> int:
    """Backward-compatible stable replay seed helper."""

    return stable_turn_seed(session_id, turn_index, channel)
