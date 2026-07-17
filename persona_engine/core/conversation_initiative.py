"""Bounded, state-grounded initiative for conversational extensions.

This module does not select an action.  It identifies at most one existing
reason the character might add something of its own after honoring the current
conversational obligation.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, replace
import hashlib
import math
from typing import Any, Mapping, Sequence


INITIATIVE_SOURCES = frozenset({
    "contextual_memory", "open_loop", "intrinsic_activity",
    "relationship_expectation", "world_change",
})
INITIATIVE_OUTCOMES = frozenset({
    "no_source_eligible", "proposal_below_threshold", "proposal_available",
    "proposal_selected", "proposal_inhibited", "proposal_denied_by_synthesis",
})
INITIATIVE_MOVES = frozenset({
    "probe", "compare", "reminisce", "speculate", "express_curiosity",
    "continue_working",
})
INITIATIVE_DIRECT_ACTION_KINDS = frozenset({"speak"})
INITIATIVE_HIGHER_GATE_ACTION_KINDS = frozenset({
    "gesture", "continue_activity", "delay", "silence", "withdraw",
})


def _clamp(value: float) -> float:
    number = float(value)
    return max(0.0, min(1.0, number)) if math.isfinite(number) else 0.0


def _stable_id(*parts: object) -> str:
    payload = "|".join(str(item) for item in parts).encode("utf-8", errors="ignore")
    return "initiative_" + hashlib.blake2b(payload, digest_size=8).hexdigest()


@dataclass(frozen=True)
class InitiativeSource:
    source_kind: str
    source_id: str
    topic_key: str
    proposed_move: str
    strength: float
    reason_codes: tuple[str, ...]

    def __post_init__(self) -> None:
        if self.source_kind not in INITIATIVE_SOURCES:
            raise ValueError(f"unsupported initiative source: {self.source_kind}")
        if self.proposed_move not in INITIATIVE_MOVES:
            raise ValueError(f"unsupported initiative move: {self.proposed_move}")
        if not 0.0 <= float(self.strength) <= 1.0:
            raise ValueError("initiative source strength must be within [0, 1]")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class InitiativeProposal:
    schema_version: int
    proposal_id: str
    actor_id: int
    turn: int
    source_kind: str
    source_id: str
    topic_key: str
    proposed_move: str
    strength: float
    reason_codes: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "InitiativeProposal":
        raw = {key: value[key] for key in cls.__dataclass_fields__ if key in value}
        raw["reason_codes"] = tuple(raw.get("reason_codes", ()))
        return cls(**raw)


@dataclass(frozen=True)
class InitiativeAssessment:
    schema_version: int
    actor_id: int
    turn: int
    threshold: float
    eligible_sources: tuple[InitiativeSource, ...]
    proposal: InitiativeProposal | None
    outcome: str
    reason_codes: tuple[str, ...]

    def __post_init__(self) -> None:
        if self.outcome not in INITIATIVE_OUTCOMES:
            raise ValueError(f"unsupported initiative outcome: {self.outcome}")

    def with_outcome(self, outcome: str, *reason_codes: str) -> "InitiativeAssessment":
        return replace(
            self,
            outcome=outcome,
            reason_codes=tuple(dict.fromkeys((*self.reason_codes, *reason_codes))),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "actor_id": self.actor_id,
            "turn": self.turn,
            "threshold": self.threshold,
            "eligible_sources": [item.to_dict() for item in self.eligible_sources],
            "proposal": self.proposal.to_dict() if self.proposal else None,
            "outcome": self.outcome,
            "reason_codes": self.reason_codes,
        }


def validate_initiative_realization(
    *, proposal: InitiativeProposal, conversation_candidate: Any,
    action_decision: Any,
) -> None:
    """Reject any initiative path that escapes the authored dialogue fence."""

    if getattr(conversation_candidate, "initiative_proposal_id", None) != proposal.proposal_id:
        raise ValueError("initiative realization must preserve proposal ownership")
    if getattr(conversation_candidate, "move", None) != "honor_obligation":
        raise ValueError("initiative may extend but cannot replace the conversational obligation")
    if getattr(conversation_candidate, "extension_move", None) != proposal.proposed_move:
        raise ValueError("initiative realization must preserve the validated optional move")
    action_kind = str(getattr(action_decision, "action_kind", ""))
    allowed = INITIATIVE_DIRECT_ACTION_KINDS | INITIATIVE_HIGHER_GATE_ACTION_KINDS
    if action_kind not in allowed:
        raise ValueError(f"initiative realization escaped bounded action space: {action_kind}")
    if (
        action_kind in INITIATIVE_DIRECT_ACTION_KINDS
        and str(getattr(action_decision, "target", "")) != "current interlocutor"
    ):
        raise ValueError("initiative speech cannot redirect its authored target")


def assess_conversation_initiative(
    *,
    actor_id: int,
    turn: int,
    obligation: str | None,
    initiative_budget: float,
    contextual_memories: Sequence[Any] = (),
    open_loop: Any | None = None,
    intrinsic_proposal: Any | None = None,
    relationship_expectations: Sequence[Any] = (),
    world_changes: Sequence[Mapping[str, Any]] = (),
    recent_source_ids: Sequence[str] = (),
    threshold: float = 0.62,
) -> InitiativeAssessment:
    """Choose at most one grounded optional move, or explain why none exists."""

    threshold = _clamp(threshold)
    sources: list[InitiativeSource] = []
    recent = set(str(item) for item in recent_source_ids[-8:])

    for retrieved in contextual_memories[:3]:
        memory = getattr(retrieved, "memory", retrieved)
        memory_id = str(getattr(memory, "id", ""))
        content = str(getattr(memory, "content", ""))
        tags = set(getattr(memory, "tags", ()))
        if (
            not memory_id or memory_id in recent
            or content.casefold().startswith("i heard you say")
            or {"sensorium", "ambient_event"} & tags
        ):
            continue
        reasons = getattr(retrieved, "reasons", {}) or {}
        contextual = _clamp(float(reasons.get("active_topic_score", 0.0)))
        score = _clamp(
            0.50
            + 0.22 * _clamp(getattr(memory, "salience", 0.5))
            + 0.18 * _clamp(getattr(memory, "emotional_intensity", 0.0))
            + 0.20 * contextual
        )
        sources.append(InitiativeSource(
            "contextual_memory", memory_id, str(getattr(memory, "id", "memory")),
            "reminisce", score, ("source:contextual_memory",),
        ))

    if open_loop is not None:
        source_id = str(getattr(open_loop, "topic_key", "") or getattr(open_loop, "topic", ""))
        if source_id and source_id not in recent:
            score = _clamp(
                0.42
                + 0.34 * _clamp(getattr(open_loop, "urgency", 0.0))
                + 0.18 * _clamp(getattr(open_loop, "emotional_charge", 0.0))
            )
            sources.append(InitiativeSource(
                "open_loop", source_id, source_id[:96], "probe", score,
                ("source:open_loop",),
            ))

    if intrinsic_proposal is not None:
        source_id = str(getattr(intrinsic_proposal, "proposal_id", ""))
        if source_id and source_id not in recent:
            action_kind = str(getattr(intrinsic_proposal, "proposed_action_kind", ""))
            move = {
                "observe": "speculate",
                "gesture": "probe",
                "silence": "continue_working",
            }.get(action_kind, "express_curiosity")
            score = _clamp(0.40 + 0.22 * max(0.0, float(getattr(intrinsic_proposal, "utility", 0.0))))
            sources.append(InitiativeSource(
                "intrinsic_activity", source_id,
                str(getattr(intrinsic_proposal, "activity_id", "activity"))[:96],
                move, score, ("source:intrinsic_activity", f"action:{action_kind}"),
            ))

    for expectation in relationship_expectations[:2]:
        source_id = str(getattr(expectation, "key", ""))
        if (
            source_id and source_id not in recent
            and str(getattr(expectation, "value", "")) in {"usually", "strongly_expected"}
        ):
            score = _clamp(0.40 + 0.30 * _clamp(getattr(expectation, "confidence", 0.0)))
            sources.append(InitiativeSource(
                "relationship_expectation", source_id, source_id[:96], "probe", score,
                ("source:relationship_expectation",),
            ))

    for event in world_changes[-4:]:
        source_id = str(event.get("event_id") or event.get("action") or "")
        if source_id and source_id not in recent:
            category = str(event.get("category", "ordinary"))
            score = 0.72 if (
                category in {"limitation", "rare_chaos"}
                or event.get("event_type") in {"correction", "discovery", "task_failure", "task_success"}
            ) else 0.65
            sources.append(InitiativeSource(
                "world_change", source_id, str(event.get("action", source_id))[:96],
                "speculate", score, ("source:world_change", f"category:{category}"),
            ))

    ordered = tuple(sorted(sources, key=lambda item: (-item.strength, item.source_kind, item.source_id))[:5])
    if not ordered:
        return InitiativeAssessment(
            1, int(actor_id), int(turn), threshold, (), None,
            "no_source_eligible", ("initiative:no_source_eligible",),
        )
    selected = ordered[0]
    if selected.strength < threshold or initiative_budget < 0.34:
        reasons = ["initiative:below_threshold"]
        if initiative_budget < 0.34:
            reasons.append("initiative:budget_exhausted")
        return InitiativeAssessment(
            1, int(actor_id), int(turn), threshold, ordered, None,
            "proposal_below_threshold", tuple(reasons),
        )
    proposal = InitiativeProposal(
        1, _stable_id(actor_id, turn, selected.source_kind, selected.source_id),
        int(actor_id), int(turn), selected.source_kind, selected.source_id,
        selected.topic_key, selected.proposed_move, selected.strength,
        selected.reason_codes,
    )
    outcome = "proposal_available"
    reasons = ["initiative:proposal_available"]
    if obligation not in {None, "acknowledge", "follow_up"}:
        outcome = "proposal_inhibited"
        reasons.append(f"initiative:obligation:{obligation}")
    return InitiativeAssessment(
        1, int(actor_id), int(turn), threshold, ordered, proposal, outcome, tuple(reasons),
    )
