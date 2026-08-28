"""Structured consistency evaluation for rendered candidate expression.

This module sits between a renderer and exposure of its text. It does not own
character state and it does not retrieve new evidence. It evaluates a candidate
against constraints supplied by higher-authority Wayfarer subsystems.
"""

from __future__ import annotations

from typing import Iterable

from .renderer_contract import (
    ValidationAction,
    ValidationIssue,
    ValidationRequest,
    ValidationResult,
    ValidationSeverity,
)


_CRITICAL_CODES = {
    "self_model_conflict",
    "world_authority_conflict",
    "canonicality_conflict",
}
_HARD_CODES = {
    "false_memory_claim",
    "unauthorized_fabrication",
    "unsupported_private_user_state",
    "deception_contradiction",
}


def _code(detail: str) -> str:
    return str(detail).split(":", 1)[0].strip() or "unknown_violation"


def severity_for_violation(detail: str) -> ValidationSeverity:
    code = _code(detail)
    if code in _CRITICAL_CODES:
        return ValidationSeverity.CRITICAL
    if code in _HARD_CODES:
        return ValidationSeverity.HARD
    return ValidationSeverity.SOFT


def action_for_issues(issues: Iterable[ValidationIssue]) -> ValidationAction:
    issues = tuple(issues)
    if not issues:
        return ValidationAction.ACCEPT
    severities = {issue.severity for issue in issues}
    if ValidationSeverity.CRITICAL in severities:
        return ValidationAction.FALLBACK_IDENTITY_ONLY
    if ValidationSeverity.HARD in severities:
        return ValidationAction.REGENERATE_CONSTRAINED
    return ValidationAction.SANITIZE_CONTINUE


class ConsistencyLayer:
    """Adapter that gives the existing validator a typed severity contract.

    ``detector`` is expected to expose the existing ``check`` and ``sanitize``
    methods. This keeps the production detector logic reusable while making the
    assembly boundary explicit and testable.
    """

    def __init__(self, detector):
        self.detector = detector

    def evaluate(self, request: ValidationRequest) -> ValidationResult:
        raw = list(self.detector.check(
            request.candidate_text,
            list(request.relevant_history),
            authorization=request.authorization,
            deception_ledger=request.deception_ledger,
            decision_payload=dict(request.decision_payload),
            forbidden_self_claims=tuple(request.identity_constraints),
        ))

        # World/canonical authority may provide explicit expressions that the
        # renderer must not assert. The consistency layer never invents these;
        # it only consumes a supplied high-authority constraint set.
        canonical_forbidden = request.canonical_context.get("forbidden_claims", ())
        lowered = request.candidate_text.lower()
        for claim in canonical_forbidden or ():
            normalized = str(claim).strip().lower()
            if normalized and normalized in lowered:
                raw.append(f"world_authority_conflict:{claim}")

        issues = tuple(
            ValidationIssue(
                code=_code(detail),
                severity=severity_for_violation(detail),
                detail=str(detail),
                authority_source=(
                    "world_authority"
                    if _code(detail) == "world_authority_conflict"
                    else "self_model"
                    if _code(detail) == "self_model_conflict"
                    else "consistency_layer"
                ),
            )
            for detail in raw
        )
        action = action_for_issues(issues)
        output_text = request.candidate_text
        if action == ValidationAction.SANITIZE_CONTINUE:
            output_text = self.detector.sanitize(
                request.candidate_text,
                forbidden_self_claims=tuple(request.identity_constraints),
            )
        return ValidationResult(
            candidate_text=request.candidate_text,
            output_text=output_text,
            issues=issues,
            action=action,
        )


def regeneration_constraints(result: ValidationResult) -> tuple[str, ...]:
    """Return concise machine-facing constraints for one bounded retry.

    This helper deliberately returns semantics, not a freeform role-play prompt.
    The engine may later pass these to a renderer's expression constraints.
    """

    if result.action != ValidationAction.REGENERATE_CONSTRAINED:
        return ()
    return tuple(f"avoid:{issue.code}" for issue in result.issues if issue.severity == ValidationSeverity.HARD)
