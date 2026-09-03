"""Candidate-level semantic filtering for Project Ensemble.

Ensemble generates several noncanonical performances of one already-resolved
character moment. This module reuses the production ``ConsistencyLayer`` to
remove candidates that contradict higher-authority subject state *before* soft
surface ranking. It does not introduce an LLM judge or a second semantic
planner.

The final engine validation remains authoritative and still evaluates the
selected utterance before exposure. Candidate prevalidation can either use the
portable authority reconstructed from ``ExpressionRequest`` or a live
engine-authority evaluator supplied by the host. The latter is preferred for
normal CharacterAgent integration because it can inspect the exact current
World Authority and deception ledger rather than a renderer-side approximation.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Callable, Iterable

from .consistency import ConsistencyLayer
from .ensemble_realization import RealizationCandidate
from .renderer import OutputValidator
from .renderer_contract import ValidationAction, ValidationRequest, ValidationResult


ENSEMBLE_PREVALIDATION_VERSION = "ensemble-candidate-prevalidation-v2"
CandidateEvaluator = Callable[[str, object], ValidationResult]


@dataclass(frozen=True)
class CandidateValidationRecord:
    candidate: RealizationCandidate
    result: ValidationResult
    accepted: bool


@dataclass(frozen=True)
class CandidateValidationBatch:
    survivors: tuple[RealizationCandidate, ...]
    records: tuple[CandidateValidationRecord, ...]

    @property
    def rejected(self) -> tuple[CandidateValidationRecord, ...]:
        return tuple(record for record in self.records if not record.accepted)


def _identity_constraints(request) -> tuple[str, ...]:
    digest = request.ledger_digest if isinstance(request.ledger_digest, dict) else {}
    authored = digest.get("authored_identity", {}) if isinstance(digest, dict) else {}
    if not isinstance(authored, dict):
        return ()
    values = authored.get("forbidden_self_claims", ())
    if not isinstance(values, (list, tuple, set)):
        return ()
    return tuple(str(value) for value in values if str(value).strip())


def _interpretive_state(request) -> tuple[dict, ...]:
    beliefs: list[dict] = []
    for item in list(request.evidence or []):
        if not isinstance(item, dict) or item.get("type") != "interpretation":
            continue
        raw = item.get("beliefs", ())
        if isinstance(raw, (list, tuple)):
            beliefs.extend(dict(value) for value in raw if isinstance(value, dict))
    return tuple(beliefs)


def candidate_validation_request(candidate_text: str, request) -> ValidationRequest:
    resolved = request.resolved_state if isinstance(request.resolved_state, dict) else {}
    canonical_context = {
        "current_input": str(resolved.get("user_text", "")),
        "recall_contract": resolved.get("recall_contract"),
    }
    return ValidationRequest(
        candidate_text=str(candidate_text or ""),
        identity_constraints=_identity_constraints(request),
        interpretive_state=_interpretive_state(request),
        relevant_history=tuple(request.retrieved_memories or ()),
        decision_payload=dict(request.decision_payload or {}),
        canonical_context=canonical_context,
    )


def validate_candidate(
    candidate: RealizationCandidate,
    request,
    consistency: ConsistencyLayer | None = None,
    evaluator: CandidateEvaluator | None = None,
) -> CandidateValidationRecord:
    """Evaluate one candidate with deterministic higher-authority contracts.

    ``evaluator`` is the preferred engine-bound path. It receives the candidate
    text and the immutable ExpressionRequest and returns the live engine's
    ValidationResult. When no evaluator is supplied, the portable standalone
    reconstruction remains available for tools and direct renderer use.

    Soft sanitizer repairs are preserved as candidates. Hard and critical
    candidates are excluded from ranking.
    """

    if evaluator is not None:
        result = evaluator(str(candidate.text or ""), request)
    else:
        consistency = consistency or ConsistencyLayer(OutputValidator())
        result = consistency.evaluate(candidate_validation_request(candidate.text, request))
    accepted = result.action in {ValidationAction.ACCEPT, ValidationAction.SANITIZE_CONTINUE}
    return CandidateValidationRecord(candidate=candidate, result=result, accepted=accepted)


def filter_candidate_pool(
    candidates: Iterable[RealizationCandidate],
    request,
    consistency: ConsistencyLayer | None = None,
    evaluator: CandidateEvaluator | None = None,
) -> CandidateValidationBatch:
    consistency = consistency or ConsistencyLayer(OutputValidator())
    records: list[CandidateValidationRecord] = []
    survivors: list[RealizationCandidate] = []

    for candidate in candidates:
        record = validate_candidate(candidate, request, consistency, evaluator=evaluator)
        records.append(record)
        if not record.accepted:
            continue
        metadata = dict(candidate.metadata)
        metadata.update({
            "prevalidation_version": ENSEMBLE_PREVALIDATION_VERSION,
            "prevalidation_action": record.result.action.value,
            "prevalidation_issue_codes": [issue.code for issue in record.result.issues],
            "prevalidation_authority": "engine_live" if evaluator is not None else "request_reconstruction",
        })
        survivors.append(replace(
            candidate,
            text=record.result.output_text,
            metadata=metadata,
        ))

    return CandidateValidationBatch(survivors=tuple(survivors), records=tuple(records))
