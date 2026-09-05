"""DUCK organism checkpoint and append-only cycle evidence."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any

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

    def find_expression(self, speech_id: str) -> dict[str, Any] | None:
        """Recover a realized utterance from durable trace evidence.

        This is intentionally a cold-path linear scan. Recent expressions live in
        the bounded hot journal; an evicted expression only pays this cost when an
        exact historical replay is requested.
        """
        if not self.event_log_path.exists():
            return None
        target = str(speech_id)
        found: dict[str, Any] | None = None
        with self.event_log_path.open("r", encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, start=1):
                if not line.strip():
                    continue
                try:
                    trace = json.loads(line)
                except json.JSONDecodeError as exc:
                    raise ValueError(
                        f"DUCK event log contains invalid JSON at line {line_number}"
                    ) from exc
                outcome = trace.get("outcome", {}) if isinstance(trace, dict) else {}
                execution = outcome.get("execution", {}) if isinstance(outcome, dict) else {}
                metadata = execution.get("metadata", {}) if isinstance(execution, dict) else {}
                if str(metadata.get("speech_id", "")) != target:
                    continue
                expression = metadata.get("expression")
                if isinstance(expression, dict):
                    found = dict(expression)
        return found
