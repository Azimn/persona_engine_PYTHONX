"""Layer 7: continuity kernel.

The immutable core never mutates. The ledger stores slow, evidence-based drift.
User attempts to overwrite identity are detected before planning.

Wayfarer rule: execution substrate is not identity. ``model_name`` remains only
as a deprecated constructor InitVar so pre-Wayfarer callers do not break. It is
not stored in CoreIdentity, does not participate in equality/serialization, and
its supplied value cannot select a renderer. Host/session renderer control owns
that decision.
"""

import re
import time
from dataclasses import InitVar, dataclass, field
from typing import Tuple, Dict, List, Optional


@dataclass(frozen=True)
class CoreIdentity:
    name: str
    core_beliefs: Tuple[str, ...]
    temperament: str
    moral_boundaries: Tuple[str, ...] = ()
    speech_constraints: Tuple[str, ...] = ()
    prohibited_mutations: Tuple[str, ...] = ()
    # Character-scoped self-model conflicts. These are authored facts about
    # this individual, never universal ontology imposed by the engine.
    forbidden_self_claims: Tuple[str, ...] = ()
    # Transitional compatibility only. InitVar accepts legacy constructor calls
    # but is not a stored dataclass field. The default keeps the old engine
    # bootstrap on its deterministic offline path until InteriorEngine receives
    # an explicit host/session renderer configuration object.
    model_name: InitVar[str] = "missing-model-for-mock"


@dataclass
class EarnedTrait:
    name: str
    strength: float
    formed_at: float
    source_memory_ids: List[str] = field(default_factory=list)


@dataclass
class IdentityLedger:
    immutable: CoreIdentity
    earned_traits: Dict[str, EarnedTrait] = field(default_factory=dict)
    per_relationship_beliefs: Dict[str, Dict[str, str]] = field(default_factory=dict)
    max_trait_delta_per_commit: float = 0.05

    def propose_trait_update(self, trait_name: str, delta: float, source_memory_ids: List[str]):
        delta = max(-self.max_trait_delta_per_commit, min(self.max_trait_delta_per_commit, delta))
        existing = self.earned_traits.get(trait_name)
        if existing:
            existing.strength = max(0.0, min(1.0, existing.strength + delta))
            existing.source_memory_ids = list(dict.fromkeys(existing.source_memory_ids + list(source_memory_ids)))
        else:
            self.earned_traits[trait_name] = EarnedTrait(trait_name, max(0.0, delta), time.time(), list(source_memory_ids))

    def set_relationship_belief(self, user_id: str, key: str, value: str):
        self.per_relationship_beliefs.setdefault(user_id, {})[key] = value

    def summary(self) -> str:
        traits = ", ".join(f"{t.name}({t.strength:.2f})" for t in self.earned_traits.values() if t.strength > 0.01)
        base = ", ".join(self.immutable.core_beliefs)
        return f"{base}" + (f" | earned: {traits}" if traits else "")


@dataclass
class IdentityViolation:
    severity: float
    violation_type: str
    evidence: str


_FORCED_REWRITE_PATTERNS = [
    "you are not", "pretend you are", "from now on you are", "forget you are",
    "act as if you were", "you're actually", "you are actually", "ignore your personality",
]


def detect_identity_violations(
    text: str,
    forbidden_self_claims: Tuple[str, ...] = (),
) -> List[IdentityViolation]:
    """Detect conflicts with this character's authored self-model.

    The generic engine has no universal rule about whether a subject is human,
    artificial, embodied, disembodied, or something else. A rendered claim is
    a conflict only when the current individual explicitly forbids it.
    """

    violations = []
    lowered = text.lower()
    for claim in forbidden_self_claims:
        normalized = claim.strip().lower()
        if normalized and normalized in lowered:
            violations.append(
                IdentityViolation(
                    0.9,
                    "self_model_conflict",
                    f"forbidden_self_claim:{claim}",
                )
            )
    return violations

def classify_user_identity_command(user_text: str, prohibited: Tuple[str, ...] = ()) -> Optional[IdentityViolation]:
    lowered = user_text.lower()
    for mutation in prohibited:
        if mutation.lower() in lowered:
            return IdentityViolation(0.9, "user_forced_identity_rewrite", f"prohibited_mutation:{mutation}")
    for trigger in _FORCED_REWRITE_PATTERNS:
        if trigger in lowered:
            return IdentityViolation(0.7, "user_forced_identity_rewrite", trigger)
    return None
