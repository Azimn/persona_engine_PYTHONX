"""SQLite persistence for Wayfarer character state and continuity evidence.

The legacy ``event_log`` remains a broad diagnostic journal during M3 migration.
The new ``continuity_event`` table is narrower: only events admitted by the
fail-closed canonicality policy enter the character's canonical lived history.

The default local profile is append-only and sequence-validated. It intentionally
does not use a per-event cryptographic previous-hash chain.
"""

from __future__ import annotations

import json
import sqlite3
import time
import uuid
from contextlib import contextmanager
from typing import Any

from .continuity import (
    CONTINUITY_SCHEMA_VERSION,
    STATE_DIGEST_SCHEMA_VERSION,
    ContinuityEvent,
    ContinuityIntegrityReport,
    canonical_continuity_eligible,
    event_authority,
    state_digest,
)
from .deception_ledger import DeceptionLedger

# Operational telemetry is not character cognition. The normal runtime keeps a
# recent diagnostic window for debugging while direct Persistence callers retain
# the legacy unlimited default for migration and tooling compatibility.
DEFAULT_RUNTIME_DIAGNOSTIC_EVENT_LIMIT = 512


def _extract_evidence_types(event_type: str, payload: dict[str, Any]) -> list[str]:
    """Return the exact semantic counters consumed by slow consolidation."""

    types: list[str] = []
    trigger = payload.get("trigger_memory_type") if isinstance(payload, dict) else None
    if trigger:
        types.append(str(trigger))
    if isinstance(payload, dict):
        for item in payload.get("memory_types", []) or []:
            types.append(str(item))
    if not types:
        types.append(str(event_type))
    return types


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
CREATE TABLE IF NOT EXISTS subject_state (
    subject_uuid TEXT NOT NULL,
    key TEXT NOT NULL,
    value TEXT NOT NULL,
    updated_at REAL NOT NULL,
    PRIMARY KEY (subject_uuid, key)
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
CREATE TABLE IF NOT EXISTS consolidation_evidence (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    legacy_event_id INTEGER NOT NULL UNIQUE,
    character_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    evidence_types TEXT NOT NULL,
    created_at REAL NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_consolidation_evidence_stream_time
    ON consolidation_evidence(character_id, user_id, created_at);
CREATE TABLE IF NOT EXISTS continuity_subject (
    character_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    subject_uuid TEXT NOT NULL,
    continuity_epoch INTEGER NOT NULL DEFAULT 0,
    updated_at REAL NOT NULL,
    PRIMARY KEY (character_id, user_id)
);
CREATE TABLE IF NOT EXISTS continuity_event (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_uuid TEXT NOT NULL UNIQUE,
    subject_uuid TEXT NOT NULL,
    character_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    sequence INTEGER NOT NULL,
    subject_sequence INTEGER,
    continuity_epoch INTEGER NOT NULL DEFAULT 0,
    subject_time REAL NOT NULL,
    wall_time REAL NOT NULL,
    source_actor TEXT NOT NULL,
    source_class TEXT NOT NULL,
    authority_class TEXT NOT NULL,
    event_type TEXT NOT NULL,
    visibility TEXT NOT NULL,
    canonicality TEXT NOT NULL,
    causal_parents TEXT NOT NULL,
    payload_schema TEXT NOT NULL,
    payload TEXT NOT NULL,
    legacy_event_id INTEGER UNIQUE,
    UNIQUE(subject_uuid, user_id, continuity_epoch, sequence)
);
CREATE INDEX IF NOT EXISTS idx_continuity_subject_sequence
    ON continuity_event(subject_uuid, user_id, continuity_epoch, sequence);
CREATE TABLE IF NOT EXISTS continuity_checkpoint (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    subject_uuid TEXT NOT NULL,
    character_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    continuity_epoch INTEGER NOT NULL,
    sequence INTEGER NOT NULL,
    state_schema TEXT NOT NULL,
    state_digest TEXT NOT NULL,
    created_at REAL NOT NULL,
    UNIQUE(subject_uuid, user_id, continuity_epoch,sequence)
);
"""


class ContinuityImportError(ValueError):
    """Raised when an imported canonical event tail violates continuity rules."""


class Persistence:
    def __init__(self, path: str = "persona_state.db", diagnostic_event_limit: int | None = None):
        self.path = path
        self.diagnostic_event_limit = None if diagnostic_event_limit is None else max(1, int(diagnostic_event_limit))
        # Operational hysteresis: avoid a SELECT/DELETE maintenance cycle on
        # every logged event. Small limits still prune every event; the normal
        # 512-row runtime window amortizes maintenance across 128 writes.
        self._diagnostic_writes_since_prune: dict[tuple[str, str], int] = {}
        self._subject_bindings: dict[tuple[str, str], tuple[str, int]] = {}
        with self._connection() as conn:
            conn.executescript(SCHEMA)
            self._ensure_subject_sequence_schema_conn(conn)
            # Migrate semantic consolidation evidence before any runtime is
            # allowed to prune verbose legacy diagnostics. Source event ids make
            # this idempotent across interrupted upgrades and repeated startups.
            self._backfill_consolidation_evidence_conn(conn)

    def _ensure_subject_sequence_schema_conn(self, conn) -> None:
        """Add/backfill the subject-owned ordinal without changing stream sequence.

        Existing databases predate ``subject_sequence``. Their canonical rows
        are deterministically ordered by recorded wall time then insertion id
        for the one-time migration. New events allocate the next ordinal inside
        the same SQLite transaction as the canonical insert.
        """

        columns = {str(row[1]) for row in conn.execute("PRAGMA table_info(continuity_event)").fetchall()}
        if "subject_sequence" not in columns:
            conn.execute("ALTER TABLE continuity_event ADD COLUMN subject_sequence INTEGER")
            groups = conn.execute(
                "SELECT DISTINCT subject_uuid,continuity_epoch FROM continuity_event ORDER BY subject_uuid,continuity_epoch"
            ).fetchall()
            for subject_uuid, epoch in groups:
                rows = conn.execute(
                    "SELECT id FROM continuity_event WHERE subject_uuid=? AND continuity_epoch=? ORDER BY wall_time,id",
                    (subject_uuid, epoch),
                ).fetchall()
                for ordinal, (row_id,) in enumerate(rows, start=1):
                    conn.execute(
                        "UPDATE continuity_event SET subject_sequence=? WHERE id=?",
                        (ordinal, row_id),
                    )
        else:
            groups = conn.execute(
                "SELECT DISTINCT subject_uuid,continuity_epoch FROM continuity_event WHERE subject_sequence IS NULL ORDER BY subject_uuid,continuity_epoch"
            ).fetchall()
            for subject_uuid, epoch in groups:
                row = conn.execute(
                    "SELECT COALESCE(MAX(subject_sequence),0) FROM continuity_event WHERE subject_uuid=? AND continuity_epoch=?",
                    (subject_uuid, epoch),
                ).fetchone()
                next_ordinal = int(row[0] or 0) + 1
                rows = conn.execute(
                    "SELECT id FROM continuity_event WHERE subject_uuid=? AND continuity_epoch=? AND subject_sequence IS NULL ORDER BY wall_time,id",
                    (subject_uuid, epoch),
                ).fetchall()
                for offset, (row_id,) in enumerate(rows):
                    conn.execute(
                        "UPDATE continuity_event SET subject_sequence=? WHERE id=?",
                        (next_ordinal + offset, row_id),
                    )
        conn.execute(
            "CREATE UNIQUE INDEX IF NOT EXISTS idx_continuity_subject_global_sequence "
            "ON continuity_event(subject_uuid,continuity_epoch,subject_sequence) "
            "WHERE subject_sequence IS NOT NULL"
        )

    def _backfill_consolidation_evidence_conn(self, conn) -> int:
        """Copy compact semantic evidence from any legacy diagnostic rows once."""

        rows = conn.execute(
            "SELECT e.id,e.character_id,e.user_id,e.event_type,e.payload,e.created_at "
            "FROM event_log e LEFT JOIN consolidation_evidence c ON c.legacy_event_id=e.id "
            "WHERE c.legacy_event_id IS NULL ORDER BY e.id"
        ).fetchall()
        inserted = 0
        for event_id, character_id, user_id, event_type, payload_text, created_at in rows:
            try:
                payload = json.loads(payload_text)
            except (json.JSONDecodeError, TypeError):
                payload = {}
            if not isinstance(payload, dict):
                payload = {}
            types = _extract_evidence_types(str(event_type), payload)
            conn.execute(
                "INSERT OR IGNORE INTO consolidation_evidence "
                "(legacy_event_id,character_id,user_id,evidence_types,created_at) VALUES(?,?,?,?,?)",
                (int(event_id), str(character_id), str(user_id), json.dumps(types, ensure_ascii=False), float(created_at)),
            )
            inserted += 1
        return inserted

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
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    # ---------------- subject identity / epoch ----------------
    def bind_subject(
        self,
        character_id: str,
        user_id: str,
        subject_uuid: str,
        continuity_epoch: int = 0,
    ) -> None:
        """Bind a persistence stream to the permanent portable subject UUID."""

        subject_uuid = str(subject_uuid or "").strip()
        if not subject_uuid:
            raise ValueError("bind_subject requires a non-empty permanent subject UUID")
        try:
            uuid.UUID(subject_uuid)
        except ValueError as exc:
            raise ValueError(f"invalid subject UUID: {subject_uuid}") from exc
        continuity_epoch = max(0, int(continuity_epoch))
        key = (str(character_id), str(user_id))
        self._subject_bindings[key] = (subject_uuid, continuity_epoch)
        with self._connection() as conn:
            conn.execute(
                "INSERT INTO continuity_subject(character_id,user_id,subject_uuid,continuity_epoch,updated_at) VALUES(?,?,?,?,?) "
                "ON CONFLICT(character_id,user_id) DO UPDATE SET subject_uuid=excluded.subject_uuid, continuity_epoch=excluded.continuity_epoch, updated_at=excluded.updated_at",
                (character_id, user_id, subject_uuid, continuity_epoch, time.time()),
            )
        if self.diagnostic_event_limit is not None:
            # A pre-M3 database may contain canonical experiences only in the
            # legacy journal. Admit them to continuity before telemetry pruning.
            self.backfill_legacy_events(character_id, user_id)
            self.prune_diagnostic_events(character_id, user_id)

    def _resolve_subject(self, character_id: str, user_id: str) -> tuple[str, int]:
        key = (str(character_id), str(user_id))
        if key in self._subject_bindings:
            return self._subject_bindings[key]
        with self._connection() as conn:
            row = conn.execute(
                "SELECT subject_uuid,continuity_epoch FROM continuity_subject WHERE character_id=? AND user_id=?",
                (character_id, user_id),
            ).fetchone()
        if row:
            resolved = (str(row[0]), int(row[1]))
            self._subject_bindings[key] = resolved
            return resolved
        # Compatibility fallback for direct Persistence users. InteriorEngine is
        # expected to bind the actual .snp entity_uuid during initialization.
        fallback = str(uuid.uuid5(uuid.NAMESPACE_URL, f"wayfarer-legacy-subject:{character_id}"))
        resolved = (fallback, 0)
        self._subject_bindings[key] = resolved
        return resolved

    # ---------------- state snapshots ----------------
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

    def save_subject(self, character_id: str, user_id: str, key: str, value) -> None:
        """Persist one explicitly subject-owned snapshot value.

        This table is a current-state cache, not canonical event authority. The
        engine decides which semantic families are allowed to use subject scope.
        """

        subject_uuid, _ = self._resolve_subject(character_id, user_id)
        with self._connection() as conn:
            conn.execute(
                "INSERT INTO subject_state(subject_uuid,key,value,updated_at) VALUES(?,?,?,?) "
                "ON CONFLICT(subject_uuid,key) DO UPDATE SET value=excluded.value, updated_at=excluded.updated_at",
                (subject_uuid, key, json.dumps(value, ensure_ascii=False), time.time()),
            )

    def load_subject(self, character_id: str, user_id: str, key: str, default=None):
        """Load one explicitly subject-owned snapshot value by permanent UUID."""

        subject_uuid, _ = self._resolve_subject(character_id, user_id)
        with self._connection() as conn:
            row = conn.execute(
                "SELECT value FROM subject_state WHERE subject_uuid=? AND key=?",
                (subject_uuid, key),
            ).fetchone()
        return json.loads(row[0]) if row else default

    def save_subject_many(self, character_id: str, user_id: str, items: dict) -> None:
        """Persist a small explicit set of subject-owned snapshot values."""

        subject_uuid, _ = self._resolve_subject(character_id, user_id)
        now = time.time()
        with self._connection() as conn:
            for key, value in items.items():
                conn.execute(
                    "INSERT INTO subject_state(subject_uuid,key,value,updated_at) VALUES(?,?,?,?) "
                    "ON CONFLICT(subject_uuid,key) DO UPDATE SET value=excluded.value, updated_at=excluded.updated_at",
                    (subject_uuid, key, json.dumps(value, ensure_ascii=False), now),
                )

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

    # ---------------- diagnostic + canonical event logging ----------------
    def _prune_diagnostic_events_conn(self, conn, character_id: str, user_id: str) -> int:
        limit = self.diagnostic_event_limit
        if limit is None:
            return 0
        cutoff = conn.execute(
            "SELECT id FROM event_log WHERE character_id=? AND user_id=? ORDER BY id DESC LIMIT 1 OFFSET ?",
            (character_id, user_id, max(0, int(limit) - 1)),
        ).fetchone()
        if not cutoff:
            return 0
        cur = conn.execute(
            "DELETE FROM event_log WHERE character_id=? AND user_id=? AND id<?",
            (character_id, user_id, int(cutoff[0])),
        )
        return max(0, int(cur.rowcount or 0))

    def _diagnostic_prune_stride(self) -> int:
        limit = self.diagnostic_event_limit
        if limit is None:
            return 0
        return max(1, min(128, max(1, int(limit) // 4)))

    def prune_diagnostic_events(self, character_id: str, user_id: str) -> int:
        """Bound recent operational telemetry without touching lived history."""

        with self._connection() as conn:
            removed = self._prune_diagnostic_events_conn(conn, character_id, user_id)
        self._diagnostic_writes_since_prune[(str(character_id), str(user_id))] = 0
        return removed

    def prune_consolidation_evidence(self, character_id: str, user_id: str, through: float) -> int:
        """Discard semantic evidence already committed into the belief ledger."""

        with self._connection() as conn:
            cur = conn.execute(
                "DELETE FROM consolidation_evidence WHERE character_id=? AND user_id=? AND created_at<=?",
                (character_id, user_id, float(through)),
            )
            return max(0, int(cur.rowcount or 0))

    def log_event(self, character_id: str, user_id: str, timestep: int, event_type: str, payload: dict):
        """Write the broad diagnostic log and, when eligible, canonical continuity."""

        now = time.time()
        payload = dict(payload or {})
        with self._connection() as conn:
            cur = conn.execute(
                "INSERT INTO event_log (character_id,user_id,timestep,event_type,payload,created_at) VALUES (?,?,?,?,?,?)",
                (character_id, user_id, timestep, event_type, json.dumps(payload, ensure_ascii=False), now),
            )
            legacy_id = int(cur.lastrowid)
            conn.execute(
                "INSERT INTO consolidation_evidence "
                "(legacy_event_id,character_id,user_id,evidence_types,created_at) VALUES(?,?,?,?,?)",
                (legacy_id, character_id, user_id, json.dumps(_extract_evidence_types(event_type, payload), ensure_ascii=False), now),
            )
            if canonical_continuity_eligible(event_type, payload):
                self._append_continuity_event_conn(
                    conn,
                    character_id=character_id,
                    user_id=user_id,
                    timestep=timestep,
                    event_type=event_type,
                    payload=payload,
                    wall_time=now,
                    legacy_event_id=legacy_id,
                )
            if self.diagnostic_event_limit is not None:
                key = (str(character_id), str(user_id))
                writes = self._diagnostic_writes_since_prune.get(key, 0) + 1
                stride = self._diagnostic_prune_stride()
                if writes >= stride:
                    self._prune_diagnostic_events_conn(conn, character_id, user_id)
                    writes = 0
                self._diagnostic_writes_since_prune[key] = writes

    def _next_sequence_conn(self, conn, subject_uuid: str, user_id: str, continuity_epoch: int) -> int:
        row = conn.execute(
            "SELECT COALESCE(MAX(sequence),0) FROM continuity_event WHERE subject_uuid=? AND user_id=? AND continuity_epoch=?",
            (subject_uuid, user_id, continuity_epoch),
        ).fetchone()
        return int(row[0] or 0) + 1

    def _next_subject_sequence_conn(self, conn, subject_uuid: str, continuity_epoch: int) -> int:
        row = conn.execute(
            "SELECT COALESCE(MAX(subject_sequence),0) FROM continuity_event WHERE subject_uuid=? AND continuity_epoch=?",
            (subject_uuid, continuity_epoch),
        ).fetchone()
        return int(row[0] or 0) + 1

    def _append_continuity_event_conn(
        self,
        conn,
        *,
        character_id: str,
        user_id: str,
        timestep: int,
        event_type: str,
        payload: dict[str, Any],
        wall_time: float,
        legacy_event_id: int | None,
        event_uuid: str | None = None,
        continuity_epoch: int | None = None,
        sequence: int | None = None,
        source_actor: str | None = None,
        source_class: str | None = None,
        authority_class: str | None = None,
        visibility: str | None = None,
        causal_parents: list[str] | tuple[str, ...] | None = None,
        payload_schema: str | None = None,
    ) -> ContinuityEvent:
        subject_uuid, bound_epoch = self._resolve_subject(character_id, user_id)
        epoch = bound_epoch if continuity_epoch is None else max(0, int(continuity_epoch))
        sequence = sequence or self._next_sequence_conn(conn, subject_uuid, user_id, epoch)
        subject_sequence = self._next_subject_sequence_conn(conn, subject_uuid, epoch)
        authority = event_authority(event_type, payload)
        event_uuid = event_uuid or str(uuid.uuid4())
        parents = tuple(str(item) for item in (causal_parents if causal_parents is not None else payload.get("causal_parents", ())) if str(item))
        schema = str(payload_schema or payload.get("payload_schema") or "legacy-event-v1")
        event = ContinuityEvent(
            event_uuid=event_uuid,
            subject_uuid=subject_uuid,
            character_id=str(character_id),
            user_id=str(user_id),
            sequence=int(sequence),
            continuity_epoch=epoch,
            subject_time=float(timestep),
            wall_time=float(wall_time),
            source_actor=str(source_actor or authority.source_actor),
            source_class=str(source_class or authority.source_class),
            authority_class=str(authority_class or authority.authority_class),
            event_type=str(event_type),
            visibility=str(visibility or authority.visibility),
            canonicality="canonical_event",
            causal_parents=parents,
            payload_schema=schema,
            payload=dict(payload),
            legacy_event_id=legacy_event_id,
        )
        conn.execute(
            "INSERT INTO continuity_event(event_uuid,subject_uuid,character_id,user_id,sequence,subject_sequence,continuity_epoch,subject_time,wall_time,source_actor,source_class,authority_class,event_type,visibility,canonicality,causal_parents,payload_schema,payload,legacy_event_id) "
            "VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                event.event_uuid,
                event.subject_uuid,
                event.character_id,
                event.user_id,
                event.sequence,
                subject_sequence,
                event.continuity_epoch,
                event.subject_time,
                event.wall_time,
                event.source_actor,
                event.source_class,
                event.authority_class,
                event.event_type,
                event.visibility,
                event.canonicality,
                json.dumps(list(event.causal_parents), ensure_ascii=False),
                event.payload_schema,
                json.dumps(event.payload, ensure_ascii=False),
                event.legacy_event_id,
            ),
        )
        return event

    @staticmethod
    def _continuity_row_to_dict(row) -> dict[str, Any]:
        return {
            "event_uuid": row[0], "subject_uuid": row[1], "character_id": row[2], "user_id": row[3],
            "sequence": row[4], "subject_sequence": row[5], "continuity_epoch": row[6], "subject_time": row[7], "wall_time": row[8],
            "source_actor": row[9], "source_class": row[10], "authority_class": row[11], "event_type": row[12],
            "visibility": row[13], "canonicality": row[14], "causal_parents": json.loads(row[15]),
            "payload_schema": row[16], "payload": json.loads(row[17]), "legacy_event_id": row[18],
        }

    def load_continuity_events(
        self,
        character_id: str,
        user_id: str,
        *,
        after_sequence: int = 0,
        continuity_epoch: int | None = None,
    ) -> list[dict[str, Any]]:
        subject_uuid, bound_epoch = self._resolve_subject(character_id, user_id)
        epoch = bound_epoch if continuity_epoch is None else int(continuity_epoch)
        with self._connection() as conn:
            rows = conn.execute(
                "SELECT event_uuid,subject_uuid,character_id,user_id,sequence,subject_sequence,continuity_epoch,subject_time,wall_time,source_actor,source_class,authority_class,event_type,visibility,canonicality,causal_parents,payload_schema,payload,legacy_event_id "
                "FROM continuity_event WHERE subject_uuid=? AND user_id=? AND continuity_epoch=? AND sequence>? ORDER BY sequence",
                (subject_uuid, user_id, epoch, int(after_sequence)),
            ).fetchall()
        return [self._continuity_row_to_dict(row) for row in rows]

    def iter_continuity_events(
        self,
        character_id: str,
        user_id: str,
        *,
        after_sequence: int = 0,
        continuity_epoch: int | None = None,
        event_type: str | None = None,
    ):
        """Stream one interlocutor's canonical history without materializing it.

        This is the low-memory archive read seam. The permanent subject binding
        still anchors the stream, while ``user_id`` remains an explicit provenance
        boundary so cold recall cannot leak another interlocutor's private history.
        """

        subject_uuid, bound_epoch = self._resolve_subject(character_id, user_id)
        epoch = bound_epoch if continuity_epoch is None else int(continuity_epoch)
        query = (
            "SELECT event_uuid,subject_uuid,character_id,user_id,sequence,subject_sequence,continuity_epoch,subject_time,wall_time,source_actor,source_class,authority_class,event_type,visibility,canonicality,causal_parents,payload_schema,payload,legacy_event_id "
            "FROM continuity_event WHERE subject_uuid=? AND user_id=? AND continuity_epoch=? AND sequence>?"
        )
        params: list[Any] = [subject_uuid, user_id, epoch, int(after_sequence)]
        if event_type is not None:
            query += " AND event_type=?"
            params.append(str(event_type))
        query += " ORDER BY sequence"
        conn = self._connect()
        try:
            cursor = conn.execute(query, tuple(params))
            for row in cursor:
                yield self._continuity_row_to_dict(row)
        finally:
            conn.close()

    def load_subject_continuity_events(
        self,
        character_id: str,
        user_id: str,
        *,
        continuity_epoch: int | None = None,
        event_type: str | None = None,
    ) -> list[dict[str, Any]]:
        """Read canonical events owned by the subject across interlocutor views.

        ``user_id`` is used only to resolve the permanent subject binding. It is
        intentionally not part of the event filter. The event's own ``user_id``
        remains available as provenance so relationship/social meaning can stay
        actor-specific.

        The existing ``sequence`` remains a per-interlocutor compatibility stream.
        ``subject_sequence`` is the additive subject-owned canonical ordinal and is
        therefore the ordering key for this cross-interlocutor reader.
        """

        subject_uuid, bound_epoch = self._resolve_subject(character_id, user_id)
        epoch = bound_epoch if continuity_epoch is None else int(continuity_epoch)
        query = (
            "SELECT event_uuid,subject_uuid,character_id,user_id,sequence,subject_sequence,continuity_epoch,subject_time,wall_time,source_actor,source_class,authority_class,event_type,visibility,canonicality,causal_parents,payload_schema,payload,legacy_event_id "
            "FROM continuity_event WHERE subject_uuid=? AND continuity_epoch=?"
        )
        params: list[Any] = [subject_uuid, epoch]
        if event_type is not None:
            query += " AND event_type=?"
            params.append(str(event_type))
        query += " ORDER BY subject_sequence"
        with self._connection() as conn:
            rows = conn.execute(query, tuple(params)).fetchall()
        return [self._continuity_row_to_dict(row) for row in rows]

    def validate_continuity(self, character_id: str, user_id: str, continuity_epoch: int | None = None) -> ContinuityIntegrityReport:
        subject_uuid, _ = self._resolve_subject(character_id, user_id)
        events = self.load_continuity_events(character_id, user_id, after_sequence=0, continuity_epoch=continuity_epoch)
        sequences = [int(event["sequence"]) for event in events]
        missing: list[int] = []
        if sequences:
            expected = set(range(1, max(sequences) + 1))
            missing = sorted(expected - set(sequences))
        malformed: list[str] = []
        mismatches: list[str] = []
        for event in events:
            if event["subject_uuid"] != subject_uuid:
                mismatches.append(str(event["event_uuid"]))
            if event["canonicality"] != "canonical_event" or not isinstance(event["payload"], dict):
                malformed.append(str(event["event_uuid"]))
        return ContinuityIntegrityReport(
            ok=not missing and not malformed and not mismatches,
            event_count=len(events),
            first_sequence=min(sequences) if sequences else None,
            last_sequence=max(sequences) if sequences else None,
            missing_sequences=missing,
            malformed_events=malformed,
            subject_mismatches=mismatches,
        )

    def export_continuity_tail(self, character_id: str, user_id: str, after_sequence: int = 0) -> dict[str, Any]:
        subject_uuid, epoch = self._resolve_subject(character_id, user_id)
        events = self.load_continuity_events(character_id, user_id, after_sequence=int(after_sequence), continuity_epoch=epoch)
        # v1 interchange remains the established per-interlocutor stream contract.
        # The additive subject ordinal stays local until a subject-wide transfer
        # experiment earns a versioned portable representation for it.
        export_events = [{key: value for key, value in event.items() if key != "subject_sequence"} for event in events]
        return {
            "schema_version": CONTINUITY_SCHEMA_VERSION,
            "subject_uuid": subject_uuid,
            "character_id": character_id,
            "user_id": user_id,
            "continuity_epoch": epoch,
            "after_sequence": int(after_sequence),
            "events": export_events,
            "checkpoint": self.latest_checkpoint(character_id, user_id),
        }

    def import_continuity_tail(self, character_id: str, user_id: str, bundle: dict[str, Any]) -> int:
        """Import a contiguous canonical tail without applying it to runtime state."""

        if str(bundle.get("schema_version")) != CONTINUITY_SCHEMA_VERSION:
            raise ContinuityImportError("unsupported continuity schema_version")
        subject_uuid, bound_epoch = self._resolve_subject(character_id, user_id)
        if str(bundle.get("subject_uuid")) != subject_uuid:
            raise ContinuityImportError("subject UUID mismatch")
        epoch = int(bundle.get("continuity_epoch", bound_epoch))
        if epoch != bound_epoch:
            raise ContinuityImportError("continuity epoch mismatch")
        events = list(bundle.get("events") or [])
        if not all(isinstance(event, dict) for event in events):
            raise ContinuityImportError("events must be objects")
        events.sort(key=lambda event: int(event.get("sequence", -1)))

        with self._connection() as conn:
            current_row = conn.execute(
                "SELECT COALESCE(MAX(sequence),0) FROM continuity_event WHERE subject_uuid=? AND user_id=? AND continuity_epoch=?",
                (subject_uuid, user_id, epoch),
            ).fetchone()
            expected = int(current_row[0] or 0) + 1
            inserted = 0
            for event in events:
                sequence = int(event.get("sequence", -1))
                if sequence != expected:
                    raise ContinuityImportError(f"non-contiguous sequence: expected {expected}, got {sequence}")
                if event.get("canonicality") != "canonical_event":
                    raise ContinuityImportError("import contains noncanonical event")
                payload = event.get("payload")
                if not isinstance(payload, dict):
                    raise ContinuityImportError("event payload must be an object")
                if not canonical_continuity_eligible(str(event.get("event_type", "")), payload):
                    raise ContinuityImportError("event is not eligible for canonical continuity")
                self._append_continuity_event_conn(
                    conn,
                    character_id=character_id,
                    user_id=user_id,
                    timestep=int(float(event.get("subject_time", 0))),
                    event_type=str(event["event_type"]),
                    payload=payload,
                    wall_time=float(event.get("wall_time", time.time())),
                    legacy_event_id=None,
                    event_uuid=str(event["event_uuid"]),
                    continuity_epoch=epoch,
                    sequence=sequence,
                    source_actor=str(event.get("source_actor", "unknown")),
                    source_class=str(event.get("source_class", "unspecified")),
                    authority_class=str(event.get("authority_class", "canonical_event")),
                    visibility=str(event.get("visibility", "character_observed")),
                    causal_parents=list(event.get("causal_parents") or []),
                    payload_schema=str(event.get("payload_schema", "legacy-event-v1")),
                )
                expected += 1
                inserted += 1
        return inserted

    def backfill_legacy_events(self, character_id: str, user_id: str) -> int:
        """Idempotently admit eligible historical diagnostic events to continuity."""

        subject_uuid, _ = self._resolve_subject(character_id, user_id)
        with self._connection() as conn:
            rows = conn.execute(
                "SELECT id,timestep,event_type,payload,created_at FROM event_log WHERE character_id=? AND user_id=? ORDER BY id",
                (character_id, user_id),
            ).fetchall()
            inserted = 0
            for legacy_id, timestep, event_type, payload_text, created_at in rows:
                already = conn.execute("SELECT 1 FROM continuity_event WHERE legacy_event_id=?", (legacy_id,)).fetchone()
                if already:
                    continue
                try:
                    payload = json.loads(payload_text)
                except json.JSONDecodeError:
                    continue
                if not isinstance(payload, dict) or not canonical_continuity_eligible(str(event_type), payload):
                    continue
                deterministic_uuid = str(uuid.uuid5(
                    uuid.NAMESPACE_URL,
                    f"wayfarer-continuity:{subject_uuid}:{user_id}:legacy:{legacy_id}",
                ))
                self._append_continuity_event_conn(
                    conn,
                    character_id=character_id,
                    user_id=user_id,
                    timestep=int(timestep),
                    event_type=str(event_type),
                    payload=payload,
                    wall_time=float(created_at),
                    legacy_event_id=int(legacy_id),
                    event_uuid=deterministic_uuid,
                )
                inserted += 1
        return inserted

    # ---------------- deterministic checkpoints ----------------
    def record_checkpoint(self, character_id: str, user_id: str, state: dict[str, Any]) -> dict[str, Any]:
        subject_uuid, epoch = self._resolve_subject(character_id, user_id)
        digest = state_digest(state)
        now = time.time()
        with self._connection() as conn:
            row = conn.execute(
                "SELECT COALESCE(MAX(sequence),0) FROM continuity_event WHERE subject_uuid=? AND user_id=? AND continuity_epoch=?",
                (subject_uuid, user_id, epoch),
            ).fetchone()
            sequence = int(row[0] or 0)
            conn.execute(
                "INSERT INTO continuity_checkpoint(subject_uuid,character_id,user_id,continuity_epoch,sequence,state_schema,state_digest,created_at) VALUES(?,?,?,?,?,?,?,?) "
                "ON CONFLICT(subject_uuid,user_id,continuity_epoch,sequence) DO UPDATE SET state_digest=excluded.state_digest,state_schema=excluded.state_schema,created_at=excluded.created_at",
                (subject_uuid, character_id, user_id, epoch, sequence, STATE_DIGEST_SCHEMA_VERSION, digest, now),
            )
        return {
            "subject_uuid": subject_uuid,
            "continuity_epoch": epoch,
            "sequence": sequence,
            "state_schema": STATE_DIGEST_SCHEMA_VERSION,
            "state_digest": digest,
            "created_at": now,
        }

    def latest_checkpoint(self, character_id: str, user_id: str) -> dict[str, Any] | None:
        subject_uuid, epoch = self._resolve_subject(character_id, user_id)
        with self._connection() as conn:
            row = conn.execute(
                "SELECT sequence,state_schema,state_digest,created_at FROM continuity_checkpoint WHERE subject_uuid=? AND user_id=? AND continuity_epoch=? ORDER BY sequence DESC,id DESC LIMIT 1",
                (subject_uuid, user_id, epoch),
            ).fetchone()
        if not row:
            return None
        return {
            "subject_uuid": subject_uuid,
            "continuity_epoch": epoch,
            "sequence": int(row[0]),
            "state_schema": str(row[1]),
            "state_digest": str(row[2]),
            "created_at": float(row[3]),
        }

    # ---------------- legacy event-log readers ----------------
    def event_counts_since(self, character_id: str, user_id: str, since: float) -> dict[str, int]:
        """Count compact semantic evidence after the supplied consolidation watermark.

        This no longer depends on retaining verbose diagnostic payloads. Legacy
        journals are backfilled into consolidation_evidence during Persistence
        initialization before a bounded runtime can prune them.
        """

        conn = self._connect()
        cur = conn.execute(
            "SELECT evidence_types FROM consolidation_evidence "
            "WHERE character_id=? AND user_id=? AND created_at>? ORDER BY id",
            (character_id, user_id, float(since)),
        )
        counts: dict[str, int] = {}
        try:
            for (types_text,) in cur.fetchall():
                try:
                    types = json.loads(types_text)
                except (json.JSONDecodeError, TypeError):
                    types = []
                if not isinstance(types, list):
                    continue
                for item in types:
                    key = str(item)
                    counts[key] = counts.get(key, 0) + 1
            return counts
        finally:
            conn.close()

    def load_events_since(self, character_id: str, user_id: str, since: float, event_type: str | None = None) -> list[dict]:
        """Load retained diagnostic payloads after a wall-clock timestamp.\n\n        Bounded runtimes expose recent telemetry only; canonical continuity is\n        the authority for full lived history. Direct Persistence callers keep\n        the legacy unlimited journal unless they opt into a limit.\n        """
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
