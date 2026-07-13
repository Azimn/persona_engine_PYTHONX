"""Scoped deception ledger.

This ledger records structured claims and authorizations. It does not decide
speech on its own and does not grant blanket validator bypasses.
"""

from __future__ import annotations

from dataclasses import asdict
from typing import Any

from .cognition_schemas import DeceptionAuthorization, DeceptionClaim, NormalizedClaim


DEFAULT_SCOPE_RULES = {
    "omit": {"may_fabricate_memory": False},
    "minimize": {"may_fabricate_memory": False},
    "misdirect": {"may_fabricate_memory": False},
    "selective_truth": {"may_fabricate_memory": False},
    "active_lie": {"may_fabricate_memory": True},
}


class DeceptionLedger:
    def __init__(self, claims: list[DeceptionClaim] | None = None):
        self.claims: list[DeceptionClaim] = list(claims or [])

    def record(self, claim: DeceptionClaim):
        self.claims = [existing for existing in self.claims if existing.claim_id != claim.claim_id]
        self.claims.append(claim)

    def claims_for(self, audience: str, topic: str) -> list[DeceptionClaim]:
        return [
            claim for claim in self.claims
            if claim.audience == audience and claim.topic == topic and claim.status == "active"
        ]

    def authorize(
        self,
        mode: str,
        audience: str,
        topic: str,
        scope: list[str],
        may_fabricate_memory: bool = False,
    ) -> DeceptionAuthorization:
        rule = DEFAULT_SCOPE_RULES.get(mode, {"may_fabricate_memory": False})
        return DeceptionAuthorization(
            mode=mode,
            audience=audience,
            topic=topic,
            permitted_claim_scope=[str(item) for item in scope],
            may_fabricate_memory=bool(may_fabricate_memory and rule["may_fabricate_memory"]),
        )

    def to_state(self) -> list[dict[str, Any]]:
        return [asdict(claim) for claim in self.claims]

    @classmethod
    def from_state(cls, state: list[dict[str, Any]] | None) -> "DeceptionLedger":
        claims: list[DeceptionClaim] = []
        for item in state or []:
            normalized = item.get("normalized_claim", {})
            claims.append(DeceptionClaim(
                claim_id=str(item["claim_id"]),
                audience=str(item["audience"]),
                topic=str(item["topic"]),
                mode=str(item["mode"]),
                spoken_claim=str(item["spoken_claim"]),
                normalized_claim=NormalizedClaim(**normalized),
                concealed_belief_id=item.get("concealed_belief_id"),
                concealed_memory_ids=[str(x) for x in item.get("concealed_memory_ids", [])],
                consistency_obligation=str(item.get("consistency_obligation", "")),
                created_at=float(item["created_at"]),
                status=str(item.get("status", "active")),
            ))
        return cls(claims)
