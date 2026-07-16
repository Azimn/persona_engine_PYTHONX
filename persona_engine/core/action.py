"""Canonical situated action resolution.

Candidates come from existing cognitive systems.  This module is the single
boundary where selected influences become one inspectable action decision.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
import math
from typing import Any, Mapping, TYPE_CHECKING

if TYPE_CHECKING:
    from .habit import Habit
    from .intention import Intention
    from .intrinsic import IntrinsicProposal
    from .synthesis import SynthesisResult


ACTION_KINDS = frozenset({
    "speak", "gesture", "observe", "continue_activity", "delay", "silence",
    "world_action", "withdraw",
})


@dataclass(frozen=True)
class CommunicativeCandidate:
    dialogue_act: str
    communicative_function: str
    concealment_mode: str
    suspicion: float
    trigger_ids: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ActionDecision:
    schema_version: int
    decision_id: str
    tick: int
    source: str
    intention_id: str | None
    action_kind: str
    target: str
    communicative_function: str | None
    expected_effect: str
    selected_habit_id: str | None
    synthesis_id: str
    confidence: float
    interruptible: bool
    visibility: str
    reason_codes: tuple[str, ...]

    def __post_init__(self) -> None:
        if self.action_kind not in ACTION_KINDS:
            raise ValueError(f"unsupported action kind: {self.action_kind}")
        if not math.isfinite(float(self.confidence)) or not 0.0 <= float(self.confidence) <= 1.0:
            raise ValueError("action confidence must be finite and within [0, 1]")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "ActionDecision":
        values = {key: data[key] for key in cls.__dataclass_fields__ if key in data}
        values["reason_codes"] = tuple(values.get("reason_codes", ()))
        return cls(**values)


def resolve_action_decision(
    *,
    tick: int,
    synthesis: "SynthesisResult",
    selected_intention: "Intention | None",
    selected_habit: "Habit | None",
    intrinsic_proposal: "IntrinsicProposal | None",
    dialogue_act: str,
    resistance: str | None,
    current_activity: str,
    interruption: Mapping[str, Any],
) -> ActionDecision:
    """Resolve selected structured evidence into exactly one action."""

    proposal_selected = bool(
        intrinsic_proposal
        and synthesis.selected_intrinsic_proposal_id == intrinsic_proposal.proposal_id
    )
    reasons = [f"synthesis:{synthesis.synthesis_id}"]
    source = "situated_interaction"
    action_kind = "speak"
    target = "current interlocutor"
    communicative_function: str | None = dialogue_act
    interruptible = True
    visibility = "observable"
    intention_id = selected_intention.name if selected_intention else None

    if resistance == "go_quiet":
        action_kind = "silence"
        communicative_function = "withhold_response"
        reasons.append("resistance:go_quiet")
    elif resistance:
        reasons.append(f"resistance:{resistance}")
    elif proposal_selected and intrinsic_proposal is not None:
        source = f"intrinsic:{intrinsic_proposal.proposal_id}"
        target = intrinsic_proposal.target
        visibility = intrinsic_proposal.visibility
        interruptible = intrinsic_proposal.interruptible
        intention_id = intrinsic_proposal.intention
        proposed = intrinsic_proposal.proposed_action_kind
        if not interruption or proposed in {"gesture", "silence", "observe"} or not intrinsic_proposal.interruptible:
            action_kind = proposed
            communicative_function = None if proposed != "gesture" else "acknowledge"
            reasons.append("intrinsic_proposal:selected")
        else:
            target = "current interlocutor"
            reasons.append("intrinsic_proposal:informs_interruption_response")
    else:
        reasons.append("communicative_candidate:selected")

    expected = {
        "speak": "make the selected communicative function observable",
        "gesture": "make a bounded nonverbal signal observable",
        "observe": "gain bounded information without asserting a new fact",
        "continue_activity": f"continue {current_activity}",
        "delay": "defer response while preserving the active intention",
        "silence": "withhold speech while preserving organism continuity",
        "world_action": "submit the action to World Authority for resolution",
        "withdraw": "reduce immediate interaction exposure",
    }[action_kind]
    confidence = max(0.0, min(1.0, 0.45 + synthesis.reality_support * 0.35))
    canonical = {
        "tick": int(tick),
        "source": source,
        "action_kind": action_kind,
        "target": target,
        "synthesis_id": synthesis.synthesis_id,
        "intention_id": intention_id,
        "habit_id": selected_habit.name if selected_habit else None,
        "interrupted": bool(interruption),
    }
    digest = hashlib.blake2b(
        json.dumps(canonical, sort_keys=True).encode("utf-8"), digest_size=8,
    ).hexdigest()
    return ActionDecision(
        schema_version=1,
        decision_id=f"action_{digest}",
        tick=int(tick),
        source=source,
        intention_id=intention_id,
        action_kind=action_kind,
        target=str(target)[:120],
        communicative_function=communicative_function,
        expected_effect=expected,
        selected_habit_id=selected_habit.name if selected_habit else None,
        synthesis_id=synthesis.synthesis_id,
        confidence=round(confidence, 6),
        interruptible=bool(interruptible),
        visibility=str(visibility),
        reason_codes=tuple(reasons),
    )
