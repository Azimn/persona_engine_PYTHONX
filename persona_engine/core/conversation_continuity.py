"""Bounded per-actor dialogue blackboard for conversational continuity."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
import re
from typing import Any, Mapping, Sequence


OBLIGATIONS = frozenset({"answer", "clarify", "acknowledge", "repair", "follow_up"})
TRANSITION_REASONS = frozenset({"completed", "exhausted", "interrupted", "avoided", "displaced"})
OPTIONAL_MOVES = frozenset({
    "probe", "compare", "challenge", "reminisce", "speculate",
    "express_curiosity", "continue_working",
})
MAX_CONTINUITY_ACTORS = 256
MAX_BACKGROUND_TOPICS = 2
MAX_RECENT_SIGNATURES = 8

_STOP_WORDS = frozenset({
    "about", "after", "again", "could", "from", "have", "hello", "into",
    "just", "matter", "please", "that", "the", "their", "there", "these", "they", "this",
    "what", "when", "where", "which", "with", "would", "your",
})


def _tokens(value: str) -> frozenset[str]:
    return frozenset(
        item for item in re.findall(r"[a-z0-9']+", str(value).lower())
        if len(item) >= 3 and item not in _STOP_WORDS
    )


def topic_similarity(left: str, right: str) -> float:
    a, b = _tokens(left), _tokens(right)
    if not a or not b:
        return 0.0
    return len(a & b) / max(1, len(a | b))


def obligation_for_input(input_act: str) -> str:
    if input_act in {"ask_fact", "ask_opinion", "ask_memory", "ask_analysis", "request_action", "challenge"}:
        return "answer"
    if input_act == "apologize":
        return "repair"
    return "acknowledge"


@dataclass
class ConversationTopic:
    topic_id: str
    label: str
    depth: int
    freshness: float
    emotional_importance: float
    first_turn: int
    last_turn: int

    def __post_init__(self) -> None:
        if not self.topic_id or len(self.topic_id) > 96:
            raise ValueError("topic_id must contain 1..96 characters")
        if not self.label or len(self.label) > 160:
            raise ValueError("topic label must contain 1..160 characters")
        if not 1 <= int(self.depth) <= 12:
            raise ValueError("topic depth must be within [1, 12]")
        for value in (self.freshness, self.emotional_importance):
            if not 0.0 <= float(value) <= 1.0:
                raise ValueError("topic values must be within [0, 1]")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "ConversationTopic":
        return cls(**{key: value[key] for key in cls.__dataclass_fields__ if key in value})


@dataclass
class ConversationContinuityState:
    actor_id: int
    active_topic: ConversationTopic | None = None
    background_topics: list[ConversationTopic] = field(default_factory=list)
    pending_obligation: str | None = None
    initiative_budget: float = 0.45
    recent_move_signatures: list[str] = field(default_factory=list)
    last_transition_reason: str | None = None
    last_action_kind: str | None = None

    def __post_init__(self) -> None:
        if not 0 < int(self.actor_id) <= 0xFFFFFFFF:
            raise ValueError("conversation actor_id must be a nonzero uint32")
        if self.pending_obligation is not None and self.pending_obligation not in OBLIGATIONS:
            raise ValueError("unsupported conversation obligation")
        if not 0.0 <= float(self.initiative_budget) <= 1.0:
            raise ValueError("initiative budget must be within [0, 1]")
        if len(self.background_topics) > MAX_BACKGROUND_TOPICS:
            raise ValueError("background topic bound exceeded")
        if len(self.recent_move_signatures) > MAX_RECENT_SIGNATURES:
            raise ValueError("move signature bound exceeded")
        if self.last_transition_reason is not None and self.last_transition_reason not in TRANSITION_REASONS:
            raise ValueError("unsupported topic transition reason")

    def observe_input(
        self, *, text: str, input_act: str, topic_id: str, turn: int,
        emotional_importance: float,
    ) -> None:
        self.last_transition_reason = None
        self.pending_obligation = obligation_for_input(input_act)
        self.initiative_budget = min(1.0, self.initiative_budget + 0.08)
        for topic in self.background_topics:
            topic.freshness = max(0.0, topic.freshness - 0.08)
        if self.active_topic and re.search(
            r"\b(that answers it|that settles it|we are done|we're done|enough on that|case closed)\b",
            str(text).lower(),
        ):
            self.last_transition_reason = "completed"
            self.active_topic.freshness = max(0.0, self.active_topic.freshness - 0.5)
            self.background_topics = [self.active_topic, *self.background_topics][:MAX_BACKGROUND_TOPICS]
            self.active_topic = None
            return
        if input_act in {"greeting", "leave_or_return", "low_information"}:
            if self.active_topic:
                self.active_topic.freshness = max(0.0, self.active_topic.freshness - 0.04)
            return

        label = " ".join(str(text).split())[:160] or topic_id
        similarity = topic_similarity(label, self.active_topic.label) if self.active_topic else 0.0
        anaphoric_continuation = bool(
            self.active_topic
            and re.search(r"\b(it|that|this|they|them|those|the idea|the point)\b", label.lower())
            and len(_tokens(label)) <= 8
        )
        if self.active_topic and (
            topic_id == self.active_topic.topic_id
            or similarity >= 0.12
            or anaphoric_continuation
        ):
            self.active_topic.depth = min(12, self.active_topic.depth + 1)
            self.active_topic.freshness = 1.0
            self.active_topic.emotional_importance = max(
                self.active_topic.emotional_importance,
                max(0.0, min(1.0, float(emotional_importance))),
            )
            self.active_topic.last_turn = int(turn)
            return

        if self.active_topic:
            self.last_transition_reason = "displaced"
            self.background_topics = [
                self.active_topic,
                *[item for item in self.background_topics if item.topic_id != self.active_topic.topic_id],
            ][:MAX_BACKGROUND_TOPICS]
        self.active_topic = ConversationTopic(
            topic_id=str(topic_id)[:96], label=label, depth=1, freshness=1.0,
            emotional_importance=max(0.0, min(1.0, float(emotional_importance))),
            first_turn=int(turn), last_turn=int(turn),
        )

    def extension_allowed(self, move: str | None) -> tuple[bool, str | None]:
        if not move or move not in OPTIONAL_MOVES:
            return False, "extension:none"
        signature = self.signature(move)
        if self.pending_obligation in {"clarify", "repair"}:
            return False, f"extension:blocked_by_{self.pending_obligation}"
        if self.initiative_budget < 0.34:
            return False, "extension:initiative_exhausted"
        if signature in self.recent_move_signatures[-4:]:
            return False, "extension:semantic_repeat"
        if self.active_topic and self.active_topic.depth >= 8 and move in {"probe", "speculate", "express_curiosity"}:
            return False, "extension:topic_exhausted"
        return True, None

    def signature(self, extension_move: str | None) -> str:
        return f"{self.pending_obligation}|{extension_move or 'none'}"

    def complete_turn(
        self, *, extension_move: str | None, action_kind: str | None = None,
        transition_reason: str | None = None,
    ) -> None:
        signature = self.signature(extension_move)
        self.recent_move_signatures = [*self.recent_move_signatures, signature][-MAX_RECENT_SIGNATURES:]
        if extension_move:
            self.initiative_budget = max(0.0, self.initiative_budget - 0.34)
        else:
            self.initiative_budget = min(1.0, self.initiative_budget + 0.04)
        if transition_reason in TRANSITION_REASONS:
            self.last_transition_reason = transition_reason
            if transition_reason in {"completed", "exhausted", "avoided"} and self.active_topic:
                self.active_topic.freshness = max(0.0, self.active_topic.freshness - 0.35)
        self.last_action_kind = str(action_kind)[:32] if action_kind else None
        self.pending_obligation = None

    def memory_context_score(self, content: str) -> float:
        if not self.active_topic:
            return 0.0
        direct = topic_similarity(content, self.active_topic.label)
        background = max(
            (topic_similarity(content, item.label) * 0.45 for item in self.background_topics),
            default=0.0,
        )
        return round(max(direct, background), 6)

    def summary(self) -> str:
        active = self.active_topic.topic_id if self.active_topic else "none"
        return (
            f"active={active}; depth={self.active_topic.depth if self.active_topic else 0}; "
            f"obligation={self.pending_obligation}; initiative={self.initiative_budget:.2f}; "
            f"transition={self.last_transition_reason or 'none'}"
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "actor_id": self.actor_id,
            "active_topic": self.active_topic.to_dict() if self.active_topic else None,
            "background_topics": [item.to_dict() for item in self.background_topics],
            "pending_obligation": self.pending_obligation,
            "initiative_budget": round(self.initiative_budget, 6),
            "recent_move_signatures": self.recent_move_signatures[-MAX_RECENT_SIGNATURES:],
            "last_transition_reason": self.last_transition_reason,
            "last_action_kind": self.last_action_kind,
        }

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "ConversationContinuityState":
        active = value.get("active_topic")
        return cls(
            actor_id=int(value["actor_id"]),
            active_topic=ConversationTopic.from_dict(active) if active else None,
            background_topics=[
                ConversationTopic.from_dict(item) for item in value.get("background_topics", ())
            ][:MAX_BACKGROUND_TOPICS],
            pending_obligation=(
                str(value["pending_obligation"]) if value.get("pending_obligation") else None
            ),
            initiative_budget=float(value.get("initiative_budget", 0.45)),
            recent_move_signatures=[
                str(item)[:80] for item in value.get("recent_move_signatures", ())
            ][-MAX_RECENT_SIGNATURES:],
            last_transition_reason=value.get("last_transition_reason"),
            last_action_kind=value.get("last_action_kind"),
        )


class ConversationContinuityStore:
    def __init__(self, states: Sequence[ConversationContinuityState] = ()) -> None:
        if len(states) > MAX_CONTINUITY_ACTORS:
            raise ValueError("conversation continuity actor bound exceeded")
        self.states = {item.actor_id: item for item in states}

    def for_actor(self, actor_id: int) -> ConversationContinuityState:
        actor_id = int(actor_id)
        if actor_id not in self.states:
            if len(self.states) >= MAX_CONTINUITY_ACTORS:
                raise ValueError("conversation continuity store is full")
            self.states[actor_id] = ConversationContinuityState(actor_id=actor_id)
        return self.states[actor_id]

    def to_list(self) -> list[dict[str, Any]]:
        return [self.states[key].to_dict() for key in sorted(self.states)]

    @classmethod
    def from_list(cls, values: Sequence[Mapping[str, Any]] | None) -> "ConversationContinuityStore":
        return cls(tuple(ConversationContinuityState.from_dict(item) for item in (values or ())))
