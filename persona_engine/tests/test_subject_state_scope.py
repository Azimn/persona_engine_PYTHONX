"""Explicit subject-owned versus interlocutor-owned snapshot contracts."""

from pathlib import Path
import os
import tempfile
import uuid

from persona_engine.agent import CharacterAgent
from persona_engine.core.persistence import Persistence

ROOT = Path(__file__).resolve().parents[1]
CART = ROOT / "cartridges" / "pretorius.snp"


def test_persistence_subject_scope_is_shared_by_uuid_not_user_id():
    with tempfile.TemporaryDirectory() as d:
        p = Persistence(os.path.join(d, "state.db"))
        subject_uuid = str(uuid.uuid4())
        p.bind_subject("Character", "alice", subject_uuid)
        p.bind_subject("Character", "bob", subject_uuid)
        p.save_subject("Character", "alice", "probe", {"value": 7})
        assert p.load_subject("Character", "bob", "probe") == {"value": 7}
        assert p.load("Character", "bob", "probe") is None


def test_only_demonstrated_snapshot_families_enter_subject_scope():
    with tempfile.TemporaryDirectory() as d:
        db = os.path.join(d, "state.db")
        agent = CharacterAgent(cartridge_path=str(CART), user_id="alice", db_path=db)
        agent.engine._persist()
        conn = agent.engine.persistence.conn
        try:
            keys = {row[0] for row in conn.execute("SELECT key FROM subject_state").fetchall()}
        finally:
            conn.close()
        assert keys == {"continuity_clock", "earned_traits"}


def test_earned_trait_is_subject_owned_while_relationship_remains_actor_specific():
    with tempfile.TemporaryDirectory() as d:
        db = os.path.join(d, "state.db")
        alice = CharacterAgent(cartridge_path=str(CART), user_id="alice", db_path=db)
        alice.engine.ledger.propose_trait_update("deliberate_caution", 0.05, ["evidence-1"])
        alice.engine.relationship.trust = 0.81
        alice.engine._persist()

        bob = CharacterAgent(cartridge_path=str(CART), user_id="bob", db_path=db)
        trait = bob.engine.ledger.earned_traits.get("deliberate_caution")
        assert trait is not None
        assert trait.strength == 0.05
        assert trait.source_memory_ids == ["evidence-1"]
        assert bob.engine.relationship.trust != 0.81
        assert bob.engine.relationship.user_id == "bob"


def test_legacy_active_stream_trait_snapshot_still_loads_when_subject_snapshot_absent():
    with tempfile.TemporaryDirectory() as d:
        db = os.path.join(d, "state.db")
        agent = CharacterAgent(cartridge_path=str(CART), user_id="legacy", db_path=db)
        agent.engine.ledger.propose_trait_update("legacy_trait", 0.05, ["legacy-evidence"])
        agent.engine._persist()

        conn = agent.engine.persistence.conn
        try:
            conn.execute("DELETE FROM subject_state WHERE key='earned_traits'")
            conn.commit()
        finally:
            conn.close()

        restarted = CharacterAgent(cartridge_path=str(CART), user_id="legacy", db_path=db)
        assert restarted.engine.ledger.earned_traits["legacy_trait"].strength == 0.05
