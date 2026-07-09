"""Portable checksum-verified session snapshots."""

from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime, timezone
import hashlib
import json


class SessionImportError(ValueError):
    """Raised when a snapshot cannot be imported safely."""


@dataclass
class SessionSnapshot:
    entity_name: str
    variables: dict[str, float]
    beliefs: dict[str, float]
    last_updated: str
    schema_version: str = "1.0"
    checksum: str = ""


def compute_checksum(snap: SessionSnapshot) -> str:
    payload = {
        "variables": snap.variables,
        "beliefs": snap.beliefs,
        "last_updated": snap.last_updated,
        "entity_name": snap.entity_name,
    }
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()


def export_snapshot(pressure_system, belief_ledger, entity_name: str) -> SessionSnapshot:
    snap = SessionSnapshot(
        entity_name=entity_name,
        variables={name: p.magnitude for name, p in pressure_system.pressures.items()},
        beliefs=dict(belief_ledger.values),
        last_updated=datetime.now(timezone.utc).isoformat(),
    )
    snap.checksum = compute_checksum(snap)
    return snap


def snapshot_to_json(snap: SessionSnapshot) -> str:
    if not snap.checksum:
        snap.checksum = compute_checksum(snap)
    return json.dumps(asdict(snap), sort_keys=True, indent=2)


def snapshot_from_json(data: str) -> SessionSnapshot:
    raw = json.loads(data)
    return SessionSnapshot(**raw)


def import_snapshot(snap: SessionSnapshot, pressure_system, belief_ledger, entity_name: str) -> None:
    if snap.entity_name != entity_name:
        raise SessionImportError(f"snapshot entity {snap.entity_name!r} does not match target {entity_name!r}")
    if compute_checksum(snap) != snap.checksum:
        raise SessionImportError("snapshot checksum mismatch")
    for name, value in snap.variables.items():
        pressure_system.ensure(name).magnitude = float(value)
    belief_ledger.set_values({k: float(v) for k, v in snap.beliefs.items()})
