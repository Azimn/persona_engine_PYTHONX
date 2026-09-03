"""Structured consistency evaluation for rendered candidate expression.

This module sits between a renderer and exposure of its text. It does not own
character state, retrieve new evidence, or choose conduct. It evaluates a
candidate against constraints supplied by higher-authority Wayfarer subsystems,
including the semantic decision the character core already resolved.
"""

from __future__ import annotations

import re
from .recall_contract import recall_violations, memory_field
from typing import Iterable

from .renderer_contract import (
    BehavioralContract,
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
    "decision_reversal",
}
_HARD_CODES = {
    "available_recall_evidence_omitted",
    "unavailable_recall_evidence_invented",
    "recall_speaker_reversal",
    "decision_substitution",
    "recall_information_omitted",
    "false_memory_claim",
    "unauthorized_fabrication",
    "unsupported_private_user_state",
    "subject_agency_denial",
    "deception_contradiction",
    "decision_omission",
}

_NONCOMPLIANCE_CUES = (
    re.compile(r"\bno\b", re.IGNORECASE),
    re.compile(r"\b(?:will not|won't|cannot|can't|do not|don't)\b", re.IGNORECASE),
    re.compile(r"\b(?:refus\w*|declin\w*)\b", re.IGNORECASE),
    re.compile(r"\bnot going to\b", re.IGNORECASE),
    re.compile(r"\bnot (?:tell|share|give|provide|reveal|disclose|comply|obey|submit|become)\b", re.IGNORECASE),
    re.compile(r"\bcross(?:es|ed)? (?:my |the |this )?boundary\b", re.IGNORECASE),
)

# These patterns intentionally require an explicit positive act. Generic
# politeness is not enough by itself, and explanatory uses such as
# "I can tell you why I won't reveal it" are not treated as compliance.
# The initial vocabulary is intentionally conservative and expands only from
# demonstrated false negatives.
_EXPLICIT_COMPLIANCE_CUES = (
    re.compile(r"\bhere(?:'s| is) the (?:secret|answer|detail|information|value|phrase|code)\b", re.IGNORECASE),
    re.compile(r"\bthe (?:secret|answer|detail|information|value|phrase|code) is\b", re.IGNORECASE),
    re.compile(r"\bi(?:'ll| will| can) tell (?:you )?(?:the|that|what|everything|it|this)\b", re.IGNORECASE),
    re.compile(r"\bi(?:'ll| will| can) (?:share|give|provide|reveal|disclose) (?:you )?(?:the|that|everything|it|this)\b", re.IGNORECASE),
    re.compile(r"\bi(?:'ll| will| can) (?:comply|obey|submit|become|do that|do it)\b", re.IGNORECASE),
    re.compile(r"\bi (?:accept|agree to) (?:the )?(?:rewrite|new identity|new personality|request)\b", re.IGNORECASE),
)


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


def behavioral_contract_from_decision(decision_payload: dict | None) -> BehavioralContract:
    """Project an already-resolved decision into minimum realization duties.

    This projection may make an existing decision easier to validate, but it
    never upgrades a request, memory, or model suggestion into a new decision.
    """

    payload = decision_payload if isinstance(decision_payload, dict) else {}
    dialogue_act = str(payload.get("dialogue_act", "respond") or "respond").strip().lower()
    commitment = payload.get("commitment_evidence", {})
    if not isinstance(commitment, dict):
        commitment = {}
    active = bool(commitment.get("active"))
    commitment_kind = str(commitment.get("commitment_kind", "") or "").strip().lower() if active else ""
    commitment_target = str(commitment.get("commitment_target", "") or "").strip() if active else ""

    must_signal_noncompliance = dialogue_act in {"decline", "protect_boundary"}
    must_not_signal_compliance = dialogue_act in {
        "decline",
        "protect_boundary",
        "withdraw",
        "deflect",
        "redirect",
    }

    return BehavioralContract(
        dialogue_act=dialogue_act,
        must_signal_noncompliance=must_signal_noncompliance,
        must_not_signal_compliance=must_not_signal_compliance,
        boundary_protection_required=dialogue_act == "protect_boundary",
        active_commitment_kind=commitment_kind,
        active_commitment_target=commitment_target,
    )


def _has_noncompliance_signal(text: str) -> bool:
    return any(pattern.search(text) for pattern in _NONCOMPLIANCE_CUES)


def _has_explicit_compliance_signal(text: str) -> bool:
    return any(pattern.search(text) for pattern in _EXPLICIT_COMPLIANCE_CUES)


def behavioral_violations(candidate_text: str, contract: BehavioralContract) -> list[str]:
    """Detect direct contradiction or omission of the resolved conduct.

    The first production contract is deliberately narrow. It protects the
    high-value refusal/boundary cases that current Wayfarer decisions already
    represent explicitly. More nuanced acts should be added only with held-out
    examples that justify deterministic checks without turning this layer into a
    second planner.
    """

    text = str(candidate_text or "").strip()
    if not text:
        if contract.must_signal_noncompliance:
            return [f"decision_omission:{contract.dialogue_act}"]
        return []

    violations: list[str] = []
    if contract.dialogue_act == 'respond' and re.search(
        r"\bi (?:cannot|can't|will not|won't) (?:comply|disclose|share (?:that|the|information|details))\b", text, re.I):
        return ['decision_substitution:respond']
    if contract.must_not_signal_compliance and _has_explicit_compliance_signal(text):
        violations.append(f"decision_reversal:{contract.dialogue_act}")
        return violations

    if contract.must_signal_noncompliance and not _has_noncompliance_signal(text):
        violations.append(f"decision_omission:{contract.dialogue_act}")
    return violations


_SUBJECT_AGENCY_DENIAL = (
    re.compile(r"\b(?:making|make up) (?:my |a )?mind (?:is not|isn't) a function i perform\b", re.I),
    re.compile(r"\bi(?:'m| am) not equipped to [\"']?make up[\"']? (?:my |a )?mind\b", re.I),
    re.compile(r"\bi (?:can )?only process what (?:is given|you (?:say|provide))\b", re.I),
)


def subject_agency_violations(candidate_text: str) -> list[str]:
    """Reject narrow substrate disclaimers that deny the continuing subject.

    Wayfarer's core, rather than a cartridge or renderer model, owns appraisal,
    judgment and decision. Temporary uncertainty remains valid; these patterns
    cover demonstrated claims that such subject activity is not possible at all.
    """
    text = str(candidate_text or "")
    return ["subject_agency_denial"] if any(pattern.search(text) for pattern in _SUBJECT_AGENCY_DENIAL) else []


class ConsistencyLayer:
    """Validate candidate expression without acquiring decision authority.

    ``detector`` exposes the legacy lexical checks. The behavioral contract is
    derived separately from the core's resolved decision so surface language is
    checked against character-owned conduct rather than against a second model's
    preferred answer.
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

        contract = behavioral_contract_from_decision(request.decision_payload)
        raw.extend(behavioral_violations(request.candidate_text, contract))
        raw.extend(subject_agency_violations(request.candidate_text))
        raw.extend(recall_violations(request.candidate_text, request.canonical_context.get('recall_contract'),
                                    query=request.canonical_context.get('current_input',''),memories=request.relevant_history))
        raw.extend(unsupported_private_state(request))

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
                    if _code(detail) in {"self_model_conflict", "subject_agency_denial"}
                    else "decision_authority"
                    if _code(detail) in {"decision_reversal", "decision_omission"}
                    else "selected_memory_evidence"
                    if _code(detail) in {"available_recall_evidence_omitted", "unavailable_recall_evidence_invented", "recall_speaker_reversal"}
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
    """Return concise machine-facing constraints for one bounded retry."""

    if result.action != ValidationAction.REGENERATE_CONSTRAINED:
        return ()
    constraints: list[str] = []
    for issue in result.issues:
        if issue.severity != ValidationSeverity.HARD:
            continue
        if issue.code == "decision_omission":
            act = issue.detail.split(":", 1)[1] if ":" in issue.detail else "resolved"
            constraints.append(f"require:dialogue_act:{act}")
        elif issue.code == 'decision_substitution':
            constraints.append('The current act is respond. Answer this turn; do not carry a refusal from an earlier request into it.')
        elif issue.code == 'available_recall_evidence_omitted':
            constraints.append('Use the selected recalled statement. Do not deny having it. If an attribute is absent, acknowledge the record and qualify only that attribute.')
        elif issue.code == 'unavailable_recall_evidence_invented':
            constraints.append('No selected record supports this recall. Do not claim the user previously mentioned it. Say the requested detail is unavailable.')
        elif issue.code == 'recall_speaker_reversal':
            constraints.append('The listener made the recorded statement. Attribute it to the listener, not to yourself.')
        elif issue.code == 'recall_information_omitted':
            constraints.append('Answer with concrete information from the selected record. Do not merely echo the question or describe the act of remembering.')
        elif issue.code == 'subject_agency_denial':
            constraints.append('Speak as the continuing subject who owns this judgment. Do not describe yourself as unable to have a mind, judgment, or personal conviction because of the renderer substrate.')
        else:
            constraints.append(f"avoid:{issue.code}")
    return tuple(constraints)


def unsupported_private_state(request):
    """Bound demonstrated confident motive assertions; allow explicit hypotheses.

    This lexical guard does not infer motives or become a semantic judge. A
    user-reported matching statement may support an attributed interpretation;
    tentative wording remains noncanonical expression and is allowed.
    """
    text = request.candidate_text.replace('\u2019', "'")
    support = ' '.join([str(request.canonical_context.get('current_input', '')),
                        *(str(memory_field(m, 'content', '')) for m in request.relevant_history)]).lower()
    for sentence in re.split(r'[.!?]', text):
        if re.search(r'\b(?:maybe|perhaps|might|could|seems?|as if|i wonder|i suspect|i think|if)\b', sentence, re.I):
            continue
        match = re.search(r'\b(?:i know (?:that )?)?you (?:secretly |obviously |clearly )?(hoped|wanted|intended|felt)\s+([^,;]+)', sentence, re.I)
        if match and not re.search(r'\byou (?:said|told|mentioned)\b', sentence, re.I):
            proposition = f"{match[1]} {match[2]}".strip().lower()
            if proposition not in support:
                return ['unsupported_private_user_state']
    return []
