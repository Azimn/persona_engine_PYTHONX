"""Provenance-aware current belief state for Project Ensemble.

The existing memory system can preserve that the subject heard a claim and the
WorldAuthority can preserve what the host establishes as true. Those are not the
same as what the subject currently believes. This module represents that missing
middle explicitly.

Evidence is append-only. Belief revision is explicit. Testimony does not become
world truth merely because it was heard, model inference does not become fact,
and a later correction does not rewrite the original evidence.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Iterable


EPISTEMIC_LEDGER_SCHEMA = "ensemble-epistemic-ledger-v1"


class EpistemicStance(str, Enum):
    UNKNOWN = "unknown"
    TENTATIVE = "tentative"
    BELIEVED = "believed"
    DISBELIEVED = "disbelieved"


class EvidenceSource(str, Enum):
    TESTIMONY = "testimony"
    OBSERVATION = "observation"
    WORLD_AUTHORITY = "world_authority"
    MODEL_INFERENCE = "model_inference"
    SELF_INFERENCE = "self_inference"


@dataclass(frozen=True)
class EpistemicEvidence:
    evidence_id: str
    proposition_key: str
    proposition_text: str
    polarity: int
    source: EvidenceSource
    source_ref: str
    observed_at: float
    confidence: float = 1.0
    claim_valid_from: float | None = None
    claim_valid_until: float | None = None

    def __post_init__(self):
        if not self.evidence_id or not self.proposition_key or not self.proposition_text:
            raise ValueError("evidence_id, proposition_key and proposition_text are required")
        if int(self.polarity) not in {-1, 1}:
            raise ValueError("polarity must be -1 or 1")
        if not 0.0 <= float(self.confidence) <= 1.0:
            raise ValueError("confidence must be between 0 and 1")
        if (
            self.claim_valid_from is not None
            and self.claim_valid_until is not None
            and float(self.claim_valid_until) < float(self.claim_valid_from)
        ):
            raise ValueError("claim_valid_until cannot precede claim_valid_from")

    def to_dict(self) -> dict:
        return {
            "evidence_id": self.evidence_id,
            "proposition_key": self.proposition_key,
            "proposition_text": self.proposition_text,
            "polarity": self.polarity,
            "source": self.source.value,
            "source_ref": self.source_ref,
            "observed_at": self.observed_at,
            "confidence": self.confidence,
            "claim_valid_from": self.claim_valid_from,
            "claim_valid_until": self.claim_valid_until,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "EpistemicEvidence":
        return cls(
            evidence_id=str(data["evidence_id"]),
            proposition_key=str(data["proposition_key"]),
            proposition_text=str(data["proposition_text"]),
            polarity=int(data["polarity"]),
            source=EvidenceSource(data["source"]),
            source_ref=str(data.get("source_ref", "")),
            observed_at=float(data["observed_at"]),
            confidence=float(data.get("confidence", 1.0)),
            claim_valid_from=data.get("claim_valid_from"),
            claim_valid_until=data.get("claim_valid_until"),
        )


@dataclass(frozen=True)
class EpistemicProposition:
    proposition_key: str
    proposition_text: str
    stance: EpistemicStance = EpistemicStance.UNKNOWN
    confidence: float = 0.0
    evidence_refs: tuple[str, ...] = ()
    updated_at: float = 0.0
    revision_source: str = ""

    def __post_init__(self):
        if not self.proposition_key or not self.proposition_text:
            raise ValueError("proposition_key and proposition_text are required")
        if not 0.0 <= float(self.confidence) <= 1.0:
            raise ValueError("confidence must be between 0 and 1")
        if self.stance == EpistemicStance.UNKNOWN and self.confidence != 0.0:
            raise ValueError("unknown stance must have zero confidence")

    def to_dict(self) -> dict:
        return {
            "proposition_key": self.proposition_key,
            "proposition_text": self.proposition_text,
            "stance": self.stance.value,
            "confidence": self.confidence,
            "evidence_refs": list(self.evidence_refs),
            "updated_at": self.updated_at,
            "revision_source": self.revision_source,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "EpistemicProposition":
        return cls(
            proposition_key=str(data["proposition_key"]),
            proposition_text=str(data["proposition_text"]),
            stance=EpistemicStance(data.get("stance", "unknown")),
            confidence=float(data.get("confidence", 0.0)),
            evidence_refs=tuple(str(value) for value in data.get("evidence_refs", ())),
            updated_at=float(data.get("updated_at", 0.0)),
            revision_source=str(data.get("revision_source", "")),
        )


@dataclass(frozen=True)
class EpistemicRevision:
    proposition_key: str
    before_stance: EpistemicStance
    after_stance: EpistemicStance
    before_confidence: float
    after_confidence: float
    evidence_refs: tuple[str, ...]
    revised_at: float
    source: str
    reason: str

    def to_dict(self) -> dict:
        return {
            "proposition_key": self.proposition_key,
            "before_stance": self.before_stance.value,
            "after_stance": self.after_stance.value,
            "before_confidence": self.before_confidence,
            "after_confidence": self.after_confidence,
            "evidence_refs": list(self.evidence_refs),
            "revised_at": self.revised_at,
            "source": self.source,
            "reason": self.reason,
        }


@dataclass
class EpistemicLedger:
    """Append-only evidence plus current explicitly revised subject beliefs."""

    evidence: dict[str, EpistemicEvidence] = field(default_factory=dict)
    propositions: dict[str, EpistemicProposition] = field(default_factory=dict)
    revisions: list[EpistemicRevision] = field(default_factory=list)

    def record_evidence(self, item: EpistemicEvidence) -> None:
        existing = self.evidence.get(item.evidence_id)
        if existing is not None and existing != item:
            raise ValueError("evidence_id already exists with different content")
        self.evidence[item.evidence_id] = item

    def evidence_for(self, proposition_key: str) -> tuple[EpistemicEvidence, ...]:
        return tuple(
            item for item in self.evidence.values()
            if item.proposition_key == proposition_key
        )

    def current(self, proposition_key: str, proposition_text: str | None = None) -> EpistemicProposition:
        if proposition_key in self.propositions:
            return self.propositions[proposition_key]
        if proposition_text is None:
            matching = self.evidence_for(proposition_key)
            proposition_text = matching[0].proposition_text if matching else proposition_key
        return EpistemicProposition(
            proposition_key=proposition_key,
            proposition_text=str(proposition_text),
        )

    def revise(
        self,
        *,
        proposition_key: str,
        proposition_text: str,
        stance: EpistemicStance,
        confidence: float,
        evidence_refs: Iterable[str],
        revised_at: float,
        source: str,
        reason: str,
    ) -> EpistemicRevision:
        refs = tuple(dict.fromkeys(str(ref) for ref in evidence_refs if str(ref)))
        confidence = float(confidence)
        if not 0.0 <= confidence <= 1.0:
            raise ValueError("confidence must be between 0 and 1")
        if stance == EpistemicStance.UNKNOWN:
            if confidence != 0.0:
                raise ValueError("unknown stance must have zero confidence")
        elif not refs:
            raise ValueError("non-unknown belief revision requires explicit evidence refs")

        for ref in refs:
            item = self.evidence.get(ref)
            if item is None:
                raise ValueError(f"unknown evidence ref: {ref}")
            if item.proposition_key != proposition_key:
                raise ValueError("cross-proposition evidence cannot support revision")

        before = self.current(proposition_key, proposition_text)
        after = EpistemicProposition(
            proposition_key=proposition_key,
            proposition_text=proposition_text,
            stance=stance,
            confidence=confidence,
            evidence_refs=refs,
            updated_at=float(revised_at),
            revision_source=str(source),
        )
        self.propositions[proposition_key] = after
        revision = EpistemicRevision(
            proposition_key=proposition_key,
            before_stance=before.stance,
            after_stance=after.stance,
            before_confidence=before.confidence,
            after_confidence=after.confidence,
            evidence_refs=refs,
            revised_at=float(revised_at),
            source=str(source),
            reason=str(reason),
        )
        self.revisions.append(revision)
        return revision

    def first_person_status(self, proposition_key: str, proposition_text: str | None = None) -> str:
        state = self.current(proposition_key, proposition_text)
        text = state.proposition_text
        if state.stance == EpistemicStance.BELIEVED:
            return f"I currently believe {text}."
        if state.stance == EpistemicStance.TENTATIVE:
            return f"I currently lean toward {text}, but I am not certain."
        if state.stance == EpistemicStance.DISBELIEVED:
            return f"I currently do not believe {text}."
        return f"I do not currently have a settled belief about {text}."

    def to_dict(self) -> dict:
        return {
            "schema": EPISTEMIC_LEDGER_SCHEMA,
            "evidence": [item.to_dict() for item in self.evidence.values()],
            "propositions": [item.to_dict() for item in self.propositions.values()],
            "revisions": [item.to_dict() for item in self.revisions],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "EpistemicLedger":
        ledger = cls()
        for raw in data.get("evidence", ()):
            ledger.record_evidence(EpistemicEvidence.from_dict(raw))
        for raw in data.get("propositions", ()):
            proposition = EpistemicProposition.from_dict(raw)
            ledger.propositions[proposition.proposition_key] = proposition
        for raw in data.get("revisions", ()):
            ledger.revisions.append(EpistemicRevision(
                proposition_key=str(raw["proposition_key"]),
                before_stance=EpistemicStance(raw["before_stance"]),
                after_stance=EpistemicStance(raw["after_stance"]),
                before_confidence=float(raw["before_confidence"]),
                after_confidence=float(raw["after_confidence"]),
                evidence_refs=tuple(str(value) for value in raw.get("evidence_refs", ())),
                revised_at=float(raw["revised_at"]),
                source=str(raw.get("source", "")),
                reason=str(raw.get("reason", "")),
            ))
        return ledger
