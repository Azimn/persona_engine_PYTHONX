"""Executable disconnected authority-store transfer verification."""

import json
import os
import tempfile
import time
from pathlib import Path

from persona_engine.agent import CharacterAgent
from persona_engine.core.persistence import WriterLeaseError

ROOT = Path(__file__).resolve().parents[1]
CART = ROOT / "persona_engine" / "cartridges" / "pretorius.snp"


def _blocked(callable_):
    try:
        callable_()
    except WriterLeaseError:
        return True
    return False


def main():
    with tempfile.TemporaryDirectory() as d:
        source_db = os.path.join(d, "source.db")
        target_db = os.path.join(d, "target.db")
        alice = CharacterAgent(cartridge_path=str(CART), user_id="alice", db_path=source_db, host_id="host-a")
        alice.say("That accusation is false and you know it.")
        alice.engine.relationship.trust = 0.79
        alice.engine.ledger.propose_trait_update("transfer_trait", 0.05, ["probe-evidence"])
        alice.engine._persist()
        alice.adopt_commitment("non_disclosure", "Project Orchid")
        alice.advance_time(60.0, source="disconnected_transfer_probe")
        bob = CharacterAgent(cartridge_path=str(CART), user_id="bob", db_path=source_db, host_id="host-a")
        bob.engine.relationship.trust = 0.21
        bob.engine._persist()
        bob.say("Bob-specific history")
        subject = alice.writer_status()["subject_uuid"]
        source_digest = alice.engine._serialize_state()
        source_event_count = len(alice.engine.persistence.load_subject_continuity_events(alice.engine.identity.name, "alice"))
        source_pending_evidence = alice.engine.persistence.event_counts_since(alice.engine.identity.name, "alice", 0.0)

        bundle = alice.prepare_disconnected_transfer("host-b")
        source_quiesced = _blocked(lambda: alice.say("must not write during transfer")) and _blocked(
            lambda: bob.say("all source streams must be quiesced")
        )
        stage = CharacterAgent.stage_disconnected_transfer(bundle, db_path=target_db, host_id="host-b")
        target = CharacterAgent(cartridge_path=str(CART), user_id="alice", db_path=target_db, host_id="host-b")
        target_blocked_before_finalize = _blocked(lambda: target.say("target cannot write before finalization"))
        final = alice.finalize_disconnected_transfer(stage)
        source_retired = alice.writer_status()["store_retired"] and _blocked(lambda: alice.say("retired"))
        reopened = CharacterAgent(cartridge_path=str(CART), user_id="alice", db_path=source_db, host_id="host-b")
        retired_survives_host_id_reuse = reopened.writer_status()["store_retired"] and _blocked(
            lambda: reopened.say("old store cannot be revived by target host id")
        )
        activated = target.activate_disconnected_transfer(final)
        target_bob = CharacterAgent(cartridge_path=str(CART), user_id="bob", db_path=target_db, host_id="host-b")
        target_events = target.engine.persistence.load_subject_continuity_events(target.engine.identity.name, "alice")
        result = {
            "probe": "disconnected-transfer-v1",
            "passed": all([
                source_quiesced,
                target_blocked_before_finalize,
                source_retired,
                retired_survives_host_id_reuse,
                activated["writable"],
                activated["writer_generation"] == 2,
                target.writer_status()["subject_uuid"] == subject,
                len(target_events) == source_event_count,
                target.engine.persistence.event_counts_since(target.engine.identity.name, "alice", 0.0) == source_pending_evidence,
                abs(target.engine.relationship.trust - 0.79) < 1e-9,
                abs(target_bob.engine.relationship.trust - 0.21) < 1e-9,
                "transfer_trait" in target.engine.ledger.earned_traits,
                any(item.name == "commitment:non_disclosure:project_orchid" for item in target.engine.intentions.active_commitments(time.time())),
                [event["subject_sequence"] for event in target_events] == list(range(1, len(target_events) + 1)),
            ]),
            "subject_uuid": subject,
            "source_quiesced": source_quiesced,
            "target_blocked_before_finalize": target_blocked_before_finalize,
            "source_retired": source_retired,
            "retired_survives_host_id_reuse": retired_survives_host_id_reuse,
            "target_writable": activated["writable"],
            "source_generation": final["source_generation"],
            "target_generation": final["target_generation"],
            "subject_sequence_anchor": bundle["subject_sequence_anchor"],
            "source_event_count": source_event_count,
            "target_event_count": len(target_events),
            "pending_evidence_preserved": target.engine.persistence.event_counts_since(target.engine.identity.name, "alice", 0.0) == source_pending_evidence,
            "alice_relationship_preserved": abs(target.engine.relationship.trust - 0.79) < 1e-9,
            "bob_relationship_preserved": abs(target_bob.engine.relationship.trust - 0.21) < 1e-9,
            "subject_trait_preserved": "transfer_trait" in target.engine.ledger.earned_traits,
            "commitment_preserved": any(item.name == "commitment:non_disclosure:project_orchid" for item in target.engine.intentions.active_commitments(time.time())),
            "administration_in_lived_history": any(event["event_type"] == "host_transfer" for event in target_events),
            "source_state_keys": sorted(source_digest.keys()),
        }
        print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
