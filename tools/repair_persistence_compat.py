#!/usr/bin/env python3
"""Restore persistence compatibility methods lost during subject-reader edit."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "persona_engine" / "core" / "persistence.py"
text = PATH.read_text(encoding="utf-8")

old = '''    def integrity_check(self) -> str:
        with self._connection() as conn:
            row = conn.execute("PRAGMA integrity_check").fetchone()
        return str(row[0]) if row else "unknown"
'''
new = '''    # ---------------- legacy event-log readers ----------------
    def event_counts_since(self, character_id: str, user_id: str, since: float) -> dict[str, int]:
        """Count evidence types logged after the supplied wall-clock timestamp."""
        conn = self._connect()
        cur = conn.execute(
            "SELECT event_type, payload FROM event_log WHERE character_id=? AND user_id=? AND created_at>?",
            (character_id, user_id, since),
        )
        counts: dict[str, int] = {}
        try:
            for event_type, payload_text in cur.fetchall():
                try:
                    payload = json.loads(payload_text)
                except json.JSONDecodeError:
                    payload = {}
                types = []
                if isinstance(payload, dict):
                    if payload.get("trigger_memory_type"):
                        types.append(str(payload["trigger_memory_type"]))
                    for item in payload.get("memory_types", []) or []:
                        types.append(str(item))
                if not types:
                    types.append(str(event_type))
                for item in types:
                    counts[item] = counts.get(item, 0) + 1
            return counts
        finally:
            conn.close()

    def load_events_since(self, character_id: str, user_id: str, since: float, event_type: str | None = None) -> list[dict]:
        """Load diagnostic event-log payloads created after a wall-clock timestamp."""
        conn = self._connect()
        if event_type is None:
            cur = conn.execute(
                "SELECT id,timestep,event_type,payload,created_at FROM event_log WHERE character_id=? AND user_id=? AND created_at>? ORDER BY created_at",
                (character_id, user_id, since),
            )
        else:
            cur = conn.execute(
                "SELECT id,timestep,event_type,payload,created_at FROM event_log WHERE character_id=? AND user_id=? AND created_at>? AND event_type=? ORDER BY created_at",
                (character_id, user_id, since, event_type),
            )
        rows = []
        try:
            for event_id, timestep, ev_type, payload_text, created_at in cur.fetchall():
                try:
                    payload = json.loads(payload_text)
                except json.JSONDecodeError:
                    payload = {}
                rows.append({"id": event_id, "timestep": timestep, "event_type": ev_type, "payload": payload, "created_at": created_at})
            return rows
        finally:
            conn.close()

    def integrity_check(self) -> str:
        with self._connection() as conn:
            row = conn.execute("PRAGMA integrity_check").fetchone()
        return str(row[0]) if row else "unknown"

    def sqlite_integrity_check(self) -> str:
        """Backward-compatible name used by continuity tests and callers."""
        return self.integrity_check()

    def close(self):
        return None
'''
if old not in text or text.count(old) != 1:
    raise RuntimeError("persistence compatibility anchor missing or ambiguous")
PATH.write_text(text.replace(old, new, 1), encoding="utf-8")
print("Restored persistence compatibility methods")
