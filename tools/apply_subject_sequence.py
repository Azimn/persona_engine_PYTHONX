#!/usr/bin/env python3
"""Apply the minimum subject-wide canonical ordering repair.

This is intentionally a one-time integration helper. It preserves the existing
per-interlocutor ``sequence`` contract and adds only a storage-level
``subject_sequence`` ordinal for one individual's canonical biography.
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PERSISTENCE = ROOT / "persona_engine" / "core" / "persistence.py"
TEST_FILE = ROOT / "persona_engine" / "tests" / "test_subject_sequence.py"
PROBE = ROOT / "tools" / "subject_history_order_probe.py"


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected one exact anchor, found {count}")
    return text.replace(old, new, 1)


def patch_persistence() -> None:
    text = PERSISTENCE.read_text(encoding="utf-8")

    text = replace_once(
        text,
        "    sequence INTEGER NOT NULL,\n    continuity_epoch INTEGER NOT NULL DEFAULT 0,",
        "    sequence INTEGER NOT NULL,\n    subject_sequence INTEGER,\n    continuity_epoch INTEGER NOT NULL DEFAULT 0,",
        "schema subject_sequence column",
    )

    text = replace_once(
        text,
        "        with self._connection() as conn:\n            conn.executescript(SCHEMA)\n\n    def _connect(self):",
        "        with self._connection() as conn:\n            conn.executescript(SCHEMA)\n            self._ensure_subject_sequence_schema_conn(conn)\n\n"
        "    def _ensure_subject_sequence_schema_conn(self, conn) -> None:\n"
        "        \"\"\"Add/backfill the subject-owned ordinal without changing stream sequence.\n\n"
        "        Existing databases predate ``subject_sequence``. Their canonical rows\n"
        "        are deterministically ordered by recorded wall time then insertion id\n"
        "        for the one-time migration. New events allocate the next ordinal inside\n"
        "        the same SQLite transaction as the canonical insert.\n"
        "        \"\"\"\n\n"
        "        columns = {str(row[1]) for row in conn.execute(\"PRAGMA table_info(continuity_event)\").fetchall()}\n"
        "        if \"subject_sequence\" not in columns:\n"
        "            conn.execute(\"ALTER TABLE continuity_event ADD COLUMN subject_sequence INTEGER\")\n"
        "            groups = conn.execute(\n"
        "                \"SELECT DISTINCT subject_uuid,continuity_epoch FROM continuity_event ORDER BY subject_uuid,continuity_epoch\"\n"
        "            ).fetchall()\n"
        "            for subject_uuid, epoch in groups:\n"
        "                rows = conn.execute(\n"
        "                    \"SELECT id FROM continuity_event WHERE subject_uuid=? AND continuity_epoch=? ORDER BY wall_time,id\",\n"
        "                    (subject_uuid, epoch),\n"
        "                ).fetchall()\n"
        "                for ordinal, (row_id,) in enumerate(rows, start=1):\n"
        "                    conn.execute(\n"
        "                        \"UPDATE continuity_event SET subject_sequence=? WHERE id=?\",\n"
        "                        (ordinal, row_id),\n"
        "                    )\n"
        "        else:\n"
        "            groups = conn.execute(\n"
        "                \"SELECT DISTINCT subject_uuid,continuity_epoch FROM continuity_event WHERE subject_sequence IS NULL ORDER BY subject_uuid,continuity_epoch\"\n"
        "            ).fetchall()\n"
        "            for subject_uuid, epoch in groups:\n"
        "                row = conn.execute(\n"
        "                    \"SELECT COALESCE(MAX(subject_sequence),0) FROM continuity_event WHERE subject_uuid=? AND continuity_epoch=?\",\n"
        "                    (subject_uuid, epoch),\n"
        "                ).fetchone()\n"
        "                next_ordinal = int(row[0] or 0) + 1\n"
        "                rows = conn.execute(\n"
        "                    \"SELECT id FROM continuity_event WHERE subject_uuid=? AND continuity_epoch=? AND subject_sequence IS NULL ORDER BY wall_time,id\",\n"
        "                    (subject_uuid, epoch),\n"
        "                ).fetchall()\n"
        "                for offset, (row_id,) in enumerate(rows):\n"
        "                    conn.execute(\n"
        "                        \"UPDATE continuity_event SET subject_sequence=? WHERE id=?\",\n"
        "                        (next_ordinal + offset, row_id),\n"
        "                    )\n"
        "        conn.execute(\n"
        "            \"CREATE UNIQUE INDEX IF NOT EXISTS idx_continuity_subject_global_sequence \"\n"
        "            \"ON continuity_event(subject_uuid,continuity_epoch,subject_sequence) \"\n"
        "            \"WHERE subject_sequence IS NOT NULL\"\n"
        "        )\n\n"
        "    def _connect(self):",
        "initialization migration hook",
    )

    text = replace_once(
        text,
        "    def _next_sequence_conn(self, conn, subject_uuid: str, user_id: str, continuity_epoch: int) -> int:\n"
        "        row = conn.execute(\n"
        "            \"SELECT COALESCE(MAX(sequence),0) FROM continuity_event WHERE subject_uuid=? AND user_id=? AND continuity_epoch=?\",\n"
        "            (subject_uuid, user_id, continuity_epoch),\n"
        "        ).fetchone()\n"
        "        return int(row[0] or 0) + 1\n\n",
        "    def _next_sequence_conn(self, conn, subject_uuid: str, user_id: str, continuity_epoch: int) -> int:\n"
        "        row = conn.execute(\n"
        "            \"SELECT COALESCE(MAX(sequence),0) FROM continuity_event WHERE subject_uuid=? AND user_id=? AND continuity_epoch=?\",\n"
        "            (subject_uuid, user_id, continuity_epoch),\n"
        "        ).fetchone()\n"
        "        return int(row[0] or 0) + 1\n\n"
        "    def _next_subject_sequence_conn(self, conn, subject_uuid: str, continuity_epoch: int) -> int:\n"
        "        row = conn.execute(\n"
        "            \"SELECT COALESCE(MAX(subject_sequence),0) FROM continuity_event WHERE subject_uuid=? AND continuity_epoch=?\",\n"
        "            (subject_uuid, continuity_epoch),\n"
        "        ).fetchone()\n"
        "        return int(row[0] or 0) + 1\n\n",
        "subject sequence allocator",
    )

    text = replace_once(
        text,
        "        sequence = sequence or self._next_sequence_conn(conn, subject_uuid, user_id, epoch)\n        authority = event_authority(event_type, payload)",
        "        sequence = sequence or self._next_sequence_conn(conn, subject_uuid, user_id, epoch)\n"
        "        subject_sequence = self._next_subject_sequence_conn(conn, subject_uuid, epoch)\n"
        "        authority = event_authority(event_type, payload)",
        "append subject ordinal allocation",
    )

    text = replace_once(
        text,
        "            \"INSERT INTO continuity_event(event_uuid,subject_uuid,character_id,user_id,sequence,continuity_epoch,subject_time,wall_time,source_actor,source_class,authority_class,event_type,visibility,canonicality,causal_parents,payload_schema,payload,legacy_event_id) \"\n"
        "            \"VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)\",",
        "            \"INSERT INTO continuity_event(event_uuid,subject_uuid,character_id,user_id,sequence,subject_sequence,continuity_epoch,subject_time,wall_time,source_actor,source_class,authority_class,event_type,visibility,canonicality,causal_parents,payload_schema,payload,legacy_event_id) \"\n"
        "            \"VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)\",",
        "canonical insert columns",
    )

    text = replace_once(
        text,
        "                event.sequence,\n                event.continuity_epoch,",
        "                event.sequence,\n                subject_sequence,\n                event.continuity_epoch,",
        "canonical insert values",
    )

    text = replace_once(
        text,
        "            \"event_uuid\": row[0], \"subject_uuid\": row[1], \"character_id\": row[2], \"user_id\": row[3],\n"
        "            \"sequence\": row[4], \"continuity_epoch\": row[5], \"subject_time\": row[6], \"wall_time\": row[7],\n"
        "            \"source_actor\": row[8], \"source_class\": row[9], \"authority_class\": row[10], \"event_type\": row[11],\n"
        "            \"visibility\": row[12], \"canonicality\": row[13], \"causal_parents\": json.loads(row[14]),\n"
        "            \"payload_schema\": row[15], \"payload\": json.loads(row[16]), \"legacy_event_id\": row[17],",
        "            \"event_uuid\": row[0], \"subject_uuid\": row[1], \"character_id\": row[2], \"user_id\": row[3],\n"
        "            \"sequence\": row[4], \"subject_sequence\": row[5], \"continuity_epoch\": row[6], \"subject_time\": row[7], \"wall_time\": row[8],\n"
        "            \"source_actor\": row[9], \"source_class\": row[10], \"authority_class\": row[11], \"event_type\": row[12],\n"
        "            \"visibility\": row[13], \"canonicality\": row[14], \"causal_parents\": json.loads(row[15]),\n"
        "            \"payload_schema\": row[16], \"payload\": json.loads(row[17]), \"legacy_event_id\": row[18],",
        "row decoding",
    )

    old_select = "SELECT event_uuid,subject_uuid,character_id,user_id,sequence,continuity_epoch,subject_time,wall_time,source_actor,source_class,authority_class,event_type,visibility,canonicality,causal_parents,payload_schema,payload,legacy_event_id "
    new_select = "SELECT event_uuid,subject_uuid,character_id,user_id,sequence,subject_sequence,continuity_epoch,subject_time,wall_time,source_actor,source_class,authority_class,event_type,visibility,canonicality,causal_parents,payload_schema,payload,legacy_event_id "
    count = text.count(old_select)
    if count != 2:
        raise SystemExit(f"full continuity SELECT anchors: expected 2, found {count}")
    text = text.replace(old_select, new_select)

    text = replace_once(
        text,
        "        This reader does not redefine sequence semantics. Current M3 streams are\n"
        "        still sequenced per interlocutor, so cross-interlocutor results are ordered\n"
        "        by wall time then insertion id. Global subject ordering is a separate\n"
        "        property that must be tested before changing the ledger contract.",
        "        The existing ``sequence`` remains a per-interlocutor compatibility stream.\n"
        "        ``subject_sequence`` is the additive subject-owned canonical ordinal and is\n"
        "        therefore the ordering key for this cross-interlocutor reader.",
        "subject reader doc",
    )

    text = replace_once(
        text,
        "        query += \" ORDER BY wall_time,id\"",
        "        query += \" ORDER BY subject_sequence\"",
        "subject reader ordering",
    )

    text = replace_once(
        text,
        "    def export_continuity_tail(self, character_id: str, user_id: str, after_sequence: int = 0) -> dict[str, Any]:\n"
        "        subject_uuid, epoch = self._resolve_subject(character_id, user_id)\n"
        "        return {\n"
        "            \"schema_version\": CONTINUITY_SCHEMA_VERSION,\n"
        "            \"subject_uuid\": subject_uuid,\n"
        "            \"character_id\": character_id,\n"
        "            \"user_id\": user_id,\n"
        "            \"continuity_epoch\": epoch,\n"
        "            \"after_sequence\": int(after_sequence),\n"
        "            \"events\": self.load_continuity_events(character_id, user_id, after_sequence=int(after_sequence), continuity_epoch=epoch),\n"
        "            \"checkpoint\": self.latest_checkpoint(character_id, user_id),\n"
        "        }",
        "    def export_continuity_tail(self, character_id: str, user_id: str, after_sequence: int = 0) -> dict[str, Any]:\n"
        "        subject_uuid, epoch = self._resolve_subject(character_id, user_id)\n"
        "        events = self.load_continuity_events(character_id, user_id, after_sequence=int(after_sequence), continuity_epoch=epoch)\n"
        "        # v1 interchange remains the established per-interlocutor stream contract.\n"
        "        # The additive subject ordinal stays local until a subject-wide transfer\n"
        "        # experiment earns a versioned portable representation for it.\n"
        "        export_events = [{key: value for key, value in event.items() if key != \"subject_sequence\"} for event in events]\n"
        "        return {\n"
        "            \"schema_version\": CONTINUITY_SCHEMA_VERSION,\n"
        "            \"subject_uuid\": subject_uuid,\n"
        "            \"character_id\": character_id,\n"
        "            \"user_id\": user_id,\n"
        "            \"continuity_epoch\": epoch,\n"
        "            \"after_sequence\": int(after_sequence),\n"
        "            \"events\": export_events,\n"
        "            \"checkpoint\": self.latest_checkpoint(character_id, user_id),\n"
        "        }",
        "v1 export compatibility",
    )

    PERSISTENCE.write_text(text, encoding="utf-8")


def write_tests() -> None:
    TEST_FILE.write_text('''"""Minimum subject-wide canonical ordering contract."""\n\nimport json\nimport os\nimport sqlite3\nimport tempfile\nimport uuid\n\nfrom persona_engine.core.persistence import Persistence\n\n\ndef test_subject_sequence_orders_one_biography_without_replacing_stream_sequence():\n    with tempfile.TemporaryDirectory() as d:\n        p = Persistence(os.path.join(d, "state.db"))\n        subject_uuid = str(uuid.uuid4())\n        p.bind_subject("Character", "alice", subject_uuid)\n        p.bind_subject("Character", "bob", subject_uuid)\n\n        p.log_event("Character", "alice", 1, "input", {"text": "alice one"})\n        p.log_event("Character", "bob", 2, "input", {"text": "bob one"})\n        p.log_event("Character", "alice", 3, "state_transition", {"x": 1})\n\n        events = p.load_subject_continuity_events("Character", "alice")\n        assert [event["subject_sequence"] for event in events] == [1, 2, 3]\n        assert [(event["user_id"], event["sequence"]) for event in events] == [\n            ("alice", 1),\n            ("bob", 1),\n            ("alice", 2),\n        ]\n\n\ndef test_existing_pre_subject_sequence_database_is_backfilled_deterministically():\n    with tempfile.TemporaryDirectory() as d:\n        path = os.path.join(d, "legacy.db")\n        subject_uuid = str(uuid.uuid4())\n        conn = sqlite3.connect(path)\n        conn.execute(\n            """CREATE TABLE continuity_event (\n                id INTEGER PRIMARY KEY AUTOINCREMENT,\n                event_uuid TEXT NOT NULL UNIQUE,\n                subject_uuid TEXT NOT NULL,\n                character_id TEXT NOT NULL,\n                user_id TEXT NOT NULL,\n                sequence INTEGER NOT NULL,\n                continuity_epoch INTEGER NOT NULL DEFAULT 0,\n                subject_time REAL NOT NULL,\n                wall_time REAL NOT NULL,\n                source_actor TEXT NOT NULL,\n                source_class TEXT NOT NULL,\n                authority_class TEXT NOT NULL,\n                event_type TEXT NOT NULL,\n                visibility TEXT NOT NULL,\n                canonicality TEXT NOT NULL,\n                causal_parents TEXT NOT NULL,\n                payload_schema TEXT NOT NULL,\n                payload TEXT NOT NULL,\n                legacy_event_id INTEGER UNIQUE,\n                UNIQUE(subject_uuid, user_id, continuity_epoch, sequence)\n            )"""\n        )\n        rows = [\n            (str(uuid.uuid4()), subject_uuid, "Character", "alice", 1, 0, 1.0, 10.0, "user", "external_user", "reported_input", "input", "character_observed", "canonical_event", "[]", "legacy-event-v1", json.dumps({"text": "first"}), 1),\n            (str(uuid.uuid4()), subject_uuid, "Character", "bob", 1, 0, 2.0, 20.0, "user", "external_user", "reported_input", "input", "character_observed", "canonical_event", "[]", "legacy-event-v1", json.dumps({"text": "second"}), 2),\n            (str(uuid.uuid4()), subject_uuid, "Character", "alice", 2, 0, 3.0, 30.0, "user", "external_user", "reported_input", "input", "character_observed", "canonical_event", "[]", "legacy-event-v1", json.dumps({"text": "third"}), 3),\n        ]\n        conn.executemany(\n            "INSERT INTO continuity_event(event_uuid,subject_uuid,character_id,user_id,sequence,continuity_epoch,subject_time,wall_time,source_actor,source_class,authority_class,event_type,visibility,canonicality,causal_parents,payload_schema,payload,legacy_event_id) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",\n            rows,\n        )\n        conn.commit()\n        conn.close()\n\n        p = Persistence(path)\n        p.bind_subject("Character", "alice", subject_uuid)\n        events = p.load_subject_continuity_events("Character", "alice")\n        assert [event["subject_sequence"] for event in events] == [1, 2, 3]\n        assert [event["user_id"] for event in events] == ["alice", "bob", "alice"]\n\n\ndef test_v1_export_keeps_existing_stream_shape_without_subject_sequence():\n    with tempfile.TemporaryDirectory() as d:\n        p = Persistence(os.path.join(d, "state.db"))\n        subject_uuid = str(uuid.uuid4())\n        p.bind_subject("Character", "user", subject_uuid)\n        p.log_event("Character", "user", 1, "input", {"text": "hello"})\n\n        local_event = p.load_continuity_events("Character", "user")[0]\n        bundle_event = p.export_continuity_tail("Character", "user")["events"][0]\n\n        assert local_event["subject_sequence"] == 1\n        assert "subject_sequence" not in bundle_event\n        assert bundle_event["sequence"] == 1\n''', encoding="utf-8")


def write_probe() -> None:
    PROBE.write_text('''#!/usr/bin/env python3\n"""Probe whether one subject has one unambiguous canonical root-event order."""\n\nfrom __future__ import annotations\n\nimport argparse\nimport json\nimport tempfile\nfrom pathlib import Path\n\nfrom persona_engine.agent import CharacterAgent\n\nROOT = Path(__file__).resolve().parents[1]\nCART = ROOT / "persona_engine" / "cartridges" / "pretorius.snp"\n\n\ndef run() -> dict:\n    with tempfile.TemporaryDirectory() as d:\n        db = str(Path(d) / "shared.db")\n\n        alice1 = CharacterAgent(cartridge_path=str(CART), user_id="alice", db_path=db)\n        alice1.say("Alice first canonical turn.")\n\n        bob = CharacterAgent(cartridge_path=str(CART), user_id="bob", db_path=db)\n        bob.say("Bob canonical turn.")\n\n        alice2 = CharacterAgent(cartridge_path=str(CART), user_id="alice", db_path=db)\n        alice2.say("Alice second canonical turn.")\n\n        persistence = alice2.engine.persistence\n        events = persistence.load_subject_continuity_events(\n            alice2.engine.identity.name,\n            alice2.engine.user_id,\n            event_type="input",\n        )\n        all_events = persistence.load_subject_continuity_events(\n            alice2.engine.identity.name,\n            alice2.engine.user_id,\n        )\n        roots = [\n            {\n                "user_id": event["user_id"],\n                "sequence": int(event["sequence"]),\n                "subject_sequence": int(event["subject_sequence"]),\n                "wall_time": float(event["wall_time"]),\n                "event_uuid": event["event_uuid"],\n                "user_text": (event.get("payload") or {}).get("user_text"),\n            }\n            for event in events\n        ]\n        stream_sequences = [item["sequence"] for item in roots]\n        subject_sequences = [item["subject_sequence"] for item in roots]\n        all_subject_sequences = [int(event["subject_sequence"]) for event in all_events]\n        unique = len(subject_sequences) == len(set(subject_sequences))\n        strictly_increasing = all(b > a for a, b in zip(subject_sequences, subject_sequences[1:]))\n        all_contiguous = all_subject_sequences == list(range(1, len(all_subject_sequences) + 1))\n        same_subject = len({event["subject_uuid"] for event in all_events}) <= 1\n\n        if not same_subject:\n            diagnosis = "subject_identity_split"\n        elif unique and strictly_increasing and all_contiguous:\n            diagnosis = "subject_canonical_order_is_unambiguous"\n        else:\n            diagnosis = "subject_canonical_order_still_ambiguous"\n\n        return {\n            "probe": "subject-history-ordering-v2",\n            "roots": roots,\n            "stream_sequence_values": stream_sequences,\n            "subject_sequence_values": subject_sequences,\n            "all_subject_sequence_values": all_subject_sequences,\n            "same_subject_uuid": same_subject,\n            "subject_sequence_unique_across_interlocutors": unique,\n            "subject_sequence_strictly_increasing_across_interlocutors": strictly_increasing,\n            "subject_sequence_contiguous_across_all_canonical_events": all_contiguous,\n            "diagnosis": diagnosis,\n            "interpretation": (\n                "Per-interlocutor sequence remains available for v1 replay compatibility, while subject_sequence provides the single explicit canonical order for the continuing individual."\n            ),\n        }\n\n\ndef markdown(result: dict) -> str:\n    rows = "\\n".join(\n        f"| {index + 1} | `{item['user_id']}` | `{item['sequence']}` | `{item['subject_sequence']}` | `{item['user_text']}` |"\n        for index, item in enumerate(result["roots"])\n    )\n    return f"""# Subject-Wide Canonical Ordering Probe\n\nProbe: `{result['probe']}`\n\n| Subject encounter order | Interlocutor | Existing stream sequence | Subject sequence | Canonical input |\n| ---: | --- | ---: | ---: | --- |\n{rows}\n\nSubject UUID remains shared: `{result['same_subject_uuid']}`  \nSubject ordinals are unique across interlocutors: `{result['subject_sequence_unique_across_interlocutors']}`  \nSubject ordinals are strictly increasing across interlocutors: `{result['subject_sequence_strictly_increasing_across_interlocutors']}`  \nSubject ordinals are contiguous across all canonical events: `{result['subject_sequence_contiguous_across_all_canonical_events']}`  \nDiagnosis: `{result['diagnosis']}`\n\nThe existing `sequence` field remains the v1 per-interlocutor replay/export stream and is intentionally allowed to repeat across different interlocutors. The additive `subject_sequence` field is the minimum subject-owned ordering primitive. It gives one continuing individual one explicit canonical biography without turning relationship state into global state or replacing the established replay contract.\n"""\n\n\ndef main() -> None:\n    parser = argparse.ArgumentParser()\n    parser.add_argument("--json")\n    parser.add_argument("--markdown")\n    args = parser.parse_args()\n    result = run()\n    rendered = json.dumps(result, indent=2, sort_keys=True)\n    print(rendered)\n    if args.json:\n        path = Path(args.json)\n        path.parent.mkdir(parents=True, exist_ok=True)\n        path.write_text(rendered + "\\n", encoding="utf-8")\n    if args.markdown:\n        path = Path(args.markdown)\n        path.parent.mkdir(parents=True, exist_ok=True)\n        path.write_text(markdown(result), encoding="utf-8")\n\n\nif __name__ == "__main__":\n    main()\n''', encoding="utf-8")


def main() -> None:
    patch_persistence()
    write_tests()
    write_probe()
    print("Applied minimal subject-wide canonical ordinal repair")


if __name__ == "__main__":
    main()
