"""Research-only DUCK Platform Penalty experiment package."""

from .benchmark import run_platform_penalty
from .organization import (
    BaselinePolicy,
    DecisionContext,
    DecisionPolicyHarness,
    OrganizationResolver,
    SpecializedResolver,
    detect_semantic_cues,
)

__all__ = [
    "run_platform_penalty",
    "BaselinePolicy",
    "DecisionContext",
    "DecisionPolicyHarness",
    "OrganizationResolver",
    "SpecializedResolver",
    "detect_semantic_cues",
]
