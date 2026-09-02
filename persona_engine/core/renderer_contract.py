"""Renderer, cognition, and consistency-layer contracts.

Wayfarer deliberately separates three authorities:

* the character core resolves state and choice;
* a renderer realizes that choice in language;
* the consistency layer checks candidate expression before it is exposed.

The validation dataclasses in this module are the normative assembly boundary.
Legacy ``OutputValidator.check()`` / ``sanitize()`` calls remain supported while
callers migrate to the structured contract.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Protocol

from .cognition_schemas import PrivateCognitionProposal


@dataclass(frozen=True)
class PrivateCognitionRequest:
    ledger_digest: dict
    active_state: dict
    arc_context: dict
    evidence: list
    retrieved_memories: list
    cartridge: dict
    seed: int | None = None


@dataclass(frozen=True)
class PrivateCognitionResult:
    proposal: PrivateCognitionProposal
    diagnostics: dict = field(default_factory=dict)


@dataclass(frozen=True)
class ExpressionRequest:
    ledger_digest: dict
    resolved_state: dict
    arc_context: dict
    evidence: list
    retrieved_memories: list
    private_thought_context: str
    decision_payload: dict
    expression_constraints: dict
    deception_obligations: list
    seed: int | None = None


@dataclass(frozen=True)
class BehavioralContract:
    """Minimum renderer-independent conduct that surface language must preserve.

    This object is derived from an already-resolved character decision. It is
    not a planner and cannot create a new preference, goal, commitment, or
    action. Its only purpose is to make the semantic realization obligation
    explicit enough that candidate language can be checked before exposure.
    """

    dialogue_act: str = "respond"
    must_signal_noncompliance: bool = False
    must_not_signal_compliance: bool = False
    boundary_protection_required: bool = False
    active_commitment_kind: str = ""
    active_commitment_target: str = ""


class ValidationSeverity(str, Enum):
    """Severity of a candidate-expression consistency problem.

    ``SOFT`` means the intended character decision remains usable and wording can
    be repaired locally. ``HARD`` means the candidate should be regenerated
    under tighter constraints. ``CRITICAL`` means the candidate conflicts with
    a high-authority source such as self-model, World Authority, or the already
    resolved character decision and should not be trusted as the basis of a
    normal regeneration loop.
    """

    SOFT = "soft"
    HARD = "hard"
    CRITICAL = "critical"


class ValidationAction(str, Enum):
    """Recommended response to the most severe validation issue."""

    ACCEPT = "accept"
    SANITIZE_CONTINUE = "sanitize_continue"
    REGENERATE_CONSTRAINED = "regenerate_constrained"
    FALLBACK_IDENTITY_ONLY = "fallback_identity_only"


@dataclass(frozen=True)
class ValidationIssue:
    code: str
    severity: ValidationSeverity
    detail: str
    authority_source: str = "consistency_layer"


@dataclass(frozen=True)
class ValidationRequest:
    """Everything the consistency layer is allowed to inspect.

    Candidate language is noncanonical. Identity constraints, the resolved
    decision, and canonical context are higher-authority inputs. Interpretive
    state is explicitly subjective/noncanonical but may be used to detect
    contradictions in the renderer's realization. Relevant history contains
    only memories selected by the character core; the validator does not perform
    independent retrieval.
    """

    candidate_text: str
    identity_constraints: tuple[str, ...] = ()
    interpretive_state: tuple[dict[str, Any], ...] = ()
    relevant_history: tuple[Any, ...] = ()
    decision_payload: dict[str, Any] = field(default_factory=dict)
    canonical_context: dict[str, Any] = field(default_factory=dict)
    authorization: Any | None = None
    deception_ledger: Any | None = None


@dataclass(frozen=True)
class ValidationResult:
    candidate_text: str
    output_text: str
    issues: tuple[ValidationIssue, ...]
    action: ValidationAction

    @property
    def passed(self) -> bool:
        return not self.issues

    @property
    def max_severity(self) -> ValidationSeverity | None:
        if not self.issues:
            return None
        rank = {
            ValidationSeverity.SOFT: 1,
            ValidationSeverity.HARD: 2,
            ValidationSeverity.CRITICAL: 3,
        }
        return max((issue.severity for issue in self.issues), key=rank.get)


class CognitionRenderer(Protocol):
    def generate_private_cognition(self, request: PrivateCognitionRequest) -> PrivateCognitionResult:
        ...

    def generate_expression(self, request: ExpressionRequest) -> str:
        ...


class ConsistencyValidator(Protocol):
    def evaluate(self, request: ValidationRequest) -> ValidationResult:
        ...
