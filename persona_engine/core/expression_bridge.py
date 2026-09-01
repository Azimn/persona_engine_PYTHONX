"""Portable noncanonical expression brief shared by every language substrate.

The character core resolves the character moment before this module is used.
This module only serializes that already-resolved moment for a renderer. The
brief is deliberately vendor-neutral so an Ollama model, local HF model,
frontier service, or deterministic renderer can all realize the same semantic
position without becoming authority over identity or history.
"""

from __future__ import annotations

from dataclasses import asdict, is_dataclass
from enum import Enum
import json
from typing import Any


EXPRESSION_BRIEF_SCHEMA_VERSION = "wayfarer-expression-brief-v1"


def _json_safe(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, Enum):
        return _json_safe(value.value)
    if is_dataclass(value):
        return _json_safe(asdict(value))
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    if isinstance(value, set):
        return [_json_safe(item) for item in sorted(value, key=lambda item: str(item))]
    if hasattr(value, "to_dict"):
        try:
            return _json_safe(value.to_dict())
        except Exception:
            pass
    if hasattr(value, "__dict__"):
        return {
            str(key): _json_safe(item)
            for key, item in vars(value).items()
            if not str(key).startswith("_")
        }
    return str(value)


def build_expression_brief(request: Any) -> dict[str, Any]:
    """Return the JSON-safe, substrate-neutral character moment for expression."""

    resolved = request.resolved_state if isinstance(request.resolved_state, dict) else {}
    return {
        "schema_version": EXPRESSION_BRIEF_SCHEMA_VERSION,
        "authority": "expression_only_noncanonical",
        "identity_and_development": _json_safe(request.ledger_digest),
        "experience_context": _json_safe(resolved.get("experience_context", {})),
        "workspace_context": str(resolved.get("system_prompt", "")),
        "user_text": str(resolved.get("user_text", "")),
        "arc_context": _json_safe(request.arc_context),
        "evidence": _json_safe(request.evidence),
        "relevant_memories": _json_safe(request.retrieved_memories),
        "private_thought_context": str(request.private_thought_context or ""),
        "decision_payload": _json_safe(request.decision_payload),
        "expression_constraints": _json_safe(request.expression_constraints),
        "deception_obligations": _json_safe(request.deception_obligations),
        "seed": _json_safe(request.seed),
    }


def build_expression_messages(request: Any) -> list[dict[str, str]]:
    """Build provider-neutral chat messages for a frontier or local language model."""

    brief = build_expression_brief(request)
    instructions = (
        "You are the language-expression substrate for one persistent character. "
        "The WAYFARER EXPRESSION BRIEF below is the authoritative character moment for this response; "
        "your own default persona, remembered role-play habits, or provider style are not character authority. "
        "Realize the decision_payload in first person while preserving identity_and_development, relationship stance, "
        "relevant memories, commitments, affect, voice, and expression constraints. Do not invent memories or world facts. "
        "Do not silently change the decision, identity, relationship, or developmental state. Do not expose or explain the brief. "
        "Return only the character's user-visible response.\n\nWAYFARER EXPRESSION BRIEF:\n"
        + json.dumps(brief, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    )
    return [
        {"role": "system", "content": instructions},
        {"role": "user", "content": brief["user_text"]},
    ]


def build_expression_prompt(request: Any) -> str:
    """Flatten the same brief/messages for completion-style local backends."""

    messages = build_expression_messages(request)
    return "\n\n".join(f"{message['role'].upper()}: {message['content']}" for message in messages)
