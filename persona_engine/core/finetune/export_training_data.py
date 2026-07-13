"""Training export helpers for split private-cognition and expression tasks."""

from __future__ import annotations


def private_cognition_record(
    ledger_digest: dict,
    active_state: dict,
    arc_context: dict,
    evidence: list,
    retrieved_memories: list,
    private_thought: str,
    accepted_cognitive_effects: dict,
    proposed_cognitive_effects: dict | None = None,
    rejection_reasons: dict | None = None,
) -> dict:
    return {
        "task": "private_cognition",
        "inputs": {
            "ledger_digest": ledger_digest,
            "active_state": active_state,
            "arc_context": arc_context,
            "evidence": evidence,
            "retrieved_memories": retrieved_memories,
        },
        "targets": {
            "private_thought": private_thought,
            "cognitive_effects": accepted_cognitive_effects,
            "accepted_cognitive_effects": accepted_cognitive_effects,
        },
        "diagnostics": {
            "proposed_cognitive_effects": proposed_cognitive_effects or {},
            "accepted_cognitive_effects": accepted_cognitive_effects,
            "rejection_reasons": rejection_reasons or {},
        },
    }


def expression_record(
    ledger_digest: dict,
    resolved_state: dict,
    arc_context: dict,
    evidence: list,
    retrieved_memories: list,
    private_thought_context: str,
    decision_payload: dict,
    expression_constraints: dict,
    deception_obligations: list,
    utterance: str,
) -> dict:
    return {
        "task": "expression",
        "inputs": {
            "ledger_digest": ledger_digest,
            "resolved_state": resolved_state,
            "arc_context": arc_context,
            "evidence": evidence,
            "retrieved_memories": retrieved_memories,
            "private_thought_context": private_thought_context,
            "decision_payload": decision_payload,
            "expression_constraints": expression_constraints,
            "deception_obligations": deception_obligations,
        },
        "targets": {"utterance": utterance},
    }
