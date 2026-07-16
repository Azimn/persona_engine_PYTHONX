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
        return cls(**raw)


def derive_conversation_candidate(
    *, text: str, actor_id: int, renderer_available: bool,
    retrieved: Sequence[Any], direct_memory_cue: bool,
    ready_open_loop: Any | None, familiarity: float, turn: int,
    repeated_input_count: int = 0,
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

    if ready_open_loop is not None and renderer_available and getattr(ready_open_loop, "status", "pending") == "ready":
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
    )


def renderer_is_model_backed(renderer: Any) -> bool:
    return str(getattr(renderer, "provider", "offline")) in {
        "ollama", "openai", "anthropic", "api", "local_hf",
    }
