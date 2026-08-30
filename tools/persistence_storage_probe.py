#!/usr/bin/env python3
"""Measure where Wayfarer's persistent bytes accumulate over a long life.

This probe changes no runtime policy. It exercises the production CharacterAgent,
then inventories SQLite row counts, logical text/payload bytes, physical page
allocation when dbstat is available, event-type distribution, canonical/diagnostic
payload duplication, and checkpoint overhead.
"""

from __future__ import annotations

import argparse
import json
import os
import sqlite3
import tempfile
from pathlib import Path

from persona_engine.agent import CharacterAgent

ROOT = Path(__file__).resolve().parents[1]
CART = ROOT / "persona_engine" / "cartridges" / "pretorius.snp"
DEFAULT_TURNS = 1000


def _scalar(conn: sqlite3.Connection, sql: str, params=()):
    row = conn.execute(sql, params).fetchone()
    return row[0] if row else 0


def _table_metrics(conn: sqlite3.Connection, table: str, text_columns: tuple[str, ...]) -> dict:
    count = int(_scalar(conn, f"SELECT COUNT(*) FROM {table}") or 0)
    logical = 0
    by_column: dict[str, int] = {}
    for column in text_columns:
        value = int(_scalar(conn, f"SELECT COALESCE(SUM(LENGTH(CAST({column} AS BLOB))),0) FROM {table}") or 0)
        by_column[column] = value
        logical += value
    return {"rows": count, "logical_text_bytes": logical, "text_column_bytes": by_column}


def _by_event_type(conn: sqlite3.Connection, table: str) -> list[dict]:
    rows = conn.execute(
        f"SELECT event_type, COUNT(*), COALESCE(SUM(LENGTH(CAST(payload AS BLOB))),0), "
        f"COALESCE(AVG(LENGTH(CAST(payload AS BLOB))),0) "
        f"FROM {table} GROUP BY event_type ORDER BY 3 DESC, event_type"
    ).fetchall()
    return [
        {
            "event_type": str(event_type),
            "rows": int(count),
            "payload_bytes": int(payload_bytes),
            "average_payload_bytes": round(float(avg_bytes), 2),
        }
        for event_type, count, payload_bytes, avg_bytes in rows
    ]


def _dbstat_pages(conn: sqlite3.Connection) -> tuple[bool, dict[str, int]]:
    try:
        rows = conn.execute(
            "SELECT name, COALESCE(SUM(pgsize),0) FROM dbstat GROUP BY name ORDER BY 2 DESC"
        ).fetchall()
    except sqlite3.DatabaseError:
        return False, {}
    return True, {str(name): int(size) for name, size in rows}


def run(turns: int = DEFAULT_TURNS) -> dict:
    turns = max(1, int(turns))
    with tempfile.TemporaryDirectory() as directory:
        db = str(Path(directory) / "state.db")
        agent = CharacterAgent(cartridge_path=str(CART), user_id="storage_probe", db_path=db)

        # Preserve the same kinds of durable state that matter in the production
        # plateau test while adding routine life-history pressure.
        agent.say("Please remember this neutral detail: the archive lamp is amber.")
        agent.say("You lied to me. This is your fault.")
        agent.say("You lied to me again. This is your fault too.")
        agent.adopt_commitment("non_disclosure", "project orchid")
        for index in range(1, turns + 1):
            agent.say(f"Persistence storage note {index}: shelf marker {index} is ordinary.")

        # Ensure all completed transactions are visible before inventory.
        conn = sqlite3.connect(db)
        try:
            page_size = int(_scalar(conn, "PRAGMA page_size") or 0)
            page_count = int(_scalar(conn, "PRAGMA page_count") or 0)
            freelist_count = int(_scalar(conn, "PRAGMA freelist_count") or 0)
            journal_mode = str(_scalar(conn, "PRAGMA journal_mode") or "")

            tables = {
                "state": _table_metrics(conn, "state", ("character_id", "user_id", "key", "value")),
                "subject_state": _table_metrics(conn, "subject_state", ("subject_uuid", "key", "value")),
                "event_log": _table_metrics(conn, "event_log", ("character_id", "user_id", "event_type", "payload")),
                "continuity_subject": _table_metrics(conn, "continuity_subject", ("character_id", "user_id", "subject_uuid")),
                "continuity_event": _table_metrics(
                    conn,
                    "continuity_event",
                    (
                        "event_uuid", "subject_uuid", "character_id", "user_id", "source_actor", "source_class",
                        "authority_class", "event_type", "visibility", "canonicality", "causal_parents",
                        "payload_schema", "payload",
                    ),
                ),
                "continuity_checkpoint": _table_metrics(
                    conn,
                    "continuity_checkpoint",
                    ("subject_uuid", "character_id", "user_id", "state_schema", "state_digest"),
                ),
            }
            event_log_by_type = _by_event_type(conn, "event_log")
            continuity_by_type = _by_event_type(conn, "continuity_event")

            duplicate = conn.execute(
                "SELECT COUNT(*), "
                "COALESCE(SUM(LENGTH(CAST(e.payload AS BLOB))),0), "
                "COALESCE(SUM(LENGTH(CAST(c.payload AS BLOB))),0), "
                "COALESCE(SUM(CASE WHEN e.payload=c.payload THEN LENGTH(CAST(c.payload AS BLOB)) ELSE 0 END),0) "
                "FROM continuity_event c JOIN event_log e ON e.id=c.legacy_event_id "
                "WHERE c.legacy_event_id IS NOT NULL"
            ).fetchone()
            duplicate_rows = int(duplicate[0] or 0)
            diagnostic_copy_bytes = int(duplicate[1] or 0)
            canonical_copy_bytes = int(duplicate[2] or 0)
            exact_duplicate_payload_bytes = int(duplicate[3] or 0)

            dbstat_available, object_pages = _dbstat_pages(conn)
            file_bytes = os.path.getsize(db)
            allocated_bytes = page_size * page_count
            free_bytes = page_size * freelist_count

            total_logical_text = sum(item["logical_text_bytes"] for item in tables.values())
            result = {
                "probe": "persistence-storage-v1",
                "turns": turns,
                "production_policy_changed": False,
                "database": {
                    "file_bytes": file_bytes,
                    "page_size": page_size,
                    "page_count": page_count,
                    "allocated_bytes": allocated_bytes,
                    "freelist_pages": freelist_count,
                    "freelist_bytes": free_bytes,
                    "journal_mode": journal_mode,
                    "dbstat_available": dbstat_available,
                    "physical_bytes_by_object": object_pages,
                    "logical_text_bytes_across_measured_columns": total_logical_text,
                },
                "tables": tables,
                "event_log_by_type": event_log_by_type,
                "continuity_event_by_type": continuity_by_type,
                "canonical_diagnostic_duplication": {
                    "linked_canonical_rows": duplicate_rows,
                    "diagnostic_payload_bytes_for_linked_rows": diagnostic_copy_bytes,
                    "canonical_payload_bytes_for_linked_rows": canonical_copy_bytes,
                    "exact_duplicate_payload_bytes": exact_duplicate_payload_bytes,
                },
                "derived": {
                    "file_bytes_per_exercised_turn": round(file_bytes / turns, 2),
                    "event_log_rows_per_exercised_turn": round(tables["event_log"]["rows"] / turns, 3),
                    "continuity_rows_per_exercised_turn": round(tables["continuity_event"]["rows"] / turns, 3),
                    "checkpoint_rows_per_exercised_turn": round(tables["continuity_checkpoint"]["rows"] / turns, 3),
                    "event_log_payload_fraction_of_file": round(
                        tables["event_log"]["text_column_bytes"]["payload"] / file_bytes, 4
                    ) if file_bytes else 0.0,
                    "continuity_payload_fraction_of_file": round(
                        tables["continuity_event"]["text_column_bytes"]["payload"] / file_bytes, 4
                    ) if file_bytes else 0.0,
                    "exact_duplicate_payload_fraction_of_file": round(exact_duplicate_payload_bytes / file_bytes, 4) if file_bytes else 0.0,
                },
                "interpretation": (
                    "This probe measures storage ownership, not a proposed retention policy. The broad diagnostic journal, "
                    "canonical continuity ledger, current snapshots, and digest checkpoints are reported separately so any "
                    "future persistence optimization can preserve the semantic consumer that justified each byte."
                ),
            }
            return result
        finally:
            conn.close()


def markdown(result: dict) -> str:
    db = result["database"]
    lines = [
        "# Persistence Storage Probe",
        "",
        f"Production policy changed: `{result['production_policy_changed']}`.  ",
        f"Exercised turns: `{result['turns']:,}`.  ",
        f"SQLite file: `{db['file_bytes']:,} B`.  ",
        f"Logical text in measured columns: `{db['logical_text_bytes_across_measured_columns']:,} B`.  ",
        f"dbstat available: `{db['dbstat_available']}`.",
        "",
        "## Table inventory",
        "",
        "| Table | Rows | Logical text bytes |",
        "| --- | ---: | ---: |",
    ]
    for name, item in result["tables"].items():
        lines.append(f"| {name} | {item['rows']:,} | {item['logical_text_bytes']:,} |")
    lines.extend([
        "",
        "## Broad diagnostic journal by event type",
        "",
        "| Event type | Rows | Payload bytes | Average payload |",
        "| --- | ---: | ---: | ---: |",
    ])
    for item in result["event_log_by_type"]:
        lines.append(
            f"| {item['event_type']} | {item['rows']:,} | {item['payload_bytes']:,} | {item['average_payload_bytes']:,.1f} |"
        )
    lines.extend([
        "",
        "## Canonical continuity by event type",
        "",
        "| Event type | Rows | Payload bytes | Average payload |",
        "| --- | ---: | ---: | ---: |",
    ])
    for item in result["continuity_event_by_type"]:
        lines.append(
            f"| {item['event_type']} | {item['rows']:,} | {item['payload_bytes']:,} | {item['average_payload_bytes']:,.1f} |"
        )
    dup = result["canonical_diagnostic_duplication"]
    lines.extend([
        "",
        "## Canonical/diagnostic duplication",
        "",
        f"Linked canonical rows: `{dup['linked_canonical_rows']:,}`.  ",
        f"Diagnostic payload bytes for linked rows: `{dup['diagnostic_payload_bytes_for_linked_rows']:,}`.  ",
        f"Canonical payload bytes for linked rows: `{dup['canonical_payload_bytes_for_linked_rows']:,}`.  ",
        f"Exact duplicated payload bytes: `{dup['exact_duplicate_payload_bytes']:,}`.",
        "",
        result["interpretation"],
    ])
    if db["dbstat_available"]:
        lines.extend([
            "",
            "## Physical SQLite allocation by object",
            "",
            "| Object | Bytes |",
            "| --- | ---: |",
        ])
        for name, size in sorted(db["physical_bytes_by_object"].items(), key=lambda item: (-item[1], item[0])):
            lines.append(f"| {name} | {size:,} |")
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--turns", type=int, default=DEFAULT_TURNS)
    parser.add_argument("--json")
    parser.add_argument("--markdown")
    args = parser.parse_args()
    result = run(args.turns)
    rendered = json.dumps(result, indent=2, sort_keys=True)
    print(rendered)
    if args.json:
        path = Path(args.json)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(rendered + "\n", encoding="utf-8")
    if args.markdown:
        path = Path(args.markdown)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(markdown(result), encoding="utf-8")


if __name__ == "__main__":
    main()
