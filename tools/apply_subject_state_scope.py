#!/usr/bin/env python3
"""Apply the minimum explicit subject-owned snapshot scope.

Three independent probes showed the same ownership failure. This patch does not
make all state global. It adds a generic subject snapshot primitive and opts in
only the state families already demonstrated to belong to the continuing subject.
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PERSISTENCE = ROOT / "persona_engine" / "core" / "persistence.py"
ENGINE = ROOT / "persona_engine" / "core" / "engine.py"
TESTS = ROOT / "persona_engine" / "tests" / "test_subject_state_scope.py"


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected one exact anchor, found {count}")
    return text.replace(old, new, 1)


def patch_persistence() -> None:
    text = PERSISTENCE.read_text(encoding="utf-8")

    text = replace_once(
        text,
        '''CREATE TABLE IF NOT EXISTS state (\n    character_id TEXT NOT NULL,\n    user_id TEXT NOT NULL,\n    key TEXT NOT NULL,\n    value TEXT NOT NULL,\n    updated_at REAL NOT NULL,\n    PRIMARY KEY (character_id, user_id, key)\n);\nCREATE TABLE IF NOT EXISTS event_log (''',
        '''CREATE TABLE IF NOT EXISTS state (\n    character_id TEXT NOT NULL,\n    user_id TEXT NOT NULL,\n    key TEXT NOT NULL,\n    value TEXT NOT NULL,\n    updated_at REAL NOT NULL,\n    PRIMARY KEY (character_id, user_id, key)\n);\nCREATE TABLE IF NOT EXISTS subject_state (\n    subject_uuid TEXT NOT NULL,\n    key TEXT NOT NULL,\n    value TEXT NOT NULL,\n    updated_at REAL NOT NULL,\n    PRIMARY KEY (subject_uuid, key)\n);\nCREATE TABLE IF NOT EXISTS event_log (''',
        "subject_state schema",
    )

    anchor = '''    def save_deception_ledger(self, character_id: str, user_id: str, ledger: DeceptionLedger):\n'''
    methods = '''    def save_subject(self, character_id: str, user_id: str, key: str, value) -> None:\n        """Persist one explicitly subject-owned snapshot value.\n\n        This table is a current-state cache, not canonical event authority. The\n        engine decides which semantic families are allowed to use subject scope.\n        """\n\n        subject_uuid, _ = self._resolve_subject(character_id, user_id)\n        with self._connection() as conn:\n            conn.execute(\n                "INSERT INTO subject_state(subject_uuid,key,value,updated_at) VALUES(?,?,?,?) "\n                "ON CONFLICT(subject_uuid,key) DO UPDATE SET value=excluded.value, updated_at=excluded.updated_at",\n                (subject_uuid, key, json.dumps(value, ensure_ascii=False), time.time()),\n            )\n\n    def load_subject(self, character_id: str, user_id: str, key: str, default=None):\n        """Load one explicitly subject-owned snapshot value by permanent UUID."""\n\n        subject_uuid, _ = self._resolve_subject(character_id, user_id)\n        with self._connection() as conn:\n            row = conn.execute(\n                "SELECT value FROM subject_state WHERE subject_uuid=? AND key=?",\n                (subject_uuid, key),\n            ).fetchone()\n        return json.loads(row[0]) if row else default\n\n    def save_subject_many(self, character_id: str, user_id: str, items: dict) -> None:\n        """Persist a small explicit set of subject-owned snapshot values."""\n\n        subject_uuid, _ = self._resolve_subject(character_id, user_id)\n        now = time.time()\n        with self._connection() as conn:\n            for key, value in items.items():\n                conn.execute(\n                    "INSERT INTO subject_state(subject_uuid,key,value,updated_at) VALUES(?,?,?,?) "\n                    "ON CONFLICT(subject_uuid,key) DO UPDATE SET value=excluded.value, updated_at=excluded.updated_at",\n                    (subject_uuid, key, json.dumps(value, ensure_ascii=False), now),\n                )\n\n'''
    text = replace_once(text, anchor, methods + anchor, "subject state persistence methods")
    PERSISTENCE.write_text(text, encoding="utf-8")


def patch_engine() -> None:
    text = ENGINE.read_text(encoding="utf-8")

    text = replace_once(
        text,
        '''LEGACY_IDLE_STEP_SECONDS = 5.0\nLEGACY_CATCHUP_DYNAMICS_BUDGET_SECONDS = 1000.0\n''',
        '''LEGACY_IDLE_STEP_SECONDS = 5.0\nLEGACY_CATCHUP_DYNAMICS_BUDGET_SECONDS = 1000.0\n\n# Explicit snapshot ownership. Only experimentally demonstrated subject-owned\n# families belong here. Everything else keeps its existing interlocutor scope\n# until a separate longitudinal failure earns a different ownership rule.\nSUBJECT_OWNED_SNAPSHOT_KEYS = frozenset({"continuity_clock", "earned_traits"})\n''',
        "subject ownership whitelist",
    )

    text = replace_once(
        text,
        '''        clock_state = self.persistence.load(cid, uid, "continuity_clock")\n        if clock_state:\n            self.clock = ContinuityClock.from_dict(clock_state)\n        else:\n            # v1 compatibility: preserve the old wall anchor, but do not invent\n            # historical elapsed subject time that was never recorded.\n            self.clock.last_wall_time = float(meta.get("last_wall_time", self.clock.last_wall_time))\n''',
        '''        clock_state = self.persistence.load_subject(cid, uid, "continuity_clock", None)\n        if clock_state is None:\n            # Legacy fallback for databases created before explicit state scope.\n            clock_state = self.persistence.load(cid, uid, "continuity_clock")\n        if clock_state:\n            self.clock = ContinuityClock.from_dict(clock_state)\n        else:\n            # v1 compatibility: preserve the old wall anchor, but do not invent\n            # historical elapsed subject time that was never recorded.\n            self.clock.last_wall_time = float(meta.get("last_wall_time", self.clock.last_wall_time))\n''',
        "subject-owned clock load",
    )

    text = replace_once(
        text,
        '''        for t in self.persistence.load(cid, uid, "earned_traits", []):\n            self.ledger.earned_traits[t["name"]] = EarnedTrait(**t)\n''',
        '''        trait_state = self.persistence.load_subject(cid, uid, "earned_traits", None)\n        if trait_state is None:\n            # Legacy fallback for the active stream only. Cross-stream merging is\n            # intentionally not guessed because old snapshots may disagree.\n            trait_state = self.persistence.load(cid, uid, "earned_traits", [])\n        for t in trait_state:\n            self.ledger.earned_traits[t["name"]] = EarnedTrait(**t)\n''',
        "subject-owned earned-trait load",
    )

    text = replace_once(
        text,
        '''    def _persist(self):\n        state = self._serialize_state()\n        self.persistence.save_many(self.identity.name, self.user_id, state)\n        self.persistence.record_checkpoint(self.identity.name, self.user_id, state)\n''',
        '''    def _persist(self):\n        state = self._serialize_state()\n        # Preserve the full legacy/interlocutor snapshot for compatibility, then\n        # write only explicitly earned subject-owned families to UUID scope.\n        self.persistence.save_many(self.identity.name, self.user_id, state)\n        self.persistence.save_subject_many(\n            self.identity.name,\n            self.user_id,\n            {key: state[key] for key in SUBJECT_OWNED_SNAPSHOT_KEYS},\n        )\n        self.persistence.record_checkpoint(self.identity.name, self.user_id, state)\n''',
        "subject-owned snapshot persistence",
    )

    ENGINE.write_text(text, encoding="utf-8")


def write_tests() -> None:
    TESTS.write_text('''"""Explicit subject-owned versus interlocutor-owned snapshot contracts."""\n\nfrom pathlib import Path\nimport os\nimport tempfile\nimport uuid\n\nfrom persona_engine.agent import CharacterAgent\nfrom persona_engine.core.persistence import Persistence\n\nROOT = Path(__file__).resolve().parents[1]\nCART = ROOT / "cartridges" / "pretorius.snp"\n\n\ndef test_persistence_subject_scope_is_shared_by_uuid_not_user_id():\n    with tempfile.TemporaryDirectory() as d:\n        p = Persistence(os.path.join(d, "state.db"))\n        subject_uuid = str(uuid.uuid4())\n        p.bind_subject("Character", "alice", subject_uuid)\n        p.bind_subject("Character", "bob", subject_uuid)\n        p.save_subject("Character", "alice", "probe", {"value": 7})\n        assert p.load_subject("Character", "bob", "probe") == {"value": 7}\n        assert p.load("Character", "bob", "probe") is None\n\n\ndef test_only_demonstrated_snapshot_families_enter_subject_scope():\n    with tempfile.TemporaryDirectory() as d:\n        db = os.path.join(d, "state.db")\n        agent = CharacterAgent(cartridge_path=str(CART), user_id="alice", db_path=db)\n        agent.engine._persist()\n        conn = agent.engine.persistence.conn\n        try:\n            keys = {row[0] for row in conn.execute("SELECT key FROM subject_state").fetchall()}\n        finally:\n            conn.close()\n        assert keys == {"continuity_clock", "earned_traits"}\n\n\ndef test_earned_trait_is_subject_owned_while_relationship_remains_actor_specific():\n    with tempfile.TemporaryDirectory() as d:\n        db = os.path.join(d, "state.db")\n        alice = CharacterAgent(cartridge_path=str(CART), user_id="alice", db_path=db)\n        alice.engine.ledger.propose_trait_update("deliberate_caution", 0.05, ["evidence-1"])\n        alice.engine.relationship.trust = 0.81\n        alice.engine._persist()\n\n        bob = CharacterAgent(cartridge_path=str(CART), user_id="bob", db_path=db)\n        trait = bob.engine.ledger.earned_traits.get("deliberate_caution")\n        assert trait is not None\n        assert trait.strength == 0.05\n        assert trait.source_memory_ids == ["evidence-1"]\n        assert bob.engine.relationship.trust != 0.81\n        assert bob.engine.relationship.user_id == "bob"\n\n\ndef test_legacy_active_stream_trait_snapshot_still_loads_when_subject_snapshot_absent():\n    with tempfile.TemporaryDirectory() as d:\n        db = os.path.join(d, "state.db")\n        agent = CharacterAgent(cartridge_path=str(CART), user_id="legacy", db_path=db)\n        agent.engine.ledger.propose_trait_update("legacy_trait", 0.05, ["legacy-evidence"])\n        agent.engine._persist()\n\n        conn = agent.engine.persistence.conn\n        try:\n            conn.execute("DELETE FROM subject_state WHERE key='earned_traits'")\n            conn.commit()\n        finally:\n            conn.close()\n\n        restarted = CharacterAgent(cartridge_path=str(CART), user_id="legacy", db_path=db)\n        assert restarted.engine.ledger.earned_traits["legacy_trait"].strength == 0.05\n''', encoding="utf-8")


def main() -> None:
    patch_persistence()
    patch_engine()
    write_tests()
    print("Applied explicit subject-owned snapshot scope")


if __name__ == "__main__":
    main()
