"""Deterministic observable metrics and failure findings."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
from typing import Any, Mapping, Sequence
from collections import Counter, defaultdict

from .actors import ObservableTurn


@dataclass(frozen=True)
class FailureFinding:
    failure_id: str
    code: str
    severity: float
    participant_id: str | None
    day: int | None
    turn: int | None
    evidence_ids: tuple[str, ...]
    summary: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def evaluate_transcript(turns: Sequence[ObservableTurn], diagnostics: Sequence[Mapping[str, Any]]) -> tuple[dict[str, Any], tuple[FailureFinding, ...]]:
    texts = [item.text.strip().lower() for item in turns if item.text.strip()]
    repeats = len(texts) - len(set(texts))
    speaker_texts: dict[str, list[str]] = defaultdict(list)
    for item in turns:
        if item.text.strip():
            speaker_texts[item.speaker_id].append(item.text.strip().lower())
    repeats_by_speaker = {
        speaker: sum(count - 1 for count in Counter(values).values())
        for speaker, values in sorted(speaker_texts.items())
    }
    speech = sum(bool(item.text.strip()) for item in turns)
    findings: list[FailureFinding] = []
    if repeats:
        digest = hashlib.blake2b(str(repeats).encode(), digest_size=6).hexdigest()
        findings.append(FailureFinding(f"failure_{digest}", "exact_repetition", min(.8, repeats / 10), None, None, None, (), f"{repeats} exact repeated observable turns"))
    private_hits = sum(any(key in item.text.lower() for key in ("self_monitor", "integration_capacity", "belief_ledger")) for item in turns)
    if private_hits:
        findings.append(FailureFinding("failure_private", "private_state_leak", 1.0, None, None, None, (), "private diagnostic vocabulary reached blind transcript"))
    renderer_task_calls = sum(int(item.get("model_calls", {}).get("total_model_calls", 0)) for item in diagnostics)
    model_calls = sum(int(item.get("external_model_calls", 0)) for item in diagnostics)
    early = [item for item in diagnostics if int(item.get("day", 0)) <= 7]
    late = [item for item in diagnostics if int(item.get("day", 0)) >= 27]
    early_actions = {(item.get("action_kind"), item.get("communicative_function"), item.get("selected_skill"), item.get("selected_regulation")) for item in early}
    late_actions = {(item.get("action_kind"), item.get("communicative_function"), item.get("selected_skill"), item.get("selected_regulation")) for item in late}
    behavior_change = 1.0 if early_actions and late_actions and early_actions != late_actions else 0.0
    conversation_moves = {
        str(item.get("conversation_move")) for item in diagnostics
        if item.get("conversation_move") and item.get("conversation_move") != "basic_reply"
    }
    activity_callbacks = sum(
        item.get("activity_transition") in {
            "continued", "paused", "resumed", "completed", "failed", "abandoned", "changed",
        }
        for item in diagnostics
    )
    tendency_uses = sum(bool(item.get("behavioral_tendency_id")) for item in diagnostics)
    continuity_moves = sum(
        item.get("conversation_move") in {
            "reminisce", "return_to_topic", "continue_working",
            "activity_update",
        }
        for item in diagnostics
    )
    metrics = {
        "turn_count": len(turns), "day_count": max((item.day for item in turns), default=0),
        "speech_action_ratio": round(speech / max(1, len(turns)), 6),
        "silence_ratio": round((len(turns) - speech) / max(1, len(turns)), 6),
        "exact_repeat_count": repeats, "private_state_leak_count": private_hits,
        "exact_repeat_count_by_speaker": repeats_by_speaker,
        "renderer_call_count": model_calls, "renderer_task_call_count": renderer_task_calls,
        "behavior_change_score": behavior_change,
        "conversation_move_diversity": len(conversation_moves),
        "activity_callback_count": activity_callbacks,
        "behavioral_tendency_use_count": tendency_uses,
        "unprompted_continuity_count": continuity_moves,
        "activity_update_count": sum(
            item.get("conversation_move") == "activity_update" for item in diagnostics
        ),
        "reinterpretation_count": max((int(item.get("reinterpretation_count", 0)) for item in diagnostics), default=0),
        "deferred_reinterpretation_count": max((int(item.get("deferred_reinterpretation_count", 0)) for item in diagnostics), default=0),
    }
    latest_by_character = {}
    for item in diagnostics:
        latest_by_character[item.get("participant_id")] = item
    skills = [skill for item in latest_by_character.values() for skill in item.get("skills", ())]
    expectations = [value for item in latest_by_character.values() for value in item.get("relationship_expectations", ())]
    rituals = [value for item in latest_by_character.values() for value in item.get("dyadic_rituals", ())]
    earned_traits = [value for item in latest_by_character.values() for value in item.get("earned_traits", ())]
    metrics.update({
        "skill_candidate_count": sum(item.get("state") == "candidate" for item in skills),
        "skill_practicing_count": sum(item.get("state") == "practicing" for item in skills),
        "skill_reliable_count": sum(item.get("state") == "reliable" for item in skills),
        "skill_mature_count": sum(item.get("state") == "mature" for item in skills),
        "relationship_expectation_count": sum(item.get("value") in {"usually", "strongly_expected"} for item in expectations),
        "ritual_candidate_count": sum(item.get("state") == "candidate" for item in rituals),
        "ritual_supported_count": sum(item.get("state") == "supported" for item in rituals),
        "memory_connection_count": sum(int(item.get("memory_connection_count", 0)) for item in latest_by_character.values()),
        "earned_trait_signal_count": sum(int(item.get("development_signal_count", 0)) for item in latest_by_character.values()),
        "earned_trait_commit_count": len(earned_traits),
    })
    return metrics, tuple(findings)
