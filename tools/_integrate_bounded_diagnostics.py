#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
persistence_path = ROOT / "persona_engine" / "core" / "persistence.py"
engine_path = ROOT / "persona_engine" / "core" / "engine.py"
agent_path = ROOT / "persona_engine" / "agent.py"
dream_path = ROOT / "persona_engine" / "core" / "dream_engine.py"
probe_path = ROOT / "tools" / "persistence_storage_probe.py"
test_path = ROOT / "persona_engine" / "tests" / "test_bounded_diagnostic_persistence.py"

# ---------------------------------------------------------------------------
# persistence.py
# ---------------------------------------------------------------------------
p = persistence_path.read_text(encoding="utf-8")

anchor = 'SCHEMA = """\n'
insert = '''# Operational telemetry is not character cognition. The normal runtime keeps a\n# recent diagnostic window for debugging while direct Persistence callers retain\n# the legacy unlimited default for migration and tooling compatibility.\nDEFAULT_RUNTIME_DIAGNOSTIC_EVENT_LIMIT = 512\n\n\ndef _extract_evidence_types(event_type: str, payload: dict[str, Any]) -> list[str]:\n    """Return the exact semantic counters consumed by slow consolidation."""\n\n    types: list[str] = []\n    trigger = payload.get("trigger_memory_type") if isinstance(payload, dict) else None\n    if trigger:\n        types.append(str(trigger))\n    if isinstance(payload, dict):\n        for item in payload.get("memory_types", []) or []:\n            types.append(str(item))\n    if not types:\n        types.append(str(event_type))\n    return types\n\n\nSCHEMA = """\n'''
if anchor not in p:
    raise SystemExit("SCHEMA anchor not found")
p = p.replace(anchor, insert, 1)

continuity_anchor = '''CREATE TABLE IF NOT EXISTS continuity_subject (\n'''
consolidation_schema = '''CREATE TABLE IF NOT EXISTS consolidation_evidence (\n    id INTEGER PRIMARY KEY AUTOINCREMENT,\n    legacy_event_id INTEGER NOT NULL UNIQUE,\n    character_id TEXT NOT NULL,\n    user_id TEXT NOT NULL,\n    evidence_types TEXT NOT NULL,\n    created_at REAL NOT NULL\n);\nCREATE INDEX IF NOT EXISTS idx_consolidation_evidence_stream_time\n    ON consolidation_evidence(character_id, user_id, created_at);\nCREATE TABLE IF NOT EXISTS continuity_subject (\n'''
if continuity_anchor not in p:
    raise SystemExit("continuity schema anchor not found")
p = p.replace(continuity_anchor, consolidation_schema, 1)

old_init = '''class Persistence:\n    def __init__(self, path: str = "persona_state.db"):\n        self.path = path\n        self._subject_bindings: dict[tuple[str, str], tuple[str, int]] = {}\n        with self._connection() as conn:\n            conn.executescript(SCHEMA)\n            self._ensure_subject_sequence_schema_conn(conn)\n'''
new_init = '''class Persistence:\n    def __init__(self, path: str = "persona_state.db", diagnostic_event_limit: int | None = None):\n        self.path = path\n        self.diagnostic_event_limit = None if diagnostic_event_limit is None else max(1, int(diagnostic_event_limit))\n        self._subject_bindings: dict[tuple[str, str], tuple[str, int]] = {}\n        with self._connection() as conn:\n            conn.executescript(SCHEMA)\n            self._ensure_subject_sequence_schema_conn(conn)\n            # Migrate semantic consolidation evidence before any runtime is\n            # allowed to prune verbose legacy diagnostics. Source event ids make\n            # this idempotent across interrupted upgrades and repeated startups.\n            self._backfill_consolidation_evidence_conn(conn)\n'''
if old_init not in p:
    raise SystemExit("Persistence __init__ anchor not found")
p = p.replace(old_init, new_init, 1)

ensure_end = '''        conn.execute(\n            "CREATE UNIQUE INDEX IF NOT EXISTS idx_continuity_subject_global_sequence "\n            "ON continuity_event(subject_uuid,continuity_epoch,subject_sequence) "\n            "WHERE subject_sequence IS NOT NULL"\n        )\n\n    def _connect(self):\n'''
ensure_replacement = '''        conn.execute(\n            "CREATE UNIQUE INDEX IF NOT EXISTS idx_continuity_subject_global_sequence "\n            "ON continuity_event(subject_uuid,continuity_epoch,subject_sequence) "\n            "WHERE subject_sequence IS NOT NULL"\n        )\n\n    def _backfill_consolidation_evidence_conn(self, conn) -> int:\n        """Copy compact semantic evidence from any legacy diagnostic rows once."""\n\n        rows = conn.execute(\n            "SELECT e.id,e.character_id,e.user_id,e.event_type,e.payload,e.created_at "\n            "FROM event_log e LEFT JOIN consolidation_evidence c ON c.legacy_event_id=e.id "\n            "WHERE c.legacy_event_id IS NULL ORDER BY e.id"\n        ).fetchall()\n        inserted = 0\n        for event_id, character_id, user_id, event_type, payload_text, created_at in rows:\n            try:\n                payload = json.loads(payload_text)\n            except (json.JSONDecodeError, TypeError):\n                payload = {}\n            if not isinstance(payload, dict):\n                payload = {}\n            types = _extract_evidence_types(str(event_type), payload)\n            conn.execute(\n                "INSERT OR IGNORE INTO consolidation_evidence "\n                "(legacy_event_id,character_id,user_id,evidence_types,created_at) VALUES(?,?,?,?,?)",\n                (int(event_id), str(character_id), str(user_id), json.dumps(types, ensure_ascii=False), float(created_at)),\n            )\n            inserted += 1\n        return inserted\n\n    def _connect(self):\n'''
if ensure_end not in p:
    raise SystemExit("subject sequence end anchor not found")
p = p.replace(ensure_end, ensure_replacement, 1)

bind_anchor = '''        with self._connection() as conn:\n            conn.execute(\n                "INSERT INTO continuity_subject(character_id,user_id,subject_uuid,continuity_epoch,updated_at) VALUES(?,?,?,?,?) "\n                "ON CONFLICT(character_id,user_id) DO UPDATE SET subject_uuid=excluded.subject_uuid, continuity_epoch=excluded.continuity_epoch, updated_at=excluded.updated_at",\n                (character_id, user_id, subject_uuid, continuity_epoch, time.time()),\n            )\n\n    def _resolve_subject(self, character_id: str, user_id: str) -> tuple[str, int]:\n'''
bind_replacement = '''        with self._connection() as conn:\n            conn.execute(\n                "INSERT INTO continuity_subject(character_id,user_id,subject_uuid,continuity_epoch,updated_at) VALUES(?,?,?,?,?) "\n                "ON CONFLICT(character_id,user_id) DO UPDATE SET subject_uuid=excluded.subject_uuid, continuity_epoch=excluded.continuity_epoch, updated_at=excluded.updated_at",\n                (character_id, user_id, subject_uuid, continuity_epoch, time.time()),\n            )\n        if self.diagnostic_event_limit is not None:\n            # A pre-M3 database may contain canonical experiences only in the\n            # legacy journal. Admit them to continuity before telemetry pruning.\n            self.backfill_legacy_events(character_id, user_id)\n            self.prune_diagnostic_events(character_id, user_id)\n\n    def _resolve_subject(self, character_id: str, user_id: str) -> tuple[str, int]:\n'''
if bind_anchor not in p:
    raise SystemExit("bind_subject anchor not found")
p = p.replace(bind_anchor, bind_replacement, 1)

log_anchor = '''    # ---------------- diagnostic + canonical event logging ----------------\n    def log_event(self, character_id: str, user_id: str, timestep: int, event_type: str, payload: dict):\n'''
log_helpers = '''    # ---------------- diagnostic + canonical event logging ----------------\n    def _prune_diagnostic_events_conn(self, conn, character_id: str, user_id: str) -> int:\n        limit = self.diagnostic_event_limit\n        if limit is None:\n            return 0\n        cutoff = conn.execute(\n            "SELECT id FROM event_log WHERE character_id=? AND user_id=? ORDER BY id DESC LIMIT 1 OFFSET ?",\n            (character_id, user_id, max(0, int(limit) - 1)),\n        ).fetchone()\n        if not cutoff:\n            return 0\n        cur = conn.execute(\n            "DELETE FROM event_log WHERE character_id=? AND user_id=? AND id<?",\n            (character_id, user_id, int(cutoff[0])),\n        )\n        return max(0, int(cur.rowcount or 0))\n\n    def prune_diagnostic_events(self, character_id: str, user_id: str) -> int:\n        """Bound recent operational telemetry without touching lived history."""\n\n        with self._connection() as conn:\n            return self._prune_diagnostic_events_conn(conn, character_id, user_id)\n\n    def prune_consolidation_evidence(self, character_id: str, user_id: str, through: float) -> int:\n        """Discard semantic evidence already committed into the belief ledger."""\n\n        with self._connection() as conn:\n            cur = conn.execute(\n                "DELETE FROM consolidation_evidence WHERE character_id=? AND user_id=? AND created_at<=?",\n                (character_id, user_id, float(through)),\n            )\n            return max(0, int(cur.rowcount or 0))\n\n    def log_event(self, character_id: str, user_id: str, timestep: int, event_type: str, payload: dict):\n'''
if log_anchor not in p:
    raise SystemExit("logging anchor not found")
p = p.replace(log_anchor, log_helpers, 1)

legacy_insert = '''            legacy_id = int(cur.lastrowid)\n            if canonical_continuity_eligible(event_type, payload):\n'''
evidence_insert = '''            legacy_id = int(cur.lastrowid)\n            conn.execute(\n                "INSERT INTO consolidation_evidence "\n                "(legacy_event_id,character_id,user_id,evidence_types,created_at) VALUES(?,?,?,?,?)",\n                (legacy_id, character_id, user_id, json.dumps(_extract_evidence_types(event_type, payload), ensure_ascii=False), now),\n            )\n            if canonical_continuity_eligible(event_type, payload):\n'''
if legacy_insert not in p:
    raise SystemExit("legacy id logging anchor not found")
p = p.replace(legacy_insert, evidence_insert, 1)

append_end = '''                    legacy_event_id=legacy_id,\n                )\n\n    def _next_sequence_conn'''
append_end_replacement = '''                    legacy_event_id=legacy_id,\n                )\n            self._prune_diagnostic_events_conn(conn, character_id, user_id)\n\n    def _next_sequence_conn'''
if append_end not in p:
    raise SystemExit("log_event end anchor not found")
p = p.replace(append_end, append_end_replacement, 1)

start = p.index('    def event_counts_since(')
end = p.index('    def load_events_since(', start)
new_counts = '''    def event_counts_since(self, character_id: str, user_id: str, since: float) -> dict[str, int]:\n        """Count compact semantic evidence after the supplied consolidation watermark.\n\n        This no longer depends on retaining verbose diagnostic payloads. Legacy\n        journals are backfilled into consolidation_evidence during Persistence\n        initialization before a bounded runtime can prune them.\n        """\n\n        conn = self._connect()\n        cur = conn.execute(\n            "SELECT evidence_types FROM consolidation_evidence "\n            "WHERE character_id=? AND user_id=? AND created_at>? ORDER BY id",\n            (character_id, user_id, float(since)),\n        )\n        counts: dict[str, int] = {}\n        try:\n            for (types_text,) in cur.fetchall():\n                try:\n                    types = json.loads(types_text)\n                except (json.JSONDecodeError, TypeError):\n                    types = []\n                if not isinstance(types, list):\n                    continue\n                for item in types:\n                    key = str(item)\n                    counts[key] = counts.get(key, 0) + 1\n            return counts\n        finally:\n            conn.close()\n\n'''
p = p[:start] + new_counts + p[end:]

p = p.replace(
    '        """Load diagnostic event-log payloads created after a wall-clock timestamp."""',
    '        """Load retained diagnostic payloads after a wall-clock timestamp.\\n\\n        Bounded runtimes expose recent telemetry only; canonical continuity is\\n        the authority for full lived history. Direct Persistence callers keep\\n        the legacy unlimited journal unless they opt into a limit.\\n        """',
    1,
)
persistence_path.write_text(p, encoding="utf-8")

# ---------------------------------------------------------------------------
# engine.py
# ---------------------------------------------------------------------------
e = engine_path.read_text(encoding="utf-8")
e = e.replace(
    'from .persistence import Persistence\n',
    'from .persistence import Persistence, DEFAULT_RUNTIME_DIAGNOSTIC_EVENT_LIMIT\n',
    1,
)
old_sig = '    def __init__(self, identity: CoreIdentity | None = None, user_id: str = "default_user", db_path: str = "persona_state.db", cartridge_path: str | None = None):\n'
new_sig = '    def __init__(self, identity: CoreIdentity | None = None, user_id: str = "default_user", db_path: str = "persona_state.db", cartridge_path: str | None = None, diagnostic_event_limit: int | None = DEFAULT_RUNTIME_DIAGNOSTIC_EVENT_LIMIT):\n'
if old_sig not in e:
    raise SystemExit("InteriorEngine signature anchor not found")
e = e.replace(old_sig, new_sig, 1)
e = e.replace('        self.persistence = Persistence(db_path)\n', '        self.persistence = Persistence(db_path, diagnostic_event_limit=diagnostic_event_limit)\n', 1)
engine_path.write_text(e, encoding="utf-8")

# ---------------------------------------------------------------------------
# agent.py
# ---------------------------------------------------------------------------
a = agent_path.read_text(encoding="utf-8")
a = a.replace(
    'from .core.vision_sensor import VisionObservation\n',
    'from .core.vision_sensor import VisionObservation\nfrom .core.persistence import DEFAULT_RUNTIME_DIAGNOSTIC_EVENT_LIMIT\n',
    1,
)
old_agent_sig = '    def __init__(self, identity: CoreIdentity | None = None, user_id: str = "default_user", db_path: str = "persona_state.db", cartridge_path: str | None = None):\n        self.engine = InteriorEngine(identity, user_id=user_id, db_path=db_path, cartridge_path=cartridge_path)\n'
new_agent_sig = '    def __init__(self, identity: CoreIdentity | None = None, user_id: str = "default_user", db_path: str = "persona_state.db", cartridge_path: str | None = None, diagnostic_event_limit: int | None = DEFAULT_RUNTIME_DIAGNOSTIC_EVENT_LIMIT):\n        self.engine = InteriorEngine(identity, user_id=user_id, db_path=db_path, cartridge_path=cartridge_path, diagnostic_event_limit=diagnostic_event_limit)\n'
if old_agent_sig not in a:
    raise SystemExit("CharacterAgent signature anchor not found")
a = a.replace(old_agent_sig, new_agent_sig, 1)
agent_path.write_text(a, encoding="utf-8")

# ---------------------------------------------------------------------------
# dream_engine.py
# ---------------------------------------------------------------------------
d = dream_path.read_text(encoding="utf-8")
old_dream = '''        counts = self.persistence.event_counts_since(character_id, user_id, since)\n        changed = self.belief_ledger.evaluate_rules(belief_rules, counts)\n        self.belief_ledger.last_consolidated = time.time()\n        self.persistence.save(character_id, user_id, "belief_ledger", self.belief_ledger.to_state())\n        return changed\n'''
new_dream = '''        counts = self.persistence.event_counts_since(character_id, user_id, since)\n        changed = self.belief_ledger.evaluate_rules(belief_rules, counts)\n        watermark = time.time()\n        self.belief_ledger.last_consolidated = watermark\n        # Persist the new watermark before pruning its source evidence. A crash\n        # after save but before prune is harmless because those rows fall behind\n        # the persisted watermark; pruning before save could lose evidence.\n        self.persistence.save(character_id, user_id, "belief_ledger", self.belief_ledger.to_state())\n        self.persistence.prune_consolidation_evidence(character_id, user_id, watermark)\n        return changed\n'''
if old_dream not in d:
    raise SystemExit("DreamEngine consolidate anchor not found")
d = d.replace(old_dream, new_dream, 1)
dream_path.write_text(d, encoding="utf-8")

# ---------------------------------------------------------------------------
# persistence_storage_probe.py: include the new compact evidence stream.
# ---------------------------------------------------------------------------
probe = probe_path.read_text(encoding="utf-8")
table_anchor = '''                "event_log": _table_metrics(conn, "event_log", ("character_id", "user_id", "event_type", "payload")),\n                "continuity_subject": _table_metrics(conn, "continuity_subject", ("character_id", "user_id", "subject_uuid")),\n'''
table_replacement = '''                "event_log": _table_metrics(conn, "event_log", ("character_id", "user_id", "event_type", "payload")),\n                "consolidation_evidence": _table_metrics(conn, "consolidation_evidence", ("character_id", "user_id", "evidence_types")),\n                "continuity_subject": _table_metrics(conn, "continuity_subject", ("character_id", "user_id", "subject_uuid")),\n'''
if table_anchor not in probe:
    raise SystemExit("probe table anchor not found")
probe = probe.replace(table_anchor, table_replacement, 1)
probe = probe.replace(
    '                    "checkpoint_rows_per_exercised_turn": round(tables["continuity_checkpoint"]["rows"] / turns, 3),\n',
    '                    "checkpoint_rows_per_exercised_turn": round(tables["continuity_checkpoint"]["rows"] / turns, 3),\n                    "consolidation_evidence_rows_per_exercised_turn": round(tables["consolidation_evidence"]["rows"] / turns, 3),\n                    "runtime_diagnostic_event_limit": agent.engine.persistence.diagnostic_event_limit,\n',
    1,
)
probe_path.write_text(probe, encoding="utf-8")

# ---------------------------------------------------------------------------
# New regression tests.
# ---------------------------------------------------------------------------
test_path.write_text('''import json\nimport os\nimport sqlite3\nimport tempfile\nimport uuid\n\nfrom persona_engine.agent import CharacterAgent\nfrom persona_engine.core.belief_ledger import BeliefLedger\nfrom persona_engine.core.dream_engine import DreamEngine\nfrom persona_engine.core.persistence import (\n    DEFAULT_RUNTIME_DIAGNOSTIC_EVENT_LIMIT,\n    Persistence,\n)\n\n\ndef _count(path, table):\n    conn = sqlite3.connect(path)\n    try:\n        return int(conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0])\n    finally:\n        conn.close()\n\n\ndef test_direct_persistence_keeps_legacy_unlimited_diagnostics_by_default():\n    with tempfile.TemporaryDirectory() as d:\n        path = os.path.join(d, "state.db")\n        p = Persistence(path)\n        for index in range(600):\n            p.log_event("K", "u", index, "diagnostic", {"memory_types": ["neutral"]})\n        assert _count(path, "event_log") == 600\n        assert _count(path, "consolidation_evidence") == 600\n\n\ndef test_bounded_diagnostics_do_not_bound_semantic_consolidation_evidence():\n    with tempfile.TemporaryDirectory() as d:\n        path = os.path.join(d, "state.db")\n        p = Persistence(path, diagnostic_event_limit=3)\n        p.bind_subject("K", "u", str(uuid.uuid4()))\n        for index in range(10):\n            p.log_event("K", "u", index, "turn", {"memory_types": ["repair"]})\n        assert _count(path, "event_log") == 3\n        assert _count(path, "consolidation_evidence") == 10\n        assert p.event_counts_since("K", "u", 0.0)["repair"] == 10\n\n\ndef test_canonical_continuity_survives_diagnostic_pruning():\n    with tempfile.TemporaryDirectory() as d:\n        path = os.path.join(d, "state.db")\n        p = Persistence(path, diagnostic_event_limit=3)\n        p.bind_subject("K", "u", str(uuid.uuid4()))\n        for index in range(10):\n            p.log_event("K", "u", index, "input", {"user_text": f"event {index}", "memory_types": ["user_input"]})\n        assert _count(path, "event_log") == 3\n        assert len(p.load_continuity_events("K", "u")) == 10\n\n\ndef test_legacy_canonical_rows_are_backfilled_before_bounded_runtime_prunes_them():\n    with tempfile.TemporaryDirectory() as d:\n        path = os.path.join(d, "state.db")\n        seed = Persistence(path)\n        subject = str(uuid.uuid4())\n        seed.bind_subject("K", "u", subject)\n        conn = sqlite3.connect(path)\n        try:\n            for index in range(10):\n                conn.execute(\n                    "INSERT INTO event_log(character_id,user_id,timestep,event_type,payload,created_at) VALUES(?,?,?,?,?,?)",\n                    ("K", "u", index, "input", json.dumps({"user_text": f"legacy {index}"}), float(index + 1)),\n                )\n            conn.commit()\n        finally:\n            conn.close()\n        runtime = Persistence(path, diagnostic_event_limit=3)\n        runtime.bind_subject("K", "u", subject)\n        assert len(runtime.load_continuity_events("K", "u")) == 10\n        assert _count(path, "event_log") == 3\n        assert _count(path, "consolidation_evidence") == 10\n\n\ndef test_dream_engine_uses_compact_evidence_and_prunes_committed_window():\n    beliefs = [{"id": "trust", "initial": 0.0, "min": -1.0, "max": 1.0, "decay_rate": 0.0, "description": "trust"}]\n    rules = [{"belief_id": "trust", "trigger_memory_type": "repair", "threshold_count": 2, "delta": 0.25}]\n    with tempfile.TemporaryDirectory() as d:\n        path = os.path.join(d, "state.db")\n        p = Persistence(path, diagnostic_event_limit=2)\n        led = BeliefLedger(beliefs)\n        dream = DreamEngine(p, led)\n        for index in range(8):\n            p.log_event("K", "u", index, "turn", {"memory_types": ["repair"]})\n        assert _count(path, "event_log") == 2\n        assert dream.consolidate("K", "u", rules) == ["trust"]\n        assert led.get("trust") == 0.25\n        assert _count(path, "consolidation_evidence") == 0\n        assert dream.consolidate("K", "u", rules) == []\n\n\ndef test_character_runtime_uses_explicit_bounded_telemetry_profile():\n    with tempfile.TemporaryDirectory() as d:\n        cart = os.path.join(os.path.dirname(__file__), "..", "cartridges", "pretorius.snp")\n        agent = CharacterAgent(cartridge_path=cart, user_id="u", db_path=os.path.join(d, "state.db"))\n        assert agent.engine.persistence.diagnostic_event_limit == DEFAULT_RUNTIME_DIAGNOSTIC_EVENT_LIMIT == 512\n''', encoding="utf-8")
