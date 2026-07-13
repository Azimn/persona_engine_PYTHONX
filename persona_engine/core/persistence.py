"""SQLite-backed persistence for all non-LLM state.

The storage is intentionally inspectable: each state family is saved as a JSON
blob under (character_id, user_id, key). This is durable enough for local
prototypes and avoids schema churn while the architecture is still changing.
"""

import json
import sqlite3
import time
from contextlib import contextmanager

from .deception_ledger import DeceptionLedger

SCHEMA = """
PRAGMA journal_mode=WAL;
CREATE TABLE IF NOT EXISTS state (
    character_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    key TEXT NOT NULL,
    value TEXT NOT NULL,
    updated_at REAL NOT NULL,
    PRIMARY KEY (character_id, user_id, key)
);
CREATE TABLE IF NOT EXISTS event_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    character_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    timestep INTEGER NOT NULL,
    event_type TEXT NOT NULL,
    payload TEXT NOT NULL,
    created_at REAL NOT NULL
);
"""


class Persistence:
    def __init__(self, path: str = "persona_state.db"):
        self.path = path
        with self._connection() as conn:
            conn.executescript(SCHEMA)

    def _connect(self):
        conn = sqlite3.connect(self.path, check_same_thread=False)
        conn.execute("PRAGMA foreign_keys=ON")
        return conn

    @contextmanager
    def _connection(self):
        conn = self._connect()
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    @property
    def conn(self):
        """Compatibility escape hatch for legacy read-only callers."""

        return self._connect()

    @contextmanager
    def transaction(self):
        conn = self._connect()
        try:
            yield
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def save(self, character_id: str, user_id: str, key: str, value):
        with self._connection() as conn:
            conn.execute(
                "INSERT INTO state (character_id, user_id, key, value, updated_at) VALUES (?,?,?,?,?) "
                "ON CONFLICT(character_id, user_id,key) DO UPDATE SET value=excluded.value, updated_at=excluded.updated_at",
                (character_id, user_id, key, json.dumps(value, ensure_ascii=False), time.time()),
            )

    def load(self, character_id: str, user_id: str, key: str, default=None):
        with self._connection() as conn:
            cur = conn.execute(
                "SELECT value FROM state WHERE character_id=? AND user_id=? AND key=?",
                (character_id, user_id, key),
            )
            row = cur.fetchone()
        return json.loads(row[0]) if row else default

    def save_deception_ledger(self, character_id: str, user_id: str, ledger: DeceptionLedger):
        self.save(character_id, user_id, "deception_ledger", ledger.to_state())

    def load_deception_ledger(self, character_id: str, user_id: str) -> DeceptionLedger:
        return DeceptionLedger.from_state(self.load(character_id, user_id, "deception_ledger", []))

    def save_many(self, character_id: str, user_id: str, items: dict):
        now = time.time()
        with self._connection() as conn:
            for key, value in items.items():
                conn.execute(
                    "INSERT INTO state (character_id, user_id, key, value, updated_at) VALUES (?,?,?,?,?) "
                    "ON CONFLICT(character_id,user_id,key) DO UPDATE SET value=excluded.value, updated_at=excluded.updated_at",
                    (character_id, user_id, key, json.dumps(value, ensure_ascii=False), now),
                )

    def log_event(self, character_id: str, user_id: str, timestep: int, event_type: str, payload: dict):
        with self._connection() as conn:
            conn.execute(
                "INSERT INTO event_log (character_id,user_id,timestep,event_type,payload,created_at) VALUES (?,?,?,?,?,?)",
                (character_id, user_id, timestep, event_type, json.dumps(payload, ensure_ascii=False), time.time()),
            )


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
        """Load event-log payloads created after a wall-clock timestamp."""
        if event_type is None:
            conn = self._connect()
            cur = conn.execute(
                "SELECT id,timestep,event_type,payload,created_at FROM event_log WHERE character_id=? AND user_id=? AND created_at>? ORDER BY created_at",
                (character_id, user_id, since),
            )
        else:
            conn = self._connect()
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

    def close(self):
        return None
