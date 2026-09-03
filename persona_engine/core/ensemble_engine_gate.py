"""Live engine-authority validation for Ensemble candidate admission.

The renderer is allowed to propose expressive possibilities. It is not allowed
to decide which possibilities are semantically compatible with the continuing
subject. This adapter evaluates each candidate with the InteriorEngine's actual
ConsistencyLayer and current authority state.

It deliberately does not generate, rank, or select candidates. It only answers:
"may this candidate enter the expression competition?"
"""

from __future__ import annotations

from .renderer_contract import ValidationRequest, ValidationResult


ENGINE_CANDIDATE_GATE_VERSION = "ensemble-engine-candidate-gate-v1"


def _interpretive_state(request) -> tuple[dict, ...]:
    beliefs: list[dict] = []
    for item in list(getattr(request, "evidence", ()) or ()):
        if not isinstance(item, dict) or item.get("type") != "interpretation":
            continue
        raw = item.get("beliefs", ())
        if isinstance(raw, (list, tuple)):
            beliefs.extend(dict(value) for value in raw if isinstance(value, dict))
    return tuple(beliefs)


class EngineAuthorityCandidateGate:
    """Callable candidate gate bound to one live InteriorEngine instance."""

    version = ENGINE_CANDIDATE_GATE_VERSION

    def __init__(self, engine):
        self.engine = engine

    def __call__(self, candidate_text: str, request) -> ValidationResult:
        resolved = request.resolved_state if isinstance(request.resolved_state, dict) else {}
        canonical_context = {
            "world": self.engine.world.to_dict(),
            "current_input": str(resolved.get("user_text", "")),
            "recall_contract": resolved.get("recall_contract"),
        }
        return self.engine.consistency.evaluate(ValidationRequest(
            candidate_text=str(candidate_text or ""),
            identity_constraints=tuple(self.engine.identity.forbidden_self_claims),
            interpretive_state=_interpretive_state(request),
            relevant_history=tuple(request.retrieved_memories or ()),
            decision_payload=dict(request.decision_payload or {}),
            canonical_context=canonical_context,
            deception_ledger=self.engine.deception_ledger,
        ))

    def status(self) -> dict:
        identity = getattr(self.engine, "identity", None)
        return {
            "version": self.version,
            "authority": "live_interior_engine",
            "subject_uuid": str(getattr(identity, "entity_uuid", "") or ""),
            "user_id": str(getattr(self.engine, "user_id", "")),
        }
