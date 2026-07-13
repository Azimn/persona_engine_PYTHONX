"""Bounded private cognition proposal and application.

The proposal may come from a model, but only the structured, validated report
may influence runtime state.
"""

from __future__ import annotations

from dataclasses import asdict
import math
from typing import Any

from .cognition_schemas import CognitiveApplicationReport, Impulse, PrivateCognitionProposal
from .emotion import DECAY_PROFILES
from .intention import OpenLoop
from .renderer_contract import PrivateCognitionRequest, PrivateCognitionResult


MAX_PRESSURE_DELTA = 0.15

DEFAULT_THEME_RETRIEVAL_FILTERS: dict[str, dict[str, str]] = {
    "anticipate_betrayal": {"tag": "accusation"},
    "resist_dependence": {"tag": "intimacy_bid"},
    "probe_for_motive": {"tag": "neutral_turn"},
    "suppress_disclosure": {"tag": "identity_violation"},
}
ALLOWED_COGNITIVE_PRESSURES = set(DECAY_PROFILES) | {"suspicion"}


def _empty_proposal() -> PrivateCognitionProposal:
    return PrivateCognitionProposal(
        prose="",
        attention_targets=[],
        pressure_deltas={},
        impulse_candidates=[],
        memory_activation_requests=[],
        cognitive_theme_ids=[],
    )


def _proposal_from_mapping(data: dict[str, Any]) -> PrivateCognitionProposal:
    impulses = []
    for item in data.get("impulse_candidates", []) or []:
        if isinstance(item, Impulse):
            impulses.append(item)
        elif isinstance(item, dict):
            impulses.append(Impulse(
                type=str(item.get("type", "")),
                strength=float(item.get("strength", 0.0)),
                target=str(item.get("target", "")),
            ))
    return PrivateCognitionProposal(
        prose=str(data.get("prose", "")),
        attention_targets=[str(x) for x in data.get("attention_targets", []) or []],
        pressure_deltas={str(k): float(v) for k, v in (data.get("pressure_deltas", {}) or {}).items()},
        impulse_candidates=impulses,
        memory_activation_requests=[str(x) for x in data.get("memory_activation_requests", []) or []],
        cognitive_theme_ids=[str(x) for x in data.get("cognitive_theme_ids", []) or []],
    )


def generate_private_cognition(renderer, state_packet, cartridge) -> PrivateCognitionProposal:
    """Call the renderer's private-cognition task without touching state."""

    if hasattr(renderer, "generate_private_cognition"):
        try:
            raw = renderer.generate_private_cognition(PrivateCognitionRequest(
                ledger_digest={},
                active_state=dict(state_packet or {}),
                arc_context={},
                evidence=[],
                retrieved_memories=[],
                cartridge=dict(cartridge or {}),
            ))
        except TypeError:
            raw = renderer.generate_private_cognition(state_packet=state_packet, cartridge=cartridge)
        except Exception:
            raw = _empty_proposal()
    else:
        raw = _empty_proposal()
    if isinstance(raw, PrivateCognitionResult):
        return raw.proposal
    if isinstance(raw, PrivateCognitionProposal):
        return raw
    if isinstance(raw, dict):
        return _proposal_from_mapping(raw)
    return _empty_proposal()


def _allowed_themes(cartridge) -> set[str]:
    data = cartridge or {}
    section = data.get("cognitive_themes", {}) if isinstance(data, dict) else {}
    allowed = section.get("allowed", []) if isinstance(section, dict) else []
    return {str(item) for item in allowed}


def _theme_filters(cartridge) -> dict[str, dict[str, str]]:
    data = cartridge or {}
    section = data.get("cognitive_themes", {}) if isinstance(data, dict) else {}
    raw_filters = section.get("retrieval_filters", {}) if isinstance(section, dict) else {}
    filters = dict(DEFAULT_THEME_RETRIEVAL_FILTERS)
    if isinstance(raw_filters, dict):
        for key, value in raw_filters.items():
            if isinstance(value, dict):
                filters[str(key)] = {str(k): str(v) for k, v in value.items()}
    return filters


def _memory_ids_for_filter(memory, retrieval_filter: dict[str, str]) -> list[str]:
    tag = retrieval_filter.get("tag")
    if not tag:
        return []
    ids = []
    for mem in getattr(memory, "memories", []):
        if tag in getattr(mem, "tags", set()):
            ids.append(mem.id)
    return ids


def validate_and_apply(
    proposal: PrivateCognitionProposal,
    pressures,
    intentions,
    memory,
    cartridge,
    now: float,
) -> CognitiveApplicationReport:
    """Validate and apply bounded structured effects.

    This function never parses proposal prose and never mutates belief, memory,
    habit, world, relationship, identity, renderer, or UI state.
    """

    applied_pressure_deltas: dict[str, float] = {}
    rejected_pressure_deltas: dict[str, str] = {}
    for name, raw_delta in proposal.pressure_deltas.items():
        if str(name) not in ALLOWED_COGNITIVE_PRESSURES:
            rejected_pressure_deltas[str(name)] = "unknown pressure name"
            continue
        delta = float(raw_delta)
        if not math.isfinite(delta):
            rejected_pressure_deltas[str(name)] = "non-finite pressure delta"
            continue
        clamped = max(-MAX_PRESSURE_DELTA, min(MAX_PRESSURE_DELTA, delta))
        if clamped != delta:
            rejected_pressure_deltas[str(name)] = f"clamped from {delta:.3f} to {clamped:.3f}"
        pressure = pressures.ensure(str(name))
        pressure.magnitude = max(0.0, min(1.0, pressure.magnitude + clamped))
        applied_pressure_deltas[str(name)] = clamped

    accepted_impulses: list[Impulse] = []
    rejected_impulses: list[tuple[Impulse, str]] = []
    seen_impulses: set[str] = set()
    for impulse in proposal.impulse_candidates:
        raw_strength = float(impulse.strength)
        if not math.isfinite(raw_strength):
            rejected_impulses.append((Impulse(type=str(impulse.type), strength=0.0, target=str(impulse.target)), "non-finite impulse strength"))
            continue
        strength = max(0.0, min(1.0, raw_strength))
        normalized = Impulse(type=str(impulse.type), strength=strength, target=str(impulse.target))
        impulse_key = f"{normalized.type}:{normalized.target}"
        if impulse_key in seen_impulses:
            rejected_impulses.append((normalized, "duplicate impulse"))
            continue
        seen_impulses.add(impulse_key)
        if strength > 0.6 and normalized.type and normalized.target:
            accepted_impulses.append(normalized)
            intentions.add_open_loop(OpenLoop(
                topic=f"{normalized.type}:{normalized.target}",
                emotional_charge=strength,
                created_at=now,
                last_touched=now,
                urgency=strength,
                preferred_resolution="resolve through future visible evidence",
            ))
        else:
            rejected_impulses.append((normalized, "impulse below threshold or missing fields"))

    allowed = _allowed_themes(cartridge)
    accepted_theme_ids: list[str] = []
    rejected_theme_ids: list[tuple[str, str]] = []
    for theme_id in proposal.cognitive_theme_ids:
        if theme_id in allowed:
            accepted_theme_ids.append(theme_id)
        else:
            rejected_theme_ids.append((theme_id, "theme not allowed by cartridge"))

    filters = _theme_filters(cartridge)
    activated_memory_ids: list[str] = []
    unresolved_memory_requests: list[str] = []
    for request in proposal.memory_activation_requests:
        if request not in allowed or request not in filters:
            unresolved_memory_requests.append(request)
            continue
        activated_memory_ids.extend(_memory_ids_for_filter(memory, filters[request]))

    return CognitiveApplicationReport(
        applied_pressure_deltas=applied_pressure_deltas,
        rejected_pressure_deltas=rejected_pressure_deltas,
        accepted_impulses=accepted_impulses,
        rejected_impulses=rejected_impulses,
        activated_memory_ids=sorted(set(activated_memory_ids)),
        unresolved_memory_requests=unresolved_memory_requests,
        accepted_theme_ids=accepted_theme_ids,
        rejected_theme_ids=rejected_theme_ids,
    )


def report_to_dict(report: CognitiveApplicationReport) -> dict[str, Any]:
    return asdict(report)
