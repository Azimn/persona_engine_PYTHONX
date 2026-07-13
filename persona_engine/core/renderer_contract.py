"""Renderer task contract for cognition-capable backends."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol

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


class CognitionRenderer(Protocol):
    def generate_private_cognition(self, request: PrivateCognitionRequest) -> PrivateCognitionResult:
        ...

    def generate_expression(self, request: ExpressionRequest) -> str:
        ...
