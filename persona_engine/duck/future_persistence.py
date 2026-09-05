"""Crash-safe persistence for future-runtime operational state."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any


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
        return dict(raw) if isinstance(raw, dict) else {}

    def save(self, payload: dict[str, Any]) -> None:
        temp = self.path.with_suffix(".json.tmp")
        encoded = json.dumps(payload, indent=2, sort_keys=True) + "\n"
        with temp.open("w", encoding="utf-8") as handle:
            handle.write(encoded)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp, self.path)
