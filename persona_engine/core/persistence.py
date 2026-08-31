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
    canonical_continuity_root_eligible,
    event_authority,
    state_digest,
)
from .deception_ledger import DeceptionLedger

# Operational telemetry is not character cognition. The normal runtime keeps a
# recent diagnostic window for debugging while direct Persistence callers retain
# the legacy unlimited default for migration and tooling compatibility.
DEFAULT_RUNTIME_DIAGNOSTIC_EVENT_LIMIT = 512

DISCONNECTED_TRANSFER_SCHEMA_VERSION = "disconnected-transfer-v1"
DISCONNECTED_TRANSFER_STAGE_RECEIPT_VERSION = "disconnected-transfer-stage-v1"
DISCONNECTED_TRANSFER_FINAL_RECEIPT_VERSION = "disconnected-transfer-final-v1"


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
CREATE TABLE IF NOT EXISTS continuity_writer (
    subject_uuid TEXT PRIMARY KEY,
    active_host_id TEXT NOT NULL,
    writer_generation INTEGER NOT NULL,
    updated_at REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS continuity_handoff (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    handoff_uuid TEXT NOT NULL UNIQUE,
    subject_uuid TEXT NOT NULL,
    from_host_id TEXT NOT NULL,
    to_host_id TEXT NOT NULL,
    previous_generation INTEGER NOT NULL,
    writer_generation INTEGER NOT NULL,
    continuity_epoch INTEGER NOT NULL,
    subject_sequence_anchor INTEGER NOT NULL,
    state_digest TEXT NOT NULL,
    created_at REAL NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_continuity_handoff_subject_generation
    ON continuity_handoff(subject_uuid, writer_generation);
CREATE TABLE IF NOT EXISTS continuity_transfer (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    transfer_uuid TEXT NOT NULL,
    subject_uuid TEXT NOT NULL,
    role TEXT NOT NULL,
    phase TEXT NOT NULL,
    character_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    source_host_id TEXT NOT NULL,
    target_host_id TEXT NOT NULL,
    source_generation INTEGER NOT NULL,
    target_generation INTEGER NOT NULL,
    continuity_epoch INTEGER NOT NULL,
    subject_sequence_anchor INTEGER NOT NULL,
    state_digest TEXT NOT NULL,
    content_digest TEXT NOT NULL,
    bundle_digest TEXT NOT NULL,
    migration_chain TEXT NOT NULL,
    created_at REAL NOT NULL,
    updated_at REAL NOT NULL,
    UNIQUE(transfer_uuid, role)
);
CREATE INDEX IF NOT EXISTS idx_continuity_transfer_subject_role_phase
    ON continuity_transfer(subject_uuid, role, phase);
"""


class ContinuityImportError(ValueError):
    """Raised when an imported canonical event tail violates continuity rules."""


class WriterLeaseError(RuntimeError):
    """Raised when a runtime without the current writer generation tries to mutate a subject."""


class Persistence:
    def __init__(self, path: str = "persona_state.db", diagnostic_event_limit: int | None = None, host_id: str = "local"):
        self.path = path
        self.host_id = " ".join(str(host_id or "").strip().split())
        if not self.host_id:
            raise ValueError("host_id must not be empty")
        if len(self.host_id) > 128:
            raise ValueError("host_id is too long")
        self.diagnostic_event_limit = None if diagnostic_event_limit is None else max(1, int(diagnostic_event_limit))
        self._writer_claims: dict[str, int] = {}
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
        """Bind a stream to a subject and establish or observe writer custody.

        The first host to bind a previously unowned subject receives writer
        generation 1. A different host may read the same store, but it cannot
        mutate subject state until the active writer explicitly hands custody to
        it. Rebinding never silently changes the subject UUID or event epoch.
        """
        subject_uuid = str(subject_uuid or "").strip()
        if not subject_uuid:
            raise ValueError("bind_subject requires a non-empty permanent subject UUID")
        try:
            uuid.UUID(subject_uuid)
        except ValueError as exc:
            raise ValueError(f"invalid subject UUID: {subject_uuid}") from exc
        requested_epoch = max(0, int(continuity_epoch))
        key = (str(character_id), str(user_id))
        now = time.time()
        with self._connection() as conn:
            existing = conn.execute(
                "SELECT subject_uuid,continuity_epoch FROM continuity_subject WHERE character_id=? AND user_id=?",
                (character_id, user_id),
            ).fetchone()
            if existing:
                if str(existing[0]) != subject_uuid:
                    raise ValueError("existing stream is bound to a different subject UUID")
                bound_epoch = int(existing[1])
                if bound_epoch != requested_epoch:
                    raise ValueError("continuity epoch rebinding requires an explicit migration contract")
                conn.execute(
                    "UPDATE continuity_subject SET updated_at=? WHERE character_id=? AND user_id=?",
                    (now, character_id, user_id),
                )
            else:
                bound_epoch = requested_epoch
                conn.execute(
                    "INSERT INTO continuity_subject(character_id,user_id,subject_uuid,continuity_epoch,updated_at) VALUES(?,?,?,?,?)",
                    (character_id, user_id, subject_uuid, bound_epoch, now),
                )
            conn.execute(
                "INSERT OR IGNORE INTO continuity_writer(subject_uuid,active_host_id,writer_generation,updated_at) VALUES(?,?,?,?)",
                (subject_uuid, self.host_id, 1, now),
            )
            writer = conn.execute(
                "SELECT active_host_id,writer_generation FROM continuity_writer WHERE subject_uuid=?",
                (subject_uuid,),
            ).fetchone()
        self._subject_bindings[key] = (subject_uuid, bound_epoch)
        if writer and str(writer[0]) == self.host_id and subject_uuid not in self._writer_claims:
            self._writer_claims[subject_uuid] = int(writer[1])
        if self.diagnostic_event_limit is not None and self.writer_status(character_id, user_id)["writable"]:
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

    # ---------------- cross-host writer custody ----------------
    def _ensure_writer_row_conn(self, conn, subject_uuid: str) -> tuple[str, int]:
        row = conn.execute(
            "SELECT active_host_id,writer_generation FROM continuity_writer WHERE subject_uuid=?",
            (subject_uuid,),
        ).fetchone()
        if row is None:
            conn.execute(
                "INSERT OR IGNORE INTO continuity_writer(subject_uuid,active_host_id,writer_generation,updated_at) VALUES(?,?,?,?)",
                (subject_uuid, self.host_id, 1, time.time()),
            )
            row = conn.execute(
                "SELECT active_host_id,writer_generation FROM continuity_writer WHERE subject_uuid=?",
                (subject_uuid,),
            ).fetchone()
        if row is None:
            raise WriterLeaseError("writer custody row could not be established")
        active_host, generation = str(row[0]), int(row[1])
        if active_host == self.host_id and subject_uuid not in self._writer_claims:
            self._writer_claims[subject_uuid] = generation
        return active_host, generation

    def _pending_disconnected_transfer_conn(self, conn, subject_uuid: str) -> str | None:
        row = conn.execute(
            "SELECT transfer_uuid FROM continuity_transfer "
            "WHERE subject_uuid=? AND role='source' AND phase='prepared' ORDER BY id DESC LIMIT 1",
            (subject_uuid,),
        ).fetchone()
        return str(row[0]) if row else None

    def _retired_disconnected_transfer_conn(self, conn, subject_uuid: str) -> str | None:
        row = conn.execute(
            "SELECT transfer_uuid FROM continuity_transfer "
            "WHERE subject_uuid=? AND role='source' AND phase='finalized' ORDER BY id DESC LIMIT 1",
            (subject_uuid,),
        ).fetchone()
        return str(row[0]) if row else None

    def _fence_writer_conn(
        self,
        conn,
        character_id: str,
        user_id: str,
        *,
        allow_transfer_uuid: str | None = None,
    ) -> tuple[str, int]:
        """Validate writer generation while holding SQLite's write reservation.

        ``BEGIN IMMEDIATE`` obtains the database write reservation before the
        custody row is read, so an explicit handoff cannot race between the
        generation check and the caller's mutation. A prepared disconnected
        transfer additionally quiesces normal writes until it is finalized or
        canceled. A finalized source store is permanently retired under the v1
        transfer contract, even if that old file is reopened using the target
        host id.
        """
        if not conn.in_transaction:
            conn.execute("BEGIN IMMEDIATE")
        subject_uuid, _ = self._resolve_subject(character_id, user_id)
        active_host, generation = self._ensure_writer_row_conn(conn, subject_uuid)
        retired = self._retired_disconnected_transfer_conn(conn, subject_uuid)
        if retired is not None:
            raise WriterLeaseError(f"authority store retired by disconnected transfer {retired}")
        claim = self._writer_claims.get(subject_uuid)
        if active_host != self.host_id or claim != generation:
            raise WriterLeaseError(
                f"stale or non-owner writer: host={self.host_id!r}, claim={claim}, "
                f"active_host={active_host!r}, active_generation={generation}"
            )
        pending = self._pending_disconnected_transfer_conn(conn, subject_uuid)
        if pending is not None and pending != str(allow_transfer_uuid or ""):
            raise WriterLeaseError(f"source is quiesced for disconnected transfer {pending}")
        return subject_uuid, generation

    def assert_writer(self, character_id: str, user_id: str) -> dict[str, Any]:
        subject_uuid, _ = self._resolve_subject(character_id, user_id)
        with self._connection() as conn:
            active_host, generation = self._ensure_writer_row_conn(conn, subject_uuid)
            pending = self._pending_disconnected_transfer_conn(conn, subject_uuid)
            retired = self._retired_disconnected_transfer_conn(conn, subject_uuid)
        claim = self._writer_claims.get(subject_uuid)
        if retired is not None:
            raise WriterLeaseError(f"authority store retired by disconnected transfer {retired}")
        if pending is not None:
            raise WriterLeaseError(f"source is quiesced for disconnected transfer {pending}")
        if active_host != self.host_id or claim != generation:
            raise WriterLeaseError(
                f"host {self.host_id!r} does not hold current writer generation for subject {subject_uuid}"
            )
        return self.writer_status(character_id, user_id)

    def writer_status(self, character_id: str, user_id: str) -> dict[str, Any]:
        subject_uuid, epoch = self._resolve_subject(character_id, user_id)
        with self._connection() as conn:
            active_host, generation = self._ensure_writer_row_conn(conn, subject_uuid)
            pending = self._pending_disconnected_transfer_conn(conn, subject_uuid)
            retired = self._retired_disconnected_transfer_conn(conn, subject_uuid)
        claim = self._writer_claims.get(subject_uuid)
        return {
            "subject_uuid": subject_uuid,
            "continuity_epoch": epoch,
            "local_host_id": self.host_id,
            "active_host_id": active_host,
            "writer_generation": generation,
            "claim_generation": claim,
            "transfer_pending": pending is not None,
            "pending_transfer_uuid": pending,
            "store_retired": retired is not None,
            "retired_transfer_uuid": retired,
            "writable": (
                active_host == self.host_id
                and claim == generation
                and pending is None
                and retired is None
            ),
        }

    def handoff_writer(self, character_id: str, user_id: str, target_host_id: str, *, state_digest: str = "") -> dict[str, Any]:
        """Transfer shared-store writer custody and advance its fencing generation.

        V1 deliberately has no timeout or automatic stealing. Ambiguous custody
        fails closed instead of risking split-brain canonical history. The audit
        is continuity administration, not a fabricated lived event.
        """
        target = " ".join(str(target_host_id or "").strip().split())
        if not target:
            raise ValueError("target_host_id must not be empty")
        if target == self.host_id:
            raise ValueError("target_host_id must name a different host")
        subject_uuid, epoch = self._resolve_subject(character_id, user_id)
        now = time.time()
        handoff_uuid = str(uuid.uuid4())
        with self._connection() as conn:
            _, generation = self._fence_writer_conn(conn, character_id, user_id)
            anchor_row = conn.execute(
                "SELECT COALESCE(MAX(subject_sequence),0) FROM continuity_event WHERE subject_uuid=? AND continuity_epoch=?",
                (subject_uuid, epoch),
            ).fetchone()
            anchor = int(anchor_row[0] or 0)
            next_generation = generation + 1
            cur = conn.execute(
                "UPDATE continuity_writer SET active_host_id=?,writer_generation=?,updated_at=? "
                "WHERE subject_uuid=? AND active_host_id=? AND writer_generation=?",
                (target, next_generation, now, subject_uuid, self.host_id, generation),
            )
            if int(cur.rowcount or 0) != 1:
                raise WriterLeaseError("writer handoff lost the fencing race")
            conn.execute(
                "INSERT INTO continuity_handoff(handoff_uuid,subject_uuid,from_host_id,to_host_id,previous_generation,writer_generation,continuity_epoch,subject_sequence_anchor,state_digest,created_at) VALUES(?,?,?,?,?,?,?,?,?,?)",
                (handoff_uuid, subject_uuid, self.host_id, target, generation, next_generation, epoch, anchor, str(state_digest or ""), now),
            )
        return {
            "schema_version": "writer-handoff-v1",
            "handoff_uuid": handoff_uuid,
            "subject_uuid": subject_uuid,
            "from_host_id": self.host_id,
            "to_host_id": target,
            "previous_generation": generation,
            "writer_generation": next_generation,
            "continuity_epoch": epoch,
            "subject_sequence_anchor": anchor,
            "state_digest": str(state_digest or ""),
            "created_at": now,
        }

    def accept_writer_handoff(self, character_id: str, user_id: str, receipt: dict[str, Any], *, local_state_digest: str = "") -> dict[str, Any]:
        """Validate the durable handoff receipt and install its generation locally."""
        if str(receipt.get("schema_version")) != "writer-handoff-v1":
            raise WriterLeaseError("unsupported writer handoff receipt")
        subject_uuid, _ = self._resolve_subject(character_id, user_id)
        if str(receipt.get("subject_uuid")) != subject_uuid:
            raise WriterLeaseError("handoff subject UUID mismatch")
        if str(receipt.get("to_host_id")) != self.host_id:
            raise WriterLeaseError("handoff targets a different host")
        expected_digest = str(receipt.get("state_digest") or "")
        if expected_digest and local_state_digest and expected_digest != local_state_digest:
            raise WriterLeaseError("target state does not match the handoff state digest")
        generation = int(receipt.get("writer_generation", -1))
        handoff_uuid = str(receipt.get("handoff_uuid") or "")
        with self._connection() as conn:
            row = conn.execute(
                "SELECT active_host_id,writer_generation FROM continuity_writer WHERE subject_uuid=?",
                (subject_uuid,),
            ).fetchone()
            audit = conn.execute(
                "SELECT to_host_id,writer_generation,state_digest FROM continuity_handoff WHERE handoff_uuid=? AND subject_uuid=?",
                (handoff_uuid, subject_uuid),
            ).fetchone()
        if row is None or str(row[0]) != self.host_id or int(row[1]) != generation:
            raise WriterLeaseError("handoff receipt is not the active writer generation")
        if audit is None or str(audit[0]) != self.host_id or int(audit[1]) != generation or str(audit[2]) != expected_digest:
            raise WriterLeaseError("handoff receipt does not match durable custody audit")
        self._writer_claims[subject_uuid] = generation
        return self.writer_status(character_id, user_id)

    def load_writer_handoffs(self, character_id: str, user_id: str) -> list[dict[str, Any]]:
        subject_uuid, _ = self._resolve_subject(character_id, user_id)
        with self._connection() as conn:
            rows = conn.execute(
                "SELECT handoff_uuid,from_host_id,to_host_id,previous_generation,writer_generation,continuity_epoch,subject_sequence_anchor,state_digest,created_at FROM continuity_handoff WHERE subject_uuid=? ORDER BY writer_generation,id",
                (subject_uuid,),
            ).fetchall()
        return [
            {
                "handoff_uuid": row[0], "subject_uuid": subject_uuid,
                "from_host_id": row[1], "to_host_id": row[2],
                "previous_generation": int(row[3]), "writer_generation": int(row[4]),
                "continuity_epoch": int(row[5]), "subject_sequence_anchor": int(row[6]),
                "state_digest": str(row[7]), "created_at": float(row[8]),
            }
            for row in rows
        ]

    # ---------------- disconnected authority-store transfer ----------------
    @staticmethod
    def _normalize_transfer_host_id(value: str, field: str) -> str:
        normalized = " ".join(str(value or "").strip().split())
        if not normalized:
            raise ContinuityImportError(f"{field} must not be empty")
        if len(normalized) > 128:
            raise ContinuityImportError(f"{field} is too long")
        return normalized

    def _migration_chain_conn(self, conn, subject_uuid: str) -> list[dict[str, Any]]:
        row = conn.execute(
            "SELECT migration_chain FROM continuity_transfer "
            "WHERE subject_uuid=? AND role='target' AND phase='activated' ORDER BY id DESC LIMIT 1",
            (subject_uuid,),
        ).fetchone()
        if not row:
            return []
        try:
            value = json.loads(row[0])
        except (json.JSONDecodeError, TypeError):
            return []
        return list(value) if isinstance(value, list) else []

    def _subject_transfer_content_conn(self, conn, subject_uuid: str, epoch: int) -> dict[str, Any]:
        bindings_rows = conn.execute(
            "SELECT character_id,user_id,continuity_epoch FROM continuity_subject "
            "WHERE subject_uuid=? ORDER BY character_id,user_id",
            (subject_uuid,),
        ).fetchall()
        bindings = [
            {"character_id": str(cid), "user_id": str(uid), "continuity_epoch": int(bound_epoch)}
            for cid, uid, bound_epoch in bindings_rows
        ]
        binding_keys = {(item["character_id"], item["user_id"]) for item in bindings}

        stream_state: list[dict[str, Any]] = []
        checkpoints: list[dict[str, Any]] = []
        for binding in bindings:
            cid, uid = binding["character_id"], binding["user_id"]
            rows = conn.execute(
                "SELECT key,value FROM state WHERE character_id=? AND user_id=? ORDER BY key",
                (cid, uid),
            ).fetchall()
            for key, value_text in rows:
                stream_state.append({
                    "character_id": cid,
                    "user_id": uid,
                    "key": str(key),
                    "value": json.loads(value_text),
                })
            checkpoint = conn.execute(
                "SELECT sequence,state_schema,state_digest,created_at FROM continuity_checkpoint "
                "WHERE subject_uuid=? AND user_id=? AND continuity_epoch=? ORDER BY sequence DESC,id DESC LIMIT 1",
                (subject_uuid, uid, epoch),
            ).fetchone()
            if checkpoint:
                checkpoints.append({
                    "character_id": cid,
                    "user_id": uid,
                    "sequence": int(checkpoint[0]),
                    "state_schema": str(checkpoint[1]),
                    "state_digest": str(checkpoint[2]),
                    "created_at": float(checkpoint[3]),
                })

        subject_state = [
            {"key": str(key), "value": json.loads(value_text)}
            for key, value_text in conn.execute(
                "SELECT key,value FROM subject_state WHERE subject_uuid=? ORDER BY key",
                (subject_uuid,),
            ).fetchall()
        ]

        event_rows = conn.execute(
            "SELECT event_uuid,subject_uuid,character_id,user_id,sequence,subject_sequence,continuity_epoch,subject_time,wall_time,source_actor,source_class,authority_class,event_type,visibility,canonicality,causal_parents,payload_schema,payload,legacy_event_id "
            "FROM continuity_event WHERE subject_uuid=? AND continuity_epoch=? ORDER BY subject_sequence",
            (subject_uuid, epoch),
        ).fetchall()
        events = []
        for row in event_rows:
            event = self._continuity_row_to_dict(row)
            event.pop("legacy_event_id", None)
            events.append(event)

        evidence_rows = conn.execute(
            "SELECT e.character_id,e.user_id,e.evidence_types,e.created_at "
            "FROM consolidation_evidence e "
            "JOIN continuity_subject s ON s.character_id=e.character_id AND s.user_id=e.user_id "
            "WHERE s.subject_uuid=? ORDER BY e.created_at,e.id",
            (subject_uuid,),
        ).fetchall()
        pending_evidence = []
        for cid, uid, evidence_text, created_at in evidence_rows:
            if (str(cid), str(uid)) not in binding_keys:
                continue
            types = json.loads(evidence_text)
            pending_evidence.append({
                "character_id": str(cid),
                "user_id": str(uid),
                "evidence_types": list(types) if isinstance(types, list) else [],
                "created_at": float(created_at),
            })

        shared_handoffs = [
            {
                "handoff_uuid": str(row[0]),
                "subject_uuid": subject_uuid,
                "from_host_id": str(row[1]),
                "to_host_id": str(row[2]),
                "previous_generation": int(row[3]),
                "writer_generation": int(row[4]),
                "continuity_epoch": int(row[5]),
                "subject_sequence_anchor": int(row[6]),
                "state_digest": str(row[7]),
                "created_at": float(row[8]),
            }
            for row in conn.execute(
                "SELECT handoff_uuid,from_host_id,to_host_id,previous_generation,writer_generation,continuity_epoch,subject_sequence_anchor,state_digest,created_at "
                "FROM continuity_handoff WHERE subject_uuid=? ORDER BY writer_generation,id",
                (subject_uuid,),
            ).fetchall()
        ]

        return {
            "bindings": bindings,
            "stream_state": stream_state,
            "subject_state": subject_state,
            "events": events,
            "pending_evidence": pending_evidence,
            "shared_handoffs": shared_handoffs,
            "checkpoints": checkpoints,
        }

    @staticmethod
    def _transfer_content_digest(content: dict[str, Any]) -> str:
        return state_digest(content)

    def _validate_disconnected_transfer_bundle(self, bundle: dict[str, Any]) -> tuple[str, int, dict[str, Any]]:
        if not isinstance(bundle, dict) or str(bundle.get("schema_version")) != DISCONNECTED_TRANSFER_SCHEMA_VERSION:
            raise ContinuityImportError("unsupported disconnected transfer schema_version")
        supplied_bundle_digest = str(bundle.get("bundle_digest") or "")
        unsigned = {key: value for key, value in bundle.items() if key != "bundle_digest"}
        if not supplied_bundle_digest or state_digest(unsigned) != supplied_bundle_digest:
            raise ContinuityImportError("disconnected transfer bundle digest mismatch")
        content = bundle.get("content")
        if not isinstance(content, dict):
            raise ContinuityImportError("disconnected transfer content must be an object")
        if self._transfer_content_digest(content) != str(bundle.get("content_digest") or ""):
            raise ContinuityImportError("disconnected transfer content digest mismatch")

        subject_uuid = str(bundle.get("subject_uuid") or "")
        try:
            uuid.UUID(subject_uuid)
        except ValueError as exc:
            raise ContinuityImportError("invalid disconnected transfer subject UUID") from exc
        epoch = int(bundle.get("continuity_epoch", -1))
        if epoch < 0:
            raise ContinuityImportError("invalid disconnected transfer continuity epoch")
        source_host = self._normalize_transfer_host_id(bundle.get("source_host_id", ""), "source_host_id")
        target_host = self._normalize_transfer_host_id(bundle.get("target_host_id", ""), "target_host_id")
        if source_host == target_host:
            raise ContinuityImportError("disconnected transfer requires distinct source and target hosts")
        source_generation = int(bundle.get("source_generation", -1))
        target_generation = int(bundle.get("target_generation", -1))
        if source_generation < 1 or target_generation != source_generation + 1:
            raise ContinuityImportError("invalid disconnected transfer writer generations")

        bindings = list(content.get("bindings") or [])
        if not bindings:
            raise ContinuityImportError("disconnected transfer requires at least one subject binding")
        binding_keys: set[tuple[str, str]] = set()
        for item in bindings:
            if not isinstance(item, dict):
                raise ContinuityImportError("invalid disconnected transfer binding")
            key = (str(item.get("character_id") or ""), str(item.get("user_id") or ""))
            if not all(key) or int(item.get("continuity_epoch", -1)) != epoch or key in binding_keys:
                raise ContinuityImportError("invalid or duplicate disconnected transfer binding")
            binding_keys.add(key)
        primary = (str(bundle.get("character_id") or ""), str(bundle.get("user_id") or ""))
        if primary not in binding_keys:
            raise ContinuityImportError("primary transfer stream is not bound to the subject")

        events = list(content.get("events") or [])
        seen_event_ids: set[str] = set()
        subject_ordinals: list[int] = []
        stream_sequences: dict[tuple[str, str], list[int]] = {}
        for event in events:
            if not isinstance(event, dict):
                raise ContinuityImportError("invalid disconnected transfer event")
            if str(event.get("subject_uuid")) != subject_uuid or int(event.get("continuity_epoch", -1)) != epoch:
                raise ContinuityImportError("disconnected transfer event subject mismatch")
            key = (str(event.get("character_id") or ""), str(event.get("user_id") or ""))
            if key not in binding_keys:
                raise ContinuityImportError("disconnected transfer event references an unbound stream")
            event_uuid = str(event.get("event_uuid") or "")
            if not event_uuid or event_uuid in seen_event_ids:
                raise ContinuityImportError("duplicate disconnected transfer event UUID")
            seen_event_ids.add(event_uuid)
            if event.get("canonicality") != "canonical_event" or not isinstance(event.get("payload"), dict):
                raise ContinuityImportError("disconnected transfer contains a noncanonical event")
            if not canonical_continuity_eligible(str(event.get("event_type", "")), event["payload"]):
                raise ContinuityImportError("disconnected transfer contains an ineligible canonical event")
            subject_ordinals.append(int(event.get("subject_sequence", -1)))
            stream_sequences.setdefault(key, []).append(int(event.get("sequence", -1)))
        anchor = int(bundle.get("subject_sequence_anchor", -1))
        expected_subject = list(range(1, anchor + 1))
        if subject_ordinals != expected_subject:
            raise ContinuityImportError("disconnected transfer subject sequence is not complete and contiguous")
        for sequences in stream_sequences.values():
            if sequences != list(range(1, max(sequences) + 1)):
                raise ContinuityImportError("disconnected transfer stream sequence is not complete and contiguous")

        for family in ("stream_state", "pending_evidence", "checkpoints"):
            for item in list(content.get(family) or []):
                if not isinstance(item, dict):
                    raise ContinuityImportError(f"invalid disconnected transfer {family} entry")
                key = (str(item.get("character_id") or ""), str(item.get("user_id") or ""))
                if key not in binding_keys:
                    raise ContinuityImportError(f"disconnected transfer {family} references an unbound stream")
        for handoff in list(content.get("shared_handoffs") or []):
            if not isinstance(handoff, dict) or str(handoff.get("subject_uuid")) != subject_uuid:
                raise ContinuityImportError("invalid shared-store handoff history in disconnected transfer")
        return subject_uuid, epoch, content

    def prepare_disconnected_transfer(
        self,
        character_id: str,
        user_id: str,
        target_host_id: str,
        *,
        local_state_digest: str,
    ) -> dict[str, Any]:
        """Create a target-specific transfer bundle and quiesce the source store.

        The source retains custody while the target stages and validates the
        bundle, but normal mutations fail closed after preparation. Finalization
        or explicit cancellation is therefore required before the source can
        proceed. Transfer administration is not added to lived biography.
        """
        target = self._normalize_transfer_host_id(target_host_id, "target_host_id")
        if target == self.host_id:
            raise ContinuityImportError("target_host_id must name a different host")
        subject_uuid, epoch = self._resolve_subject(character_id, user_id)
        transfer_uuid = str(uuid.uuid4())
        created_at = time.time()
        with self._connection() as conn:
            _, generation = self._fence_writer_conn(conn, character_id, user_id)
            content = self._subject_transfer_content_conn(conn, subject_uuid, epoch)
            content_digest = self._transfer_content_digest(content)
            anchor = len(content["events"])
            target_generation = generation + 1
            migration_chain = self._migration_chain_conn(conn, subject_uuid)
            unsigned = {
                "schema_version": DISCONNECTED_TRANSFER_SCHEMA_VERSION,
                "transfer_uuid": transfer_uuid,
                "subject_uuid": subject_uuid,
                "character_id": str(character_id),
                "user_id": str(user_id),
                "source_host_id": self.host_id,
                "target_host_id": target,
                "source_generation": generation,
                "target_generation": target_generation,
                "continuity_epoch": epoch,
                "subject_sequence_anchor": anchor,
                "state_digest": str(local_state_digest or ""),
                "content_digest": content_digest,
                "created_at": created_at,
                "migration_chain": migration_chain,
                "content": content,
            }
            bundle_digest = state_digest(unsigned)
            conn.execute(
                "INSERT INTO continuity_transfer(transfer_uuid,subject_uuid,role,phase,character_id,user_id,source_host_id,target_host_id,source_generation,target_generation,continuity_epoch,subject_sequence_anchor,state_digest,content_digest,bundle_digest,migration_chain,created_at,updated_at) "
                "VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (
                    transfer_uuid, subject_uuid, "source", "prepared", str(character_id), str(user_id),
                    self.host_id, target, generation, target_generation, epoch, anchor,
                    str(local_state_digest or ""), content_digest, bundle_digest,
                    json.dumps(migration_chain, ensure_ascii=False), created_at, created_at,
                ),
            )
        return {**unsigned, "bundle_digest": bundle_digest}

    def stage_disconnected_transfer(self, bundle: dict[str, Any]) -> dict[str, Any]:
        """Install a validated transfer bundle into a non-writable target store."""
        subject_uuid, epoch, content = self._validate_disconnected_transfer_bundle(bundle)
        if str(bundle.get("target_host_id")) != self.host_id:
            raise ContinuityImportError("disconnected transfer targets a different host")
        transfer_uuid = str(bundle["transfer_uuid"])
        now = time.time()
        with self._connection() as conn:
            if not conn.in_transaction:
                conn.execute("BEGIN IMMEDIATE")
            existing_audit = conn.execute(
                "SELECT phase,bundle_digest FROM continuity_transfer WHERE transfer_uuid=? AND role='target'",
                (transfer_uuid,),
            ).fetchone()
            if existing_audit:
                if str(existing_audit[0]) == "staged" and str(existing_audit[1]) == str(bundle["bundle_digest"]):
                    return {
                        "schema_version": DISCONNECTED_TRANSFER_STAGE_RECEIPT_VERSION,
                        "transfer_uuid": transfer_uuid,
                        "subject_uuid": subject_uuid,
                        "character_id": str(bundle["character_id"]),
                        "user_id": str(bundle["user_id"]),
                        "source_host_id": str(bundle["source_host_id"]),
                        "target_host_id": self.host_id,
                        "source_generation": int(bundle["source_generation"]),
                        "target_generation": int(bundle["target_generation"]),
                        "continuity_epoch": epoch,
                        "subject_sequence_anchor": int(bundle["subject_sequence_anchor"]),
                        "state_digest": str(bundle.get("state_digest") or ""),
                        "content_digest": str(bundle["content_digest"]),
                        "bundle_digest": str(bundle["bundle_digest"]),
                    }
                raise ContinuityImportError("transfer UUID already exists with incompatible target state")
            if conn.execute("SELECT 1 FROM continuity_subject WHERE subject_uuid=? LIMIT 1", (subject_uuid,)).fetchone():
                raise ContinuityImportError("target store already contains this subject")
            if conn.execute("SELECT 1 FROM continuity_writer WHERE subject_uuid=?", (subject_uuid,)).fetchone():
                raise ContinuityImportError("target store already contains writer custody for this subject")

            for binding in content["bindings"]:
                cid, uid = str(binding["character_id"]), str(binding["user_id"])
                if conn.execute(
                    "SELECT 1 FROM continuity_subject WHERE character_id=? AND user_id=?",
                    (cid, uid),
                ).fetchone() or conn.execute(
                    "SELECT 1 FROM state WHERE character_id=? AND user_id=? LIMIT 1",
                    (cid, uid),
                ).fetchone():
                    raise ContinuityImportError("target store has a conflicting stream binding or snapshot")
                conn.execute(
                    "INSERT INTO continuity_subject(character_id,user_id,subject_uuid,continuity_epoch,updated_at) VALUES(?,?,?,?,?)",
                    (cid, uid, subject_uuid, epoch, now),
                )
                self._subject_bindings[(cid, uid)] = (subject_uuid, epoch)

            conn.execute(
                "INSERT INTO continuity_writer(subject_uuid,active_host_id,writer_generation,updated_at) VALUES(?,?,?,?)",
                (subject_uuid, str(bundle["source_host_id"]), int(bundle["source_generation"]), now),
            )
            for item in content["stream_state"]:
                conn.execute(
                    "INSERT INTO state(character_id,user_id,key,value,updated_at) VALUES(?,?,?,?,?)",
                    (
                        str(item["character_id"]), str(item["user_id"]), str(item["key"]),
                        json.dumps(item["value"], ensure_ascii=False), now,
                    ),
                )
            for item in content["subject_state"]:
                conn.execute(
                    "INSERT INTO subject_state(subject_uuid,key,value,updated_at) VALUES(?,?,?,?)",
                    (subject_uuid, str(item["key"]), json.dumps(item["value"], ensure_ascii=False), now),
                )
            for event in content["events"]:
                conn.execute(
                    "INSERT INTO continuity_event(event_uuid,subject_uuid,character_id,user_id,sequence,subject_sequence,continuity_epoch,subject_time,wall_time,source_actor,source_class,authority_class,event_type,visibility,canonicality,causal_parents,payload_schema,payload,legacy_event_id) "
                    "VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,NULL)",
                    (
                        str(event["event_uuid"]), subject_uuid, str(event["character_id"]), str(event["user_id"]),
                        int(event["sequence"]), int(event["subject_sequence"]), epoch,
                        float(event["subject_time"]), float(event["wall_time"]), str(event["source_actor"]),
                        str(event["source_class"]), str(event["authority_class"]), str(event["event_type"]),
                        str(event["visibility"]), "canonical_event",
                        json.dumps(list(event.get("causal_parents") or []), ensure_ascii=False),
                        str(event["payload_schema"]), json.dumps(event["payload"], ensure_ascii=False),
                    ),
                )
            min_legacy = conn.execute("SELECT COALESCE(MIN(legacy_event_id),0) FROM consolidation_evidence").fetchone()
            next_legacy = min(-1, int(min_legacy[0] or 0) - 1)
            for item in content["pending_evidence"]:
                conn.execute(
                    "INSERT INTO consolidation_evidence(legacy_event_id,character_id,user_id,evidence_types,created_at) VALUES(?,?,?,?,?)",
                    (
                        next_legacy, str(item["character_id"]), str(item["user_id"]),
                        json.dumps(list(item.get("evidence_types") or []), ensure_ascii=False), float(item["created_at"]),
                    ),
                )
                next_legacy -= 1
            for item in content["shared_handoffs"]:
                conn.execute(
                    "INSERT OR IGNORE INTO continuity_handoff(handoff_uuid,subject_uuid,from_host_id,to_host_id,previous_generation,writer_generation,continuity_epoch,subject_sequence_anchor,state_digest,created_at) VALUES(?,?,?,?,?,?,?,?,?,?)",
                    (
                        str(item["handoff_uuid"]), subject_uuid, str(item["from_host_id"]), str(item["to_host_id"]),
                        int(item["previous_generation"]), int(item["writer_generation"]), int(item["continuity_epoch"]),
                        int(item["subject_sequence_anchor"]), str(item["state_digest"]), float(item["created_at"]),
                    ),
                )
            for item in content["checkpoints"]:
                conn.execute(
                    "INSERT INTO continuity_checkpoint(subject_uuid,character_id,user_id,continuity_epoch,sequence,state_schema,state_digest,created_at) VALUES(?,?,?,?,?,?,?,?)",
                    (
                        subject_uuid, str(item["character_id"]), str(item["user_id"]), epoch,
                        int(item["sequence"]), str(item["state_schema"]), str(item["state_digest"]), float(item["created_at"]),
                    ),
                )
            conn.execute(
                "INSERT INTO continuity_transfer(transfer_uuid,subject_uuid,role,phase,character_id,user_id,source_host_id,target_host_id,source_generation,target_generation,continuity_epoch,subject_sequence_anchor,state_digest,content_digest,bundle_digest,migration_chain,created_at,updated_at) "
                "VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (
                    transfer_uuid, subject_uuid, "target", "staged", str(bundle["character_id"]), str(bundle["user_id"]),
                    str(bundle["source_host_id"]), self.host_id, int(bundle["source_generation"]), int(bundle["target_generation"]),
                    epoch, int(bundle["subject_sequence_anchor"]), str(bundle.get("state_digest") or ""),
                    str(bundle["content_digest"]), str(bundle["bundle_digest"]),
                    json.dumps(list(bundle.get("migration_chain") or []), ensure_ascii=False), float(bundle["created_at"]), now,
                ),
            )
        return {
            "schema_version": DISCONNECTED_TRANSFER_STAGE_RECEIPT_VERSION,
            "transfer_uuid": transfer_uuid,
            "subject_uuid": subject_uuid,
            "character_id": str(bundle["character_id"]),
            "user_id": str(bundle["user_id"]),
            "source_host_id": str(bundle["source_host_id"]),
            "target_host_id": self.host_id,
            "source_generation": int(bundle["source_generation"]),
            "target_generation": int(bundle["target_generation"]),
            "continuity_epoch": epoch,
            "subject_sequence_anchor": int(bundle["subject_sequence_anchor"]),
            "state_digest": str(bundle.get("state_digest") or ""),
            "content_digest": str(bundle["content_digest"]),
            "bundle_digest": str(bundle["bundle_digest"]),
        }

    def cancel_disconnected_transfer(self, character_id: str, user_id: str, transfer_uuid: str) -> dict[str, Any]:
        subject_uuid, _ = self._resolve_subject(character_id, user_id)
        transfer_uuid = str(transfer_uuid or "")
        with self._connection() as conn:
            self._fence_writer_conn(conn, character_id, user_id, allow_transfer_uuid=transfer_uuid)
            row = conn.execute(
                "SELECT phase FROM continuity_transfer WHERE transfer_uuid=? AND subject_uuid=? AND role='source'",
                (transfer_uuid, subject_uuid),
            ).fetchone()
            if row is None or str(row[0]) != "prepared":
                raise WriterLeaseError("disconnected transfer is not cancelable from the source")
            conn.execute(
                "UPDATE continuity_transfer SET phase='canceled',updated_at=? WHERE transfer_uuid=? AND role='source'",
                (time.time(), transfer_uuid),
            )
        return self.writer_status(character_id, user_id)

    def finalize_disconnected_transfer(
        self,
        character_id: str,
        user_id: str,
        stage_receipt: dict[str, Any],
        *,
        local_state_digest: str,
    ) -> dict[str, Any]:
        if str(stage_receipt.get("schema_version")) != DISCONNECTED_TRANSFER_STAGE_RECEIPT_VERSION:
            raise WriterLeaseError("unsupported disconnected transfer stage receipt")
        transfer_uuid = str(stage_receipt.get("transfer_uuid") or "")
        subject_uuid, epoch = self._resolve_subject(character_id, user_id)
        now = time.time()
        with self._connection() as conn:
            _, generation = self._fence_writer_conn(
                conn, character_id, user_id, allow_transfer_uuid=transfer_uuid
            )
            audit = conn.execute(
                "SELECT target_host_id,source_generation,target_generation,continuity_epoch,subject_sequence_anchor,state_digest,content_digest,bundle_digest,migration_chain,created_at,phase "
                "FROM continuity_transfer WHERE transfer_uuid=? AND subject_uuid=? AND role='source'",
                (transfer_uuid, subject_uuid),
            ).fetchone()
            if audit is None or str(audit[10]) != "prepared":
                raise WriterLeaseError("source transfer is not in prepared state")
            target_host = str(audit[0])
            source_generation, target_generation = int(audit[1]), int(audit[2])
            if generation != source_generation or int(audit[3]) != epoch:
                raise WriterLeaseError("source transfer generation or epoch changed")
            checks = {
                "transfer_uuid": transfer_uuid,
                "subject_uuid": subject_uuid,
                "character_id": str(character_id),
                "user_id": str(user_id),
                "source_host_id": self.host_id,
                "target_host_id": target_host,
                "source_generation": source_generation,
                "target_generation": target_generation,
                "continuity_epoch": epoch,
                "subject_sequence_anchor": int(audit[4]),
                "state_digest": str(audit[5]),
                "content_digest": str(audit[6]),
                "bundle_digest": str(audit[7]),
            }
            for key, expected in checks.items():
                actual = stage_receipt.get(key)
                if str(actual) != str(expected):
                    raise WriterLeaseError(f"stage receipt mismatch for {key}")
            if str(local_state_digest or "") != str(audit[5]):
                raise WriterLeaseError("source state digest changed after transfer preparation")
            current_content = self._subject_transfer_content_conn(conn, subject_uuid, epoch)
            if self._transfer_content_digest(current_content) != str(audit[6]):
                raise WriterLeaseError("source content changed after transfer preparation")
            cur = conn.execute(
                "UPDATE continuity_writer SET active_host_id=?,writer_generation=?,updated_at=? "
                "WHERE subject_uuid=? AND active_host_id=? AND writer_generation=?",
                (target_host, target_generation, now, subject_uuid, self.host_id, source_generation),
            )
            if int(cur.rowcount or 0) != 1:
                raise WriterLeaseError("disconnected transfer lost the source fencing race")
            conn.execute(
                "UPDATE continuity_transfer SET phase='finalized',updated_at=? WHERE transfer_uuid=? AND role='source'",
                (now, transfer_uuid),
            )
            migration_chain = json.loads(audit[8]) if audit[8] else []
            created_at = float(audit[9])
        return {
            **checks,
            "schema_version": DISCONNECTED_TRANSFER_FINAL_RECEIPT_VERSION,
            "created_at": created_at,
            "finalized_at": now,
            "migration_chain": migration_chain if isinstance(migration_chain, list) else [],
        }

    def activate_disconnected_transfer(
        self,
        character_id: str,
        user_id: str,
        final_receipt: dict[str, Any],
        *,
        local_state_digest: str,
    ) -> dict[str, Any]:
        if str(final_receipt.get("schema_version")) != DISCONNECTED_TRANSFER_FINAL_RECEIPT_VERSION:
            raise WriterLeaseError("unsupported disconnected transfer final receipt")
        transfer_uuid = str(final_receipt.get("transfer_uuid") or "")
        subject_uuid, epoch = self._resolve_subject(character_id, user_id)
        if str(final_receipt.get("subject_uuid")) != subject_uuid:
            raise WriterLeaseError("disconnected transfer subject UUID mismatch")
        if str(final_receipt.get("target_host_id")) != self.host_id:
            raise WriterLeaseError("disconnected transfer final receipt targets a different host")
        if str(final_receipt.get("character_id")) != str(character_id) or str(final_receipt.get("user_id")) != str(user_id):
            raise WriterLeaseError("disconnected transfer primary stream mismatch")
        now = time.time()
        with self._connection() as conn:
            if not conn.in_transaction:
                conn.execute("BEGIN IMMEDIATE")
            audit = conn.execute(
                "SELECT source_host_id,source_generation,target_generation,continuity_epoch,subject_sequence_anchor,state_digest,content_digest,bundle_digest,migration_chain,created_at,phase "
                "FROM continuity_transfer WHERE transfer_uuid=? AND subject_uuid=? AND role='target'",
                (transfer_uuid, subject_uuid),
            ).fetchone()
            if audit is None or str(audit[10]) != "staged":
                raise WriterLeaseError("target transfer is not staged")
            checks = {
                "source_host_id": str(audit[0]),
                "source_generation": int(audit[1]),
                "target_generation": int(audit[2]),
                "continuity_epoch": int(audit[3]),
                "subject_sequence_anchor": int(audit[4]),
                "state_digest": str(audit[5]),
                "content_digest": str(audit[6]),
                "bundle_digest": str(audit[7]),
            }
            for key, expected in checks.items():
                if str(final_receipt.get(key)) != str(expected):
                    raise WriterLeaseError(f"final receipt mismatch for {key}")
            if int(audit[3]) != epoch:
                raise WriterLeaseError("target continuity epoch mismatch")
            if str(local_state_digest or "") != str(audit[5]):
                raise WriterLeaseError("target state does not match disconnected transfer boundary")
            current_content = self._subject_transfer_content_conn(conn, subject_uuid, epoch)
            if self._transfer_content_digest(current_content) != str(audit[6]):
                raise WriterLeaseError("staged target content changed before activation")
            writer = conn.execute(
                "SELECT active_host_id,writer_generation FROM continuity_writer WHERE subject_uuid=?",
                (subject_uuid,),
            ).fetchone()
            if writer is None or str(writer[0]) != str(audit[0]) or int(writer[1]) != int(audit[1]):
                raise WriterLeaseError("staged target writer fence no longer matches source generation")
            cur = conn.execute(
                "UPDATE continuity_writer SET active_host_id=?,writer_generation=?,updated_at=? "
                "WHERE subject_uuid=? AND active_host_id=? AND writer_generation=?",
                (self.host_id, int(audit[2]), now, subject_uuid, str(audit[0]), int(audit[1])),
            )
            if int(cur.rowcount or 0) != 1:
                raise WriterLeaseError("target activation lost the writer fencing race")
            prior_chain = json.loads(audit[8]) if audit[8] else []
            if not isinstance(prior_chain, list):
                prior_chain = []
            descriptor = {
                "transfer_uuid": transfer_uuid,
                "source_host_id": str(audit[0]),
                "target_host_id": self.host_id,
                "source_generation": int(audit[1]),
                "target_generation": int(audit[2]),
                "continuity_epoch": epoch,
                "subject_sequence_anchor": int(audit[4]),
                "bundle_digest": str(audit[7]),
                "state_digest": str(audit[5]),
                "created_at": float(audit[9]),
                "activated_at": now,
            }
            migration_chain = prior_chain + [descriptor]
            conn.execute(
                "UPDATE continuity_transfer SET phase='activated',migration_chain=?,updated_at=? "
                "WHERE transfer_uuid=? AND role='target'",
                (json.dumps(migration_chain, ensure_ascii=False), now, transfer_uuid),
            )
        self._writer_claims[subject_uuid] = int(final_receipt["target_generation"])
        return self.writer_status(character_id, user_id)

    # ---------------- state snapshots ----------------
    def save(self, character_id: str, user_id: str, key: str, value):
        with self._connection() as conn:
            self._fence_writer_conn(conn, character_id, user_id)
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
            self._fence_writer_conn(conn, character_id, user_id)
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
            self._fence_writer_conn(conn, character_id, user_id)
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
            self._fence_writer_conn(conn, character_id, user_id)
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
            self._fence_writer_conn(conn, character_id, user_id)
            removed = self._prune_diagnostic_events_conn(conn, character_id, user_id)
        self._diagnostic_writes_since_prune[(str(character_id), str(user_id))] = 0
        return removed

    def prune_consolidation_evidence(self, character_id: str, user_id: str, through: float) -> int:
        """Discard semantic evidence already committed into the belief ledger."""

        with self._connection() as conn:
            self._fence_writer_conn(conn, character_id, user_id)
            cur = conn.execute(
                "DELETE FROM consolidation_evidence WHERE character_id=? AND user_id=? AND created_at<=?",
                (character_id, user_id, float(through)),
            )
            return max(0, int(cur.rowcount or 0))

    def commit_belief_consolidation(
        self,
        character_id: str,
        user_id: str,
        timestep: int,
        *,
        belief_state: dict[str, Any],
        evidence_through: float,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        """Atomically commit one causally relevant slow-belief boundary.

        The belief snapshot, canonical boundary, and evidence-window consumption
        are one SQLite transaction. The boundary is diagnostic/canonical history,
        not fresh evidence for the next belief pass.
        """

        payload = dict(payload or {})
        if not canonical_continuity_root_eligible("belief_consolidation", payload):
            raise ValueError("invalid belief_consolidation causal root")
        now = time.time()
        with self._connection() as conn:
            self._fence_writer_conn(conn, character_id, user_id)
            conn.execute(
                "INSERT INTO state (character_id,user_id,key,value,updated_at) VALUES(?,?,?,?,?) "
                "ON CONFLICT(character_id,user_id,key) DO UPDATE SET value=excluded.value, updated_at=excluded.updated_at",
                (character_id, user_id, "belief_ledger", json.dumps(belief_state, ensure_ascii=False), now),
            )
            cur = conn.execute(
                "INSERT INTO event_log (character_id,user_id,timestep,event_type,payload,created_at) VALUES (?,?,?,?,?,?)",
                (character_id, user_id, timestep, "belief_consolidation", json.dumps(payload, ensure_ascii=False), now),
            )
            event = self._append_continuity_event_conn(
                conn,
                character_id=character_id,
                user_id=user_id,
                timestep=timestep,
                event_type="belief_consolidation",
                payload=payload,
                wall_time=now,
                legacy_event_id=int(cur.lastrowid),
                payload_schema="belief-consolidation-v1",
            )
            conn.execute(
                "DELETE FROM consolidation_evidence WHERE character_id=? AND user_id=? AND created_at<=?",
                (character_id, user_id, float(evidence_through)),
            )
            if self.diagnostic_event_limit is not None:
                self._prune_diagnostic_events_conn(conn, character_id, user_id)
                self._diagnostic_writes_since_prune[(str(character_id), str(user_id))] = 0
        return event.to_dict()

    def log_event(
        self,
        character_id: str,
        user_id: str,
        timestep: int,
        event_type: str,
        payload: dict,
        *,
        continuity_payload: dict[str, Any] | None = None,
        continuity_payload_schema: str | None = None,
    ):
        """Write diagnostics plus the minimum-sufficient durable causal root.

        ``payload`` remains the rich recent diagnostic packet. New canonical
        history is intentionally narrower and may receive a separate exogenous
        root payload. Historical v1 readers remain able to consume older derived
        canonical rows.
        """

        now = time.time()
        payload = dict(payload or {})
        root_payload = dict(continuity_payload) if continuity_payload is not None else dict(payload)
        with self._connection() as conn:
            self._fence_writer_conn(conn, character_id, user_id)
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
            if canonical_continuity_root_eligible(event_type, root_payload):
                self._append_continuity_event_conn(
                    conn,
                    character_id=character_id,
                    user_id=user_id,
                    timestep=timestep,
                    event_type=event_type,
                    payload=root_payload,
                    wall_time=now,
                    legacy_event_id=legacy_id,
                    payload_schema=continuity_payload_schema,
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
            self._fence_writer_conn(conn, character_id, user_id)
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
            self._fence_writer_conn(conn, character_id, user_id)
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
                # Legacy diagnostic migration keeps only causal roots. Older
                # continuity tables that already contain derived v1 rows remain
                # readable; this prevents a fresh migration from recreating the
                # redundancy that root-only persistence removes.
                if not isinstance(payload, dict) or not canonical_continuity_root_eligible(str(event_type), payload):
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
            self._fence_writer_conn(conn, character_id, user_id)
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
