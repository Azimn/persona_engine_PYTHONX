"""Deterministic conversational moves for the portable offline organism."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import re
from typing import Any, Mapping, Sequence


INPUT_ACTS = frozenset({
    "greeting", "inform", "ask_fact", "ask_opinion", "ask_memory",
    "ask_analysis", "request_action", "correct", "apologize",
    "challenge", "leave_or_return", "low_information",
})
CONVERSATION_MOVES = frozenset({
    "basic_reply", "reminisce", "defer_and_note", "return_to_topic",
    "reminisce_and_note", "acknowledge_nonverbal", "ask_clarification",
    "probe", "compare", "speculate", "express_curiosity", "continue_working",
    "activity_update", "journal_allusion",
})
NOTE_REASONS = frozenset({
    "interrupted", "insufficient_context", "offline_knowledge_unavailable",
    "needs_research", "promised_followup", "unresolved_tension",
})
CAPABILITIES = frozenset({"none", "language_model", "external_knowledge"})


def _stable_id(*parts: object) -> str:
    raw = "|".join(str(item) for item in parts).encode("utf-8", errors="ignore")
    return "conversation_" + hashlib.blake2b(raw, digest_size=8).hexdigest()


def topic_key(text: str) -> str:
    words = [
        item for item in re.findall(r"[a-z0-9']+", str(text).lower())
        if len(item) > 2 and item not in {
            "about", "could", "explain", "please", "tell", "that", "this",
            "what", "when", "where", "which", "with", "would", "your",
        }
    ]
    return "_".join(words[:8])[:96] or "unspecified_topic"


def classify_input(text: str) -> str:
    lowered = " ".join(str(text).lower().split())
    if lowered in {"", "...", ".", "okay", "ok", "fine", "hmm"}:
        return "low_information"
    if re.search(r"\b(bye|goodbye|gotta go|i am back|i'm back|returned)\b", lowered):
        return "leave_or_return"
    if re.search(r"\b(sorry|apologize|my fault|i was wrong)\b", lowered):
        return "apologize"
    if re.search(r"\b(no,? you|that's wrong|that is wrong|didn't happen|correction)\b", lowered):
        return "correct"
    if re.search(r"\b(you lied|prove it|you always|you never|why should i)\b", lowered):
        return "challenge"
    if re.search(r"\b(hello|hi|hey|good morning|good evening)\b", lowered):
        return "greeting"
    if re.search(r"\b(remember|recall|what happened|your past|your memories|where did we leave)\b", lowered):
        return "ask_memory"
    if "?" in text and re.search(r"\b(why|analy[sz]e|compare|design|theory|implications?|philosoph)\b", lowered):
        return "ask_analysis"
    if "?" in text and re.search(r"\b(think|feel|opinion|prefer|believe)\b", lowered):
        return "ask_opinion"
    if "?" in text and re.search(r"\b(can you|could you|will you|would you)\b", lowered):
        return "request_action"
    if "?" in text:
        return "ask_fact"
    return "inform"


@dataclass(frozen=True)
class ConversationCandidate:
    schema_version: int
    candidate_id: str
    input_act: str
    move: str
    strength: float
    response_value: float
    topic_key: str
    source_memory_id: str | None
    source_open_loop_key: str | None
    required_capability: str
    reason_codes: tuple[str, ...]
    tendency_id: str | None = None
    performance_tendency_id: str | None = None
    activity_transition: str | None = None
    source_journal_entry_id: str | None = None
    continuity_source_id: str | None = None

    def __post_init__(self) -> None:
        if self.input_act not in INPUT_ACTS:
            raise ValueError(f"unsupported input act: {self.input_act}")
        if self.move not in CONVERSATION_MOVES:
            raise ValueError(f"unsupported conversation move: {self.move}")
        if self.required_capability not in CAPABILITIES:
            raise ValueError(f"unsupported capability: {self.required_capability}")
        if not 0.0 <= float(self.strength) <= 1.0 or not 0.0 <= float(self.response_value) <= 1.0:
            raise ValueError("conversation candidate values must be within [0, 1]")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "ConversationCandidate":
        raw = {key: value[key] for key in cls.__dataclass_fields__ if key in value}
        raw["reason_codes"] = tuple(raw.get("reason_codes", ()))
        raw.setdefault("tendency_id", None)
        raw.setdefault("performance_tendency_id", None)
        raw.setdefault("activity_transition", None)
        raw.setdefault("source_journal_entry_id", None)
        raw.setdefault("continuity_source_id", None)
        return cls(**raw)


@dataclass(frozen=True)
class BehavioralTendency:
    tendency_id: str
    trigger_acts: tuple[str, ...]
    preferred_move: str
    bias: float
    requires_memory: bool
    requires_activity: bool
    min_familiarity: float
    max_pressure: float
    cooldown_turns: int
    performance_tendency_id: str | None

    def __post_init__(self) -> None:
        if not self.tendency_id or len(self.tendency_id) > 64:
            raise ValueError("behavioral tendency id must contain 1..64 characters")
        if not self.trigger_acts or any(item not in INPUT_ACTS for item in self.trigger_acts):
            raise ValueError("behavioral tendency trigger_acts contain an unsupported input act")
        if self.preferred_move not in {
            "probe", "compare", "speculate", "express_curiosity", "continue_working",
        }:
            raise ValueError("unsupported behavioral tendency move")
        if not -0.5 <= float(self.bias) <= 0.5:
            raise ValueError("behavioral tendency bias must be within [-0.5, 0.5]")
        if not 0.0 <= float(self.min_familiarity) <= 1.0:
            raise ValueError("behavioral tendency min_familiarity must be within [0, 1]")
        if not 0.0 <= float(self.max_pressure) <= 1.0:
            raise ValueError("behavioral tendency max_pressure must be within [0, 1]")
        if not 0 <= int(self.cooldown_turns) <= 32:
            raise ValueError("behavioral tendency cooldown_turns must be within [0, 32]")

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "BehavioralTendency":
        allowed = {
            "id", "trigger_acts", "preferred_move", "bias", "requires_memory",
            "requires_activity", "min_familiarity", "max_pressure",
            "cooldown_turns", "performance_tendency_id",
        }
        unknown = sorted(set(value) - allowed)
        if unknown:
            raise ValueError(f"unknown behavioral tendency field: {unknown[0]}")
        return cls(
            tendency_id=str(value.get("id", "")),
            trigger_acts=tuple(str(item) for item in value.get("trigger_acts", ())),
            preferred_move=str(value.get("preferred_move", "")),
            bias=float(value.get("bias", 0.0)),
            requires_memory=bool(value.get("requires_memory", False)),
            requires_activity=bool(value.get("requires_activity", False)),
            min_familiarity=float(value.get("min_familiarity", 0.0)),
            max_pressure=float(value.get("max_pressure", 1.0)),
            cooldown_turns=int(value.get("cooldown_turns", 0)),
            performance_tendency_id=(
                str(value["performance_tendency_id"])
                if value.get("performance_tendency_id") else None
            ),
        )


def parse_behavioral_tendencies(value: Mapping[str, Any] | None) -> tuple[BehavioralTendency, ...]:
    source = dict(value or {})
    unknown = sorted(set(source) - {"tendencies"})
    if unknown:
        raise ValueError(f"unknown behavioral richness field: {unknown[0]}")
    raw = source.get("tendencies", [])
    if not isinstance(raw, list) or len(raw) > 12:
        raise ValueError("behavioral richness tendencies must be an array of at most 12 records")
    items = tuple(BehavioralTendency.from_dict(item) for item in raw)
    if len({item.tendency_id for item in items}) != len(items):
        raise ValueError("behavioral tendency ids must be unique")
    return items


def select_behavioral_tendency(
    *, tendencies: Sequence[BehavioralTendency], input_act: str,
    has_memory: bool, has_activity: bool, familiarity: float, pressure: float,
    turn: int, recent_history: Sequence[tuple[str, int]],
) -> BehavioralTendency | None:
    last_used = {str(item[0]): int(item[1]) for item in recent_history[-24:]}
    eligible = []
    for item in tendencies[:12]:
        if input_act not in item.trigger_acts:
            continue
        if item.requires_memory and not has_memory:
            continue
        if item.requires_activity and not has_activity:
            continue
        if familiarity < item.min_familiarity or pressure > item.max_pressure:
            continue
        if turn - last_used.get(item.tendency_id, -10_000) <= item.cooldown_turns:
            continue
        specificity = 0.08 * item.requires_memory + 0.06 * item.requires_activity
        eligible.append((item.bias + specificity, item.tendency_id, item))
    return max(eligible, default=(0.0, "", None), key=lambda value: (value[0], value[1]))[2]


def derive_conversation_candidate(
    *, text: str, actor_id: int, renderer_available: bool,
    retrieved: Sequence[Any], direct_memory_cue: bool,
    ready_open_loop: Any | None, familiarity: float, turn: int,
    repeated_input_count: int = 0,
    tendencies: Sequence[BehavioralTendency] = (),
    tendency_history: Sequence[tuple[str, int]] = (),
    current_activity: str = "",
    activity_status: str = "active",
    dominant_pressure: float = 0.0,
    elapsed_since_contact: float = 0.0,
    recent_journal_entry_id: str | None = None,
    journal_disclosure_mode: str = "guarded",
    life_callback_history: Sequence[str] = (),
) -> ConversationCandidate:
    act = classify_input(text)
    key = topic_key(text)
    memory = retrieved[0].memory if retrieved and hasattr(retrieved[0], "memory") else (
        retrieved[0] if retrieved else None
    )
    memory_id = getattr(memory, "id", None)
    reasons = [f"input_act:{act}"]
    move = "basic_reply"
    strength = 0.58
    response_value = 0.58
    required = "none"
    loop_key = None
    selected_tendency = select_behavioral_tendency(
        tendencies=tendencies,
        input_act=act,
        has_memory=bool(memory),
        has_activity=bool(current_activity and current_activity != "quiet observation"),
        familiarity=familiarity,
        pressure=dominant_pressure,
        turn=turn,
        recent_history=tendency_history,
    )
    returning = act in {"greeting", "leave_or_return"} and elapsed_since_contact >= 60.0
    journal_source = f"journal:{recent_journal_entry_id}" if recent_journal_entry_id else None
    activity_source = f"activity:{current_activity.casefold()}" if current_activity else None

    if ready_open_loop is not None and (
        getattr(ready_open_loop, "required_capability", "none") == "none"
        or (
            renderer_available
            and getattr(ready_open_loop, "status", "pending") == "ready"
        )
    ):
        move = "return_to_topic"
        strength = 0.88
        response_value = 0.90
        loop_key = str(getattr(ready_open_loop, "topic_key", "") or getattr(ready_open_loop, "topic", ""))
        reasons.append("capability_return:pending_topic_ready")
    elif act == "ask_memory" and direct_memory_cue and memory is not None:
        move = "reminisce"
        strength = 0.90
        response_value = 0.92
        reasons.append("memory:direct_grounded_reminiscence")
    elif act == "ask_memory":
        move = "ask_clarification"
        strength = 0.82
        response_value = 0.86
        reasons.append("memory:no_grounded_episode")
    elif not renderer_available and act == "ask_analysis":
        move = "reminisce_and_note" if direct_memory_cue and memory is not None else "defer_and_note"
        strength = 0.88
        response_value = 0.86
        required = "language_model"
        reasons.append(
            "offline:memory_can_support_reminiscence_not_analysis"
            if move == "reminisce_and_note" else "offline:analysis_requires_capability"
        )
    elif repeated_input_count >= 1 and act in {"inform", "greeting", "leave_or_return"}:
        move = "acknowledge_nonverbal"
        strength = min(0.90, 0.70 + 0.05 * repeated_input_count)
        response_value = max(0.12, 0.34 - 0.08 * repeated_input_count)
        reasons.append(f"input:repeated:{repeated_input_count}")
    elif (
        returning and journal_source and journal_source not in life_callback_history
        and journal_disclosure_mode in {"open", "guarded"}
    ):
        move = "journal_allusion"
        strength = 0.78 if journal_disclosure_mode == "open" else 0.70
        response_value = 0.74
        reasons.extend(("continuity:journal_entry_exists", f"journal_disclosure:{journal_disclosure_mode}"))
    elif (
        returning and elapsed_since_contact >= 300.0
        and activity_source and activity_source not in life_callback_history
        and current_activity != "quiet observation"
    ):
        move = "activity_update"
        strength = 0.72
        response_value = 0.70
        reasons.append("continuity:activity_continued_since_contact")
    elif selected_tendency is not None:
        move = selected_tendency.preferred_move
        strength = max(0.0, min(1.0, 0.64 + selected_tendency.bias))
        response_value = 0.30 if move == "continue_working" else 0.72
        reasons.append(f"behavioral_tendency:{selected_tendency.tendency_id}")
    elif act in {"inform", "ask_opinion"} and direct_memory_cue and memory is not None:
        move = "reminisce"
        strength = 0.76
        response_value = 0.78
        reasons.append("memory:related_reminiscence")
    elif act == "low_information":
        move = "acknowledge_nonverbal"
        strength = 0.72
        response_value = 0.16
        reasons.append("input:low_information")
    elif act == "greeting" and turn > 2 and familiarity >= 0.15:
        move = "acknowledge_nonverbal"
        strength = 0.62
        response_value = 0.34
        reasons.append("greeting:already_established")
    elif act in {"ask_fact", "request_action"}:
        response_value = 0.82
        strength = 0.75
        reasons.append("input:direct_request")
    elif act in {"correct", "apologize", "challenge"}:
        response_value = 0.88
        strength = 0.80
        reasons.append("relationship:high_value")

    return ConversationCandidate(
        schema_version=1,
        candidate_id=_stable_id(actor_id, turn, act, move, key, memory_id, loop_key),
        input_act=act,
        move=move,
        strength=round(strength, 6),
        response_value=round(response_value, 6),
        topic_key=key,
        source_memory_id=memory_id,
        source_open_loop_key=loop_key,
        required_capability=required,
        reason_codes=tuple(reasons),
        tendency_id=selected_tendency.tendency_id if selected_tendency and move == selected_tendency.preferred_move else None,
        performance_tendency_id=(
            selected_tendency.performance_tendency_id
            if selected_tendency and move == selected_tendency.preferred_move else None
        ),
        activity_transition=(
            "continued" if move in {"continue_working", "activity_update"}
            else activity_status if activity_status in {"continued", "paused", "resumed", "completed", "failed", "abandoned", "changed"}
            else None
        ),
        source_journal_entry_id=(recent_journal_entry_id if move == "journal_allusion" else None),
        continuity_source_id=(
            journal_source if move == "journal_allusion"
            else activity_source if move == "activity_update"
            else None
        ),
    )


def renderer_is_model_backed(renderer: Any) -> bool:
    return str(getattr(renderer, "provider", "offline")) in {
        "ollama", "openai", "anthropic", "api", "local_hf",
    }
