"""Crash-safe, versioned persistence for future-runtime operational state."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any


CURRENT_RUNTIME_SCHEMA = 1


class FutureRuntimePersistence:
    def __init__(self, root: str | Path):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.path = self.root / "future_runtime.json"

    def exists(self) -> bool:
        return self.path.exists()

    def load(self) -> dict[str, Any]:
        if not self.path.exists():
            return {}
        raw = json.loads(self.path.read_text(encoding="utf-8"))
        if not isinstance(raw, dict):
            raise ValueError("DUCK future runtime state must be a JSON object")
        # Tranches 1-5 wrote the payload directly. Treat that shape as schema 0
        # and migrate it in memory. The next save rewrites it as schema 1.
        if "schema_version" not in raw:
            return dict(raw)
        version = int(raw.get("schema_version", 0))
        if version > CURRENT_RUNTIME_SCHEMA:
            raise ValueError(
                f"DUCK future runtime schema {version} is newer than supported schema {CURRENT_RUNTIME_SCHEMA}"
            )
        if version < 1:
            return dict(raw.get("payload", {}))
        payload = raw.get("payload")
        if not isinstance(payload, dict):
            raise ValueError("DUCK future runtime payload must be a JSON object")
        return dict(payload)

    def save(self, payload: dict[str, Any]) -> None:
        if not isinstance(payload, dict):
            raise TypeError("DUCK future runtime payload must be a mapping")
        envelope = {
            "schema_version": CURRENT_RUNTIME_SCHEMA,
            "payload": payload,
        }
        temp = self.path.with_suffix(".json.tmp")
        encoded = json.dumps(envelope, indent=2, sort_keys=True) + "\n"
        with temp.open("w", encoding="utf-8") as handle:
            handle.write(encoded)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp, self.path)
