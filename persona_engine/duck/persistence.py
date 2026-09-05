"""DUCK organism checkpoint and append-only cycle evidence."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

from .types import CycleTrace, OrganismState


class DuckPersistence:
    def __init__(self, root: str | Path):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.checkpoint_path = self.root / "organism.json"
        self.event_log_path = self.root / "events.jsonl"

    @staticmethod
    def digest_state(state: OrganismState) -> str:
        encoded = json.dumps(state.to_dict(), sort_keys=True, separators=(",", ":")).encode("utf-8")
        return hashlib.sha256(encoded).hexdigest()

    def save(self, state: OrganismState) -> str:
        payload = state.to_dict()
        payload["state_sha256"] = self.digest_state(state)
        encoded = json.dumps(payload, indent=2, sort_keys=True) + "\n"
        temporary = self.checkpoint_path.with_suffix(".json.tmp")
        with temporary.open("w", encoding="utf-8") as handle:
            handle.write(encoded)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, self.checkpoint_path)
        return payload["state_sha256"]

    def load(self) -> OrganismState:
        raw = json.loads(self.checkpoint_path.read_text(encoding="utf-8"))
        expected = raw.pop("state_sha256", None)
        state = OrganismState.from_dict(raw)
        actual = self.digest_state(state)
        if expected and expected != actual:
            raise ValueError("DUCK checkpoint digest mismatch")
        return state

    def append_trace(self, trace: CycleTrace) -> None:
        with self.event_log_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(trace.to_dict(), sort_keys=True) + "\n")
            handle.flush()
            os.fsync(handle.fileno())
