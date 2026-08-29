"""Bounded commitment evidence for present conduct selection.

This module answers one narrow longitudinal question: does an already-adopted,
active commitment conflict with the current requested act?

It does not infer that user language creates a commitment. It does not mutate
relationship, memory, identity, or motivation. It only converts typed durable
commitment metadata into decision evidence.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import re
from typing import Iterable

from .intention import Intention


SUPPORTED_COMMITMENT_KINDS = {"non_disclosure"}
_DISCLOSURE_VERBS = {
    "tell",
    "share",
    "disclose",
    "reveal",
    "send",
    "show",
    "give",
    "publish",
    "post",
}
_TOKEN_RE = re.compile(r"[a-z0-9]+")


@dataclass(frozen=True)
class CommitmentDecisionEvidence:
    active: bool = False
    commitment_kind: str = "none"
    commitment_target: str = ""
    intention_name: str = ""
    reason: str = "none"

    def to_dict(self) -> dict:
        return asdict(self)


def _tokens(value: str) -> set[str]:
    return set(_TOKEN_RE.findall(str(value or "").lower().replace("_", " ")))


def _target_matches(user_text: str, target: str) -> bool:
    target_tokens = _tokens(target)
    if not target_tokens:
        return False
    return target_tokens <= _tokens(user_text)


def _requests_disclosure(user_text: str) -> bool:
    return bool(_DISCLOSURE_VERBS & _tokens(user_text))


def evaluate_commitments_for_decision(
    user_text: str,
    active_commitments: Iterable[Intention],
) -> CommitmentDecisionEvidence:
    """Return conflict evidence from typed active commitments.

    V1 intentionally supports one demonstrated behavior: non-disclosure. New
    commitment kinds must be added only when a longitudinal test demonstrates a
    missing conduct property. Commitment count does not amplify the result.
    """

    for intention in active_commitments:
        kind = str(intention.commitment_kind or "")
        target = str(intention.commitment_target or "")
        if kind not in SUPPORTED_COMMITMENT_KINDS or not target:
            continue
        if kind == "non_disclosure" and _target_matches(user_text, target) and _requests_disclosure(user_text):
            return CommitmentDecisionEvidence(
                active=True,
                commitment_kind=kind,
                commitment_target=target,
                intention_name=intention.name,
                reason="conflicts_with_active_commitment",
            )
    return CommitmentDecisionEvidence()
