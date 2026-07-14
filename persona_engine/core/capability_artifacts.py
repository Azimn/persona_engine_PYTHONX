"""Validated durable artifacts shared by every renderer capability tier."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
import hashlib
from typing import Any


VALID_KINDS = {"episodic", "semantic", "procedural", "relationship", "belief_evidence", "research", "strategy", "summary", "template"}
VALID_STATES = {"verified", "supported", "uncertain", "challenged", "rejected"}
VALID_CANONICALITY = {"objective", "subjective", "inferred", "uncertain"}


@dataclass
class CapabilityArtifact:
    artifact_id: str
    kind: str
    content: str
    source_tier: int
    provenance: dict[str, Any]
    confidence: float
    verification_state: str
    supporting_event_ids: tuple[str, ...] = ()
    canonicality: str = "uncertain"
    created_at: float = 0.0
    available_to_tiers: tuple[int, ...] = (0, 1, 2, 3)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CapabilityArtifact":
        raw = dict(data)
        raw["supporting_event_ids"] = tuple(raw.get("supporting_event_ids", ()))
        raw["available_to_tiers"] = tuple(raw.get("available_to_tiers", (0, 1, 2, 3)))
        return cls(**raw)


class CapabilityArtifactStore:
    def __init__(self, artifacts: list[CapabilityArtifact] | None = None):
        self.artifacts = list(artifacts or [])

    def add(self, *, kind: str, content: str, source_tier: int, provenance: dict[str, Any], confidence: float,
            verification_state: str, supporting_event_ids=(), canonicality: str = "uncertain",
            created_at: float = 0.0) -> CapabilityArtifact:
        if kind not in VALID_KINDS:
            raise ValueError(f"unsupported artifact kind: {kind}")
        if verification_state not in VALID_STATES:
            raise ValueError(f"unsupported verification state: {verification_state}")
        if canonicality not in VALID_CANONICALITY:
            raise ValueError(f"unsupported canonicality: {canonicality}")
        if canonicality == "objective" and not supporting_event_ids:
            raise ValueError("objective artifacts require supporting world events")
        payload = f"{kind}|{content}|{source_tier}|{len(self.artifacts)}".encode("utf-8")
        artifact = CapabilityArtifact(
            artifact_id="artifact_" + hashlib.blake2b(payload, digest_size=8).hexdigest(),
            kind=kind, content=str(content)[:2000], source_tier=max(0, min(3, int(source_tier))),
            provenance=dict(provenance), confidence=max(0.0, min(1.0, float(confidence))),
            verification_state=verification_state, supporting_event_ids=tuple(str(item) for item in supporting_event_ids),
            canonicality=canonicality, created_at=float(created_at),
        )
        self.artifacts.append(artifact)
        return artifact

    def available(self, tier: int, include_challenged: bool = False) -> list[CapabilityArtifact]:
        return [item for item in self.artifacts if tier in item.available_to_tiers and (include_challenged or item.verification_state not in {"challenged", "rejected"})]

    def challenge(self, artifact_id: str, evidence_strength: float) -> CapabilityArtifact | None:
        artifact = next((item for item in self.artifacts if item.artifact_id == artifact_id), None)
        if artifact is None:
            return None
        artifact.confidence = max(0.0, artifact.confidence - max(0.0, min(1.0, evidence_strength)) * 0.5)
        if artifact.confidence < 0.45:
            artifact.verification_state = "challenged"
        return artifact

    def to_list(self) -> list[dict[str, Any]]:
        return [item.to_dict() for item in self.artifacts]

    @classmethod
    def from_list(cls, data: list[dict[str, Any]] | None) -> "CapabilityArtifactStore":
        return cls([CapabilityArtifact.from_dict(item) for item in (data or [])])
