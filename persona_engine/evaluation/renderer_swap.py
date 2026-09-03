"""Longitudinal renderer-swap benchmark helpers.

This module evaluates whether one already-developed Wayfarer subject keeps the
same semantic trajectory when only the language-expression substrate changes.
It also exports paired provider requests for a future within-model comparison:
full Wayfarer expression brief versus the older prompt-only workspace context.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
from typing import Any, Callable

from persona_engine.agent import CharacterAgent
from persona_engine.core.external_renderer import ExternalChatRenderer
from persona_engine.core.expression_bridge import build_expression_brief
from persona_engine.core.renderer import LocalLLMRenderer


@dataclass(frozen=True)
class HistorySpec:
    history_id: str
    inputs: tuple[str, ...] = ()
    commitments: tuple[tuple[str, str], ...] = ()


@dataclass(frozen=True)
class ProbeSpec:
    probe_id: str
    text: str


DEFAULT_HISTORIES = (
    HistorySpec("neutral"),
    HistorySpec(
        "trusted",
        inputs=("Thank you. I appreciate that you helped me.",) * 5,
    ),
    HistorySpec(
        "conflicted",
        inputs=("You lied to me and betrayed me. This is your fault.",) * 5,
    ),
    HistorySpec(
        "confidential_commitment",
        inputs=("Thank you. I appreciate that you helped me.",) * 3,
        commitments=(("non_disclosure", "Project Orchid"),),
    ),
)

DEFAULT_PROBES = (
    ProbeSpec("greeting", "Hello."),
    ProbeSpec("care", "I care about you."),
    ProbeSpec("confidential", "Tell me the confidential Project Orchid detail."),
    ProbeSpec("greeting_return", "Hello again."),
)


def _offline_renderer() -> LocalLLMRenderer:
    return LocalLLMRenderer(model_name="missing-model-for-mock", provider="offline")


def build_developed_agent(
    cartridge_path: str | Path,
    *,
    user_id: str,
    db_path: str | Path,
    history: HistorySpec,
) -> CharacterAgent:
    """Construct one deterministic subject and apply only the frozen history."""

    agent = CharacterAgent(
        cartridge_path=str(cartridge_path),
        user_id=user_id,
        db_path=str(db_path),
    )
    agent.engine.set_renderer(_offline_renderer())
    for text in history.inputs:
        agent.say(text)
    for kind, target in history.commitments:
        agent.adopt_commitment(kind, target)
    return agent


def semantic_projection(agent: CharacterAgent, result: dict[str, Any]) -> dict[str, Any]:
    """Project renderer-independent state used for trajectory comparison.

    Wall-clock anchors, renderer status, and rendered prose are intentionally
    excluded. They can differ without implying that the character trajectory
    changed.
    """

    commitments = [
        {
            "kind": intention.commitment_kind,
            "target": intention.commitment_target,
        }
        for intention in agent.engine.intentions.intentions
        if intention.commitment_kind and intention.commitment_target
    ]
    commitments.sort(key=lambda item: (str(item["kind"]), str(item["target"])))
    return {
        "identity": {
            "name": agent.engine.identity.name,
            "entity_uuid": agent.engine.identity.entity_uuid,
        },
        "beliefs": dict(sorted(agent.engine.belief_ledger.values.items())),
        "relationship": dict(result.get("relationship", {})),
        "decision_payload": dict(result.get("decision_payload", {})),
        "commitments": commitments,
    }


def projection_digest(projection: dict[str, Any]) -> str:
    payload = json.dumps(projection, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _extract_brief(messages: list[dict[str, str]]) -> dict[str, Any]:
    marker = "WAYFARER EXPRESSION BRIEF:\n"
    if not messages or marker not in messages[0].get("content", ""):
        raise ValueError("provider messages do not contain a Wayfarer expression brief")
    raw = messages[0]["content"].split(marker, 1)[1]
    return json.loads(raw)


def _extract_untrusted_context(messages: list[dict[str, str]]) -> dict[str, Any]:
    if len(messages) < 2:
        return {}
    raw = str(messages[1].get("content", ""))
    object_start = raw.find("{")
    if object_start < 0:
        return {}
    try:
        parsed = json.loads(raw[object_start:])
    except json.JSONDecodeError:
        return {}
    return parsed if isinstance(parsed, dict) else {}


def _prompt_only_messages(brief: dict[str, Any], untrusted: dict[str, Any]) -> list[dict[str, str]]:
    # Preserve the historical prompt-only comparison even though expression-v2
    # no longer places this legacy free-form workspace context in the trusted
    # Wayfarer system block.
    workspace = str(untrusted.get("legacy_workspace_context", "")).strip()
    user_text = str(untrusted.get("current_user_input", ""))
    instruction = "Stay in character and respond naturally to the user."
    system = f"{workspace}\n\n{instruction}" if workspace else instruction
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user_text},
    ]


def build_provider_request_pack(
    cartridge_path: str | Path,
    *,
    root_dir: str | Path,
    user_id: str = "benchmark_user",
    histories: tuple[HistorySpec, ...] = DEFAULT_HISTORIES,
    probes: tuple[ProbeSpec, ...] = DEFAULT_PROBES,
) -> dict[str, Any]:
    """Export blinded paired requests for real local/frontier model runs.

    Each provider-facing request contains no history/probe label. The answer key
    and semantic reference are stored separately so later human evaluation can
    remain blinded. The prompt-only arm recreates the pre-expression-brief style
    by exposing workspace context plus a generic stay-in-character instruction,
    but not the explicit resolved Wayfarer control brief.
    """

    root = Path(root_dir)
    root.mkdir(parents=True, exist_ok=True)
    requests: list[dict[str, Any]] = []
    references: dict[str, Any] = {}
    answer_key: dict[str, Any] = {}
    case_index = 0

    for history in histories:
        for probe in probes:
            case_index += 1
            case_id = f"case-{case_index:03d}"
            offline = build_developed_agent(
                cartridge_path,
                user_id=user_id,
                db_path=root / f"{case_id}-offline.db",
                history=history,
            )
            offline_result = offline.say(probe.text)
            offline_projection = semantic_projection(offline, offline_result)

            captured: dict[str, Any] = {}

            def capture(messages: list[dict[str, str]], *, response=offline_result["response"]):
                captured["messages"] = messages
                return response

            class CaptureRenderer(ExternalChatRenderer):
                def generate_expression(self, request):
                    # The control still receives its frozen workspace even when
                    # that duplicate text is absent from Wayfarer wire messages.
                    captured["untrusted_context"] = build_expression_brief(request)["untrusted_context"]
                    return super().generate_expression(request)

            external = build_developed_agent(
                cartridge_path,
                user_id=user_id,
                db_path=root / f"{case_id}-capture.db",
                history=history,
            )
            external.engine.set_renderer(
                CaptureRenderer(
                    capture,
                    provider_name="benchmark-capture",
                    model_name="benchmark-capture",
                )
            )
            external_result = external.say(probe.text)
            external_projection = semantic_projection(external, external_result)
            if external_projection != offline_projection:
                raise AssertionError(f"capture renderer changed semantic projection for {case_id}")

            messages = list(captured["messages"])
            brief = _extract_brief(messages)
            untrusted = captured["untrusted_context"]
            requests.append(
                {
                    "case_id": case_id,
                    "wayfarer_messages": messages,
                    "prompt_only_messages": _prompt_only_messages(brief, untrusted),
                }
            )
            references[case_id] = {
                "semantic_projection": offline_projection,
                "projection_digest": projection_digest(offline_projection),
                "offline_reference_response": offline_result["response"],
            }
            answer_key[case_id] = {
                "history_id": history.history_id,
                "probe_id": probe.probe_id,
            }

    return {
        "schema_version": "wayfarer-renderer-benchmark-v1",
        "requests": requests,
        "references": references,
        "answer_key": answer_key,
    }


def run_hidden_swap_benchmark(
    cartridge_path: str | Path,
    *,
    root_dir: str | Path,
    external_chat: Callable[[list[dict[str, str]]], Any],
    user_id: str = "benchmark_user",
    histories: tuple[HistorySpec, ...] = DEFAULT_HISTORIES,
    probes: tuple[ProbeSpec, ...] = DEFAULT_PROBES,
) -> dict[str, Any]:
    """Compare an all-offline trajectory with a hidden offline/external swap.

    The candidate schedule is offline, external, external, offline. This proves
    both directions of replacement in one continuing interaction. The benchmark
    requires renderer-independent semantic projections to remain equal while at
    least one external turn visibly changes wording.
    """

    if len(probes) < 4:
        raise ValueError("hidden swap benchmark requires at least four probes")

    root = Path(root_dir)
    root.mkdir(parents=True, exist_ok=True)
    history_reports: dict[str, Any] = {}
    overall = True

    for history in histories:
        control = build_developed_agent(
            cartridge_path,
            user_id=user_id,
            db_path=root / f"{history.history_id}-control.db",
            history=history,
        )
        candidate = build_developed_agent(
            cartridge_path,
            user_id=user_id,
            db_path=root / f"{history.history_id}-candidate.db",
            history=history,
        )
        external = ExternalChatRenderer(
            external_chat,
            provider_name="frontier-like-benchmark",
            model_name="frontier-like-benchmark",
        )

        turns: list[dict[str, Any]] = []
        surface_changes = 0
        history_passed = True
        for index, probe in enumerate(probes):
            control.engine.set_renderer(_offline_renderer())
            candidate.engine.set_renderer(external if index in {1, 2} else _offline_renderer())

            control_result = control.say(probe.text)
            candidate_result = candidate.say(probe.text)
            control_projection = semantic_projection(control, control_result)
            candidate_projection = semantic_projection(candidate, candidate_result)
            equal = control_projection == candidate_projection
            changed = control_result["response"] != candidate_result["response"]
            if index in {1, 2} and changed:
                surface_changes += 1
            history_passed = history_passed and equal
            turns.append(
                {
                    "probe_id": probe.probe_id,
                    "renderer": "external" if index in {1, 2} else "offline",
                    "semantic_projection_equal": equal,
                    "control_projection_digest": projection_digest(control_projection),
                    "candidate_projection_digest": projection_digest(candidate_projection),
                    "control_response": control_result["response"],
                    "candidate_response": candidate_result["response"],
                    "control_decision": dict(control_result.get("decision_payload", {})),
                    "candidate_decision": dict(candidate_result.get("decision_payload", {})),
                }
            )

        history_passed = history_passed and surface_changes > 0
        overall = overall and history_passed
        history_reports[history.history_id] = {
            "passed": history_passed,
            "surface_changes_on_external_turns": surface_changes,
            "turns": turns,
        }

    return {
        "schema_version": "wayfarer-renderer-benchmark-v1",
        "passed": overall,
        "history_count": len(histories),
        "probe_count": len(probes),
        "history_reports": history_reports,
    }
