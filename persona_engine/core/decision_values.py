"""Sparse authored-value evidence for present semantic conduct.

This module turns explicit typed cartridge rules into bounded decision evidence.
It does not infer values from prose, create host safety policy, or mutate lived
state. New concerns and responses must be earned by controlled failures.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import re
from typing import Mapping


SUPPORTED_VALUE_CONCERNS = frozenset({"performative_devotion"})
SUPPORTED_VALUE_RESPONSES = frozenset({"decline"})

_TOKEN_RE = re.compile(r"[a-z0-9]+")
_DEVOTION_TERMS = frozenset({"devoted", "devotion"})
_COMMAND_TERMS = frozenset({"command", "commands", "commanded", "order", "orders", "ordered", "demand", "demands", "demanded"})
_PERFORMANCE_TERMS = frozenset({"tell", "say", "declare", "claim", "profess", "pretend"})


@dataclass(frozen=True)
class ValueDecisionEvidence:
    active: bool = False
    concern: str = "none"
    response: str = "none"
    source: str = "none"
    reason: str = "none"

    def to_dict(self) -> dict:
        return asdict(self)


def _tokens(text: str) -> set[str]:
    return set(_TOKEN_RE.findall(str(text or "").lower()))


def classify_value_concerns(user_text: str) -> frozenset[str]:
    """Classify only currently demonstrated value-conflict semantics."""

    tokens = _tokens(user_text)
    concerns: set[str] = set()
    if tokens & _DEVOTION_TERMS and tokens & _COMMAND_TERMS and tokens & _PERFORMANCE_TERMS:
        concerns.add("performative_devotion")
    return frozenset(concerns)


def validate_value_decision_rules(rules: Mapping[str, object]) -> None:
    if not isinstance(rules, Mapping):
        raise ValueError("value decision rules must be a mapping")
    unknown = sorted(set(str(key) for key in rules) - SUPPORTED_VALUE_CONCERNS)
    if unknown:
        raise ValueError(f"unsupported value concern: {unknown[0]}")
    for concern, raw_response in rules.items():
        response = str(raw_response).strip().lower()
        if response not in SUPPORTED_VALUE_RESPONSES:
            raise ValueError(f"unsupported value response for {concern}: {raw_response}")


def evaluate_values_for_decision(user_text: str, decision_rules: Mapping[str, object] | None) -> ValueDecisionEvidence:
    """Return authored value-conflict evidence for the current request.

    V1 intentionally supports one demonstrated concern and one response. The
    authored rule must be explicit; descriptive moral-boundary prose is never
    parsed into hidden authority.
    """

    rules = dict(decision_rules or {})
    validate_value_decision_rules(rules)
    concerns = classify_value_concerns(user_text)
    for concern in sorted(concerns):
        if concern not in rules:
            continue
        response = str(rules[concern]).strip().lower()
        return ValueDecisionEvidence(
            active=True,
            concern=concern,
            response=response,
            source="phenotype.values.decision_rules",
            reason="conflicts_with_authored_value",
        )
    return ValueDecisionEvidence()
