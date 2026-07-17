"""Bounded reconsideration of existing autobiographical meaning."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json

from .lived_experience import AutobiographicalInterpretation, ReinterpretationCandidate, SubjectiveExperience


@dataclass(frozen=True)
class ReconsolidationContext:
    tick: int
    trigger_type: str
    integration_capacity: float
    perceived_capacity: float
    conflict_noticed: bool
    conflict_strength: float
    dominant_pressure: float
    relationship_shift: float = 0.0
    open_loop_resolved: bool = False
    belief_corrected: bool = False
    dream_governed: bool = False
    supporting_memory_ids: tuple[str, ...] = ()
    contradicting_memory_ids: tuple[str, ...] = ()
    supporting_world_event_ids: tuple[str, ...] = ()
    contradicting_world_event_ids: tuple[str, ...] = ()
    proposed_meaning_kind: str = "uncertain_meaning"
    proposed_meaning_code: str = "I now understand that my earlier interpretation may have been incomplete."


class AutobiographicalReconsolidator:
    MIN_REINTERPRETATION_INTERVAL = 5
    MIN_CONFLICT_STRENGTH = 0.45

    def propose(self, *, experience: SubjectiveExperience, current: AutobiographicalInterpretation,
                context: ReconsolidationContext) -> ReinterpretationCandidate | None:
        if context.trigger_type == "initial_encoding" or context.tick <= current.created_tick:
            return None
        if context.tick - current.created_tick < self.MIN_REINTERPRETATION_INTERVAL:
            return None
        if context.trigger_type == "contradictory_evidence":
            if context.conflict_strength < self.MIN_CONFLICT_STRENGTH or not context.conflict_noticed:
                return None
        if context.integration_capacity < 0.45 or context.perceived_capacity < 0.35:
            return None
        if context.dominant_pressure > 0.75 and context.trigger_type not in {"dream_consolidation", "resolved_open_loop"}:
            return None
        evidence = (*context.supporting_memory_ids, *context.contradicting_memory_ids,
                    *context.supporting_world_event_ids, *context.contradicting_world_event_ids)
        if not evidence:
            return None
        confidence = max(0.10, min(0.95,
            0.25 + 0.30 * context.integration_capacity + 0.20 * context.perceived_capacity
            + 0.20 * context.conflict_strength + 0.05 * float(context.belief_corrected)))
        candidate_id = self._stable_id(experience.experience_id, current.interpretation_id,
                                       context.tick, context.trigger_type, context.proposed_meaning_code)
        emotional_delta = 0.0
        if context.proposed_meaning_kind == "reconciled_meaning":
            emotional_delta = min(0.25, abs(current.emotional_charge) * 0.35) if current.emotional_charge < 0 else -0.05
        elif context.proposed_meaning_kind == "resentful_meaning":
            emotional_delta = -0.15
        return ReinterpretationCandidate(
            1, candidate_id, experience.experience_id, current.interpretation_id,
            context.trigger_type, context.proposed_meaning_kind, context.proposed_meaning_code,
            round(confidence, 6), context.supporting_memory_ids, context.contradicting_memory_ids,
            context.supporting_world_event_ids, context.contradicting_world_event_ids,
            round(max(0.0, min(1.0, context.conflict_strength)), 6), round(emotional_delta, 6),
            int(context.tick), tuple(dict.fromkeys((current.interpretation_id, *evidence)))[-24:],
        )

    @staticmethod
    def deferral_reason(context: ReconsolidationContext, current: AutobiographicalInterpretation) -> str:
        if context.tick - current.created_tick < AutobiographicalReconsolidator.MIN_REINTERPRETATION_INTERVAL:
            return "minimum_interval"
        if context.trigger_type == "contradictory_evidence" and not context.conflict_noticed:
            return "conflict_not_noticed"
        if context.integration_capacity < 0.45 or context.perceived_capacity < 0.35:
            return "capacity_too_low"
        if context.dominant_pressure > 0.75:
            return "pressure_too_high"
        return "insufficient_evidence"

    @staticmethod
    def _stable_id(*parts: object) -> str:
        payload = json.dumps([str(item) for item in parts], separators=(",", ":")).encode("utf-8")
        return "reinterpretation_candidate_" + hashlib.blake2b(payload, digest_size=8).hexdigest()
