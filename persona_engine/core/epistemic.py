"""Experimental subject-owned epistemic proposition state.

This module fills a deliberately narrow gap between three existing authorities:

* canonical experience can preserve that someone told the subject a claim;
* WorldAuthority can preserve objective host/world facts;
* InterpretationEngine can produce bounded turn-local subjective readings.

None of those contracts currently owns the durable statement "given the evidence
available to me, I currently believe/doubt proposition X."  This experimental
ledger represents that current first-person epistemic stance without making
natural language, a renderer, or a model authoritative over it.

Important boundaries:

* Evidence is not truth. A testimony record means the testimony occurred.
* This ledger is not WorldAuthority and cannot create objective facts.
* This ledger does not parse free-form language or assign source reliability.
* Revisions are explicit typed operations. The caller must justify them.
* Revision records are returned to the caller rather than accumulated forever;
  a future production integration should put causal revision history in canonical
  continuity while keeping only causally sufficient current state resident.

The module is intentionally dependency-free and is not wired into the production
turn loop while the Phase D actual-model fixture remains frozen.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
from typing import Any, Iterable
import time
import uuid


class EpistemicStance(str, Enum):
    """Small categorical vocabulary for the subject's current position."""

    UNKNOWN = "unknown"
    TENTATIVE = "tentative"
    BELIEVED = "believed"
    DISBELIEVED = "disbelieved"


class EvidenceSource(str, Enum):
    """Provenance class, not an automatic reliability ranking."""

    TESTIMONY = "testimony"
    OBSERVATION = "observation"
    WORLD_AUTHORITY = "world_authority"
    MODEL_INFERENCE = "model_inference"
    SELF_INFERENCE = "self_inference"


@dataclass(frozen=True)
class EpistemicEvidence:
    """One immutable item of evidence about an atomic proposition.

    ``polarity`` says only whether the evidence supports (+1) or contradicts
    (-1) the proposition.  ``confidence`` describes confidence in this evidence
    item as supplied by an authorized semantic service.  This class deliberately
    does not calculate trust from source type.
    """

    evidence_id: str
    proposition_key: str
    proposition_text: str
    polarity: int
    source_class: str
    source_ref: str
    observed_at: float
    confidence: float = 1.0
    claim_valid_from: float | None = None
    claim_valid_until: float | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class EpistemicProposition:
    """Current subject-owned stance toward one proposition."""

    proposition_key: str
    proposition_text: str
    stance: str
    confidence: float
    evidence_ids: tuple[str, ...]
    updated_at: float
    revision_source: str

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["evidence_ids"] = list(self.evidence_ids)
        return data


@dataclass(frozen=True)
class EpistemicRevision:
    """Causal revision certificate returned for continuity/debug logging."""

    proposition_key: str
    before_stance: str
    before_confidence: float
    after_stance: str
    after_confidence: float
    evidence_ids: tuple[str, ...]
    revised_at: float
    revision_source: str
    reason: str

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["evidence_ids"] = list(self.evidence_ids)
        return data


class EpistemicLedger:
    """Compact current epistemic state plus immutable evidence records.

    This experimental class stores evidence locally so its semantics can be
    tested in isolation.  A production low-resource integration should be free
    to reconstruct cold evidence from canonical continuity and retain only the
    active evidence references required by current propositions.
    """

    def __init__(
        self,
        evidence: Iterable[EpistemicEvidence] | None = None,
        propositions: Iterable[EpistemicProposition] | None = None,
    ) -> None:
        self.evidence: dict[str, EpistemicEvidence] = {}
        self.propositions: dict[str, EpistemicProposition] = {}
        for item in evidence or ():
            self._validate_evidence(item)
            if item.evidence_id in self.evidence:
                raise ValueError(f"duplicate epistemic evidence id: {item.evidence_id}")
            self.evidence[item.evidence_id] = item
        for proposition in propositions or ():
            self._validate_proposition_state(proposition)
            self.propositions[proposition.proposition_key] = proposition

    @staticmethod
    def _clean_key(value: str) -> str:
        key = " ".join(str(value or "").strip().split())
        if not key:
            raise ValueError("proposition_key must not be empty")
        return key

    @staticmethod
    def _clean_text(value: str) -> str:
        text = " ".join(str(value or "").strip().split())
        if not text:
            raise ValueError("proposition_text must not be empty")
        return text

    @staticmethod
    def _validate_evidence(item: EpistemicEvidence) -> None:
        if not str(item.evidence_id or "").strip():
            raise ValueError("evidence_id must not be empty")
        EpistemicLedger._clean_key(item.proposition_key)
        EpistemicLedger._clean_text(item.proposition_text)
        if int(item.polarity) not in {-1, 1}:
            raise ValueError("evidence polarity must be -1 or 1")
        try:
            EvidenceSource(str(item.source_class))
        except ValueError as exc:
            raise ValueError(f"unsupported evidence source class: {item.source_class}") from exc
        if not str(item.source_ref or "").strip():
            raise ValueError("source_ref must not be empty")
        if not 0.0 <= float(item.confidence) <= 1.0:
            raise ValueError("evidence confidence must be between 0 and 1")
        if item.claim_valid_from is not None and item.claim_valid_until is not None:
            if float(item.claim_valid_until) < float(item.claim_valid_from):
                raise ValueError("claim_valid_until must not precede claim_valid_from")

    def _validate_proposition_state(self, proposition: EpistemicProposition) -> None:
        key = self._clean_key(proposition.proposition_key)
        self._clean_text(proposition.proposition_text)
        try:
            stance = EpistemicStance(str(proposition.stance))
        except ValueError as exc:
            raise ValueError(f"unsupported epistemic stance: {proposition.stance}") from exc
        if not 0.0 <= float(proposition.confidence) <= 1.0:
            raise ValueError("proposition confidence must be between 0 and 1")
        if stance is EpistemicStance.UNKNOWN and proposition.confidence != 0.0:
            raise ValueError("unknown stance must have zero confidence")
        for evidence_id in proposition.evidence_ids:
            item = self.evidence.get(str(evidence_id))
            if item is None:
                raise ValueError(f"unknown evidence reference: {evidence_id}")
            if item.proposition_key != key:
                raise ValueError("proposition cannot cite evidence for another key")

    def record_evidence(
        self,
        proposition_key: str,
        proposition_text: str,
        *,
        polarity: int,
        source_class: EvidenceSource | str,
        source_ref: str,
        observed_at: float | None = None,
        confidence: float = 1.0,
        claim_valid_from: float | None = None,
        claim_valid_until: float | None = None,
        evidence_id: str | None = None,
    ) -> EpistemicEvidence:
        """Record evidence without silently changing what the subject believes."""

        key = self._clean_key(proposition_key)
        text = self._clean_text(proposition_text)
        source_value = source_class.value if isinstance(source_class, EvidenceSource) else str(source_class)
        item = EpistemicEvidence(
            evidence_id=str(evidence_id or f"evidence_{uuid.uuid4().hex}"),
            proposition_key=key,
            proposition_text=text,
            polarity=int(polarity),
            source_class=source_value,
            source_ref=str(source_ref or "").strip(),
            observed_at=float(time.time() if observed_at is None else observed_at),
            confidence=float(confidence),
            claim_valid_from=None if claim_valid_from is None else float(claim_valid_from),
            claim_valid_until=None if claim_valid_until is None else float(claim_valid_until),
        )
        self._validate_evidence(item)
        if item.evidence_id in self.evidence:
            raise ValueError(f"duplicate epistemic evidence id: {item.evidence_id}")
        self.evidence[item.evidence_id] = item
        return item

    def revise(
        self,
        proposition_key: str,
        proposition_text: str,
        *,
        stance: EpistemicStance | str,
        confidence: float,
        evidence_ids: Iterable[str] = (),
        revision_source: str,
        reason: str,
        revised_at: float | None = None,
    ) -> EpistemicRevision:
        """Explicitly revise current stance and return the causal certificate.

        The ledger verifies references but intentionally does not infer a stance
        from testimony, relationship trust, model output, or evidence count.
        That policy requires a separate experiment and authority decision.
        """

        key = self._clean_key(proposition_key)
        text = self._clean_text(proposition_text)
        stance_value = stance.value if isinstance(stance, EpistemicStance) else str(stance)
        try:
            stance_enum = EpistemicStance(stance_value)
        except ValueError as exc:
            raise ValueError(f"unsupported epistemic stance: {stance_value}") from exc
        confidence_value = float(confidence)
        if not 0.0 <= confidence_value <= 1.0:
            raise ValueError("proposition confidence must be between 0 and 1")
        if stance_enum is EpistemicStance.UNKNOWN:
            confidence_value = 0.0

        refs = tuple(dict.fromkeys(str(item) for item in evidence_ids))
        for evidence_id in refs:
            evidence = self.evidence.get(evidence_id)
            if evidence is None:
                raise ValueError(f"unknown evidence reference: {evidence_id}")
            if evidence.proposition_key != key:
                raise ValueError("proposition cannot cite evidence for another key")
        if stance_enum is not EpistemicStance.UNKNOWN and not refs:
            raise ValueError("settled/tentative stance requires at least one evidence reference")

        prior = self.propositions.get(key)
        before_stance = prior.stance if prior is not None else EpistemicStance.UNKNOWN.value
        before_confidence = float(prior.confidence) if prior is not None else 0.0
        when = float(time.time() if revised_at is None else revised_at)
        source = " ".join(str(revision_source or "").strip().split())
        if not source:
            raise ValueError("revision_source must not be empty")

        state = EpistemicProposition(
            proposition_key=key,
            proposition_text=text,
            stance=stance_enum.value,
            confidence=confidence_value,
            evidence_ids=refs,
            updated_at=when,
            revision_source=source,
        )
        self._validate_proposition_state(state)
        self.propositions[key] = state
        return EpistemicRevision(
            proposition_key=key,
            before_stance=before_stance,
            before_confidence=before_confidence,
            after_stance=state.stance,
            after_confidence=state.confidence,
            evidence_ids=refs,
            revised_at=when,
            revision_source=source,
            reason=" ".join(str(reason or "").strip().split()),
        )

    def current(self, proposition_key: str) -> EpistemicProposition | None:
        return self.propositions.get(self._clean_key(proposition_key))

    def evidence_for(self, proposition_key: str) -> tuple[EpistemicEvidence, ...]:
        key = self._clean_key(proposition_key)
        return tuple(
            sorted(
                (item for item in self.evidence.values() if item.proposition_key == key),
                key=lambda item: (item.observed_at, item.evidence_id),
            )
        )

    def first_person_status(self, proposition_key: str) -> str:
        """Deterministic first-person projection of typed state.

        This is an internal/debug projection only.  A future renderer boundary
        must still apply disclosure and least-privilege filtering before using it.
        """

        state = self.current(proposition_key)
        if state is None or state.stance == EpistemicStance.UNKNOWN.value:
            text = state.proposition_text if state is not None else self._clean_key(proposition_key)
            return f"I do not currently have a settled belief about {text}."
        if state.stance == EpistemicStance.TENTATIVE.value:
            return f"I currently lean toward {state.proposition_text}, but I am not certain."
        if state.stance == EpistemicStance.BELIEVED.value:
            return f"I currently believe {state.proposition_text}."
        return f"I currently do not believe {state.proposition_text}."

    def to_state(self) -> dict[str, Any]:
        return {
            "schema_version": "epistemic-ledger-experimental-v1",
            "evidence": [item.to_dict() for item in sorted(self.evidence.values(), key=lambda item: item.evidence_id)],
            "propositions": [
                item.to_dict()
                for item in sorted(self.propositions.values(), key=lambda item: item.proposition_key)
            ],
        }

    @classmethod
    def from_state(cls, state: dict[str, Any] | None) -> "EpistemicLedger":
        if not state:
            return cls()
        version = str(state.get("schema_version", ""))
        if version and version != "epistemic-ledger-experimental-v1":
            raise ValueError(f"unsupported epistemic ledger schema: {version}")
        evidence = [EpistemicEvidence(**item) for item in state.get("evidence", [])]
        propositions = [
            EpistemicProposition(
                proposition_key=item["proposition_key"],
                proposition_text=item["proposition_text"],
                stance=item["stance"],
                confidence=float(item["confidence"]),
                evidence_ids=tuple(item.get("evidence_ids", [])),
                updated_at=float(item["updated_at"]),
                revision_source=item["revision_source"],
            )
            for item in state.get("propositions", [])
        ]
        return cls(evidence=evidence, propositions=propositions)
