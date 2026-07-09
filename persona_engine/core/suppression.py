"""Mask-suppression observability vocabulary.

This module does not decide character behavior. It only names which existing
guardrail gate acted during a turn so tests, simulators, and human reports can
trace resistance and fact-leakage outcomes.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


ALLOWED_SUPPRESSION_GATES = {
    "identity_guard",
    "expression_envelope",
    "resistance_selector",
    "workspace_forbidden_claims",
    "output_validator",
    "renderer_sanitizer",
    "memory_firewall",
    "human_testing",
}

ALLOWED_SUPPRESSION_ACTIONS = {
    "allowed",
    "constrained",
    "blocked",
    "sanitized",
    "logged_only",
}


@dataclass(frozen=True)
class SuppressionTrace:
    gate: str
    action: str
    reason: str
    severity: str = "info"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
