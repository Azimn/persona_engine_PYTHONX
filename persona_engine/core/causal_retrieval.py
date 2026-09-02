"""Experimental bounded association retrieval over canonical continuity links.

This module deliberately does not create a graph database or infer new links.
It consumes only causal parent identifiers already present in continuity events
and expands from explicitly supplied seed events by one hop.

The experiment asks a narrow question: can Wayfarer recover semantically distant
but causally adjacent lived evidence without adding a second memory authority?
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Iterable


@dataclass(frozen=True)
class CausalNeighbor:
    event_uuid: str
    seed_event_uuid: str
    relation: str
    subject_sequence: int
    event_type: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _event_uuid(event: dict[str, Any]) -> str:
    return str(event.get("event_uuid", "")).strip()


def _subject_uuid(event: dict[str, Any]) -> str:
    return str(event.get("subject_uuid", "")).strip()


def _sequence(event: dict[str, Any]) -> int:
    value = event.get("subject_sequence", event.get("sequence", 0))
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def _parents(event: dict[str, Any]) -> tuple[str, ...]:
    value = event.get("causal_parents", ())
    if not isinstance(value, (list, tuple)):
        return ()
    return tuple(str(item).strip() for item in value if str(item).strip())


def expand_causal_neighbors(
    events: Iterable[dict[str, Any]],
    seed_event_ids: Iterable[str],
    *,
    max_neighbors: int = 2,
) -> list[CausalNeighbor]:
    """Return a tiny deterministic one-hop causal neighborhood.

    Only existing canonical events are eligible. A neighbor must belong to the
    same subject as its seed. Both direct parents and direct children are
    considered, but traversal never proceeds beyond one edge and seeds are never
    returned as their own neighbors.

    The function is intentionally retrieval-only. It does not infer causality,
    mutate continuity, promote cold events into resident memory, or alter any
    authority decision.
    """

    limit = max(0, int(max_neighbors))
    if limit == 0:
        return []

    eligible: dict[str, dict[str, Any]] = {}
    for event in events:
        if not isinstance(event, dict):
            continue
        event_id = _event_uuid(event)
        if not event_id:
            continue
        canonicality = str(event.get("canonicality", "canonical_event"))
        if canonicality != "canonical_event":
            continue
        eligible[event_id] = event

    children: dict[str, list[dict[str, Any]]] = {}
    for event in eligible.values():
        for parent_id in _parents(event):
            children.setdefault(parent_id, []).append(event)

    seen: set[str] = set()
    candidates: list[CausalNeighbor] = []
    for seed_raw in seed_event_ids:
        seed_id = str(seed_raw).strip()
        seed = eligible.get(seed_id)
        if seed is None:
            continue
        seed_subject = _subject_uuid(seed)

        for parent_id in _parents(seed):
            parent = eligible.get(parent_id)
            if parent is None or parent_id in seen or parent_id == seed_id:
                continue
            if _subject_uuid(parent) != seed_subject:
                continue
            seen.add(parent_id)
            candidates.append(CausalNeighbor(
                event_uuid=parent_id,
                seed_event_uuid=seed_id,
                relation="parent",
                subject_sequence=_sequence(parent),
                event_type=str(parent.get("event_type", "")),
            ))

        for child in children.get(seed_id, []):
            child_id = _event_uuid(child)
            if not child_id or child_id in seen or child_id == seed_id:
                continue
            if _subject_uuid(child) != seed_subject:
                continue
            seen.add(child_id)
            candidates.append(CausalNeighbor(
                event_uuid=child_id,
                seed_event_uuid=seed_id,
                relation="child",
                subject_sequence=_sequence(child),
                event_type=str(child.get("event_type", "")),
            ))

    relation_rank = {"parent": 0, "child": 1}
    candidates.sort(
        key=lambda item: (
            relation_rank.get(item.relation, 9),
            -item.subject_sequence,
            item.seed_event_uuid,
            item.event_uuid,
        )
    )
    return candidates[:limit]
