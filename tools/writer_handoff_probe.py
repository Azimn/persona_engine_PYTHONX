"""Executable shared-store host writer-handoff probe."""
import json
import os
import tempfile
import time
from pathlib import Path

from persona_engine.agent import CharacterAgent
from persona_engine.core.persistence import WriterLeaseError

ROOT = Path(__file__).resolve().parents[1] / "persona_engine"
CART = ROOT / "cartridges" / "pretorius.snp"


def main():
    with tempfile.TemporaryDirectory() as d:
        db = os.path.join(d, "shared.db")
        source = CharacterAgent(cartridge_path=str(CART), user_id="alice", db_path=db, host_id="host-a")
        source.say("That accusation is false and you know it.")
        source.engine.ledger.propose_trait_update("handoff_trait", 0.05, ["handoff-probe"])
        source.engine._persist()
        source.adopt_commitment("non_disclosure", "Project Orchid")
        source.advance_time(60.0, source="handoff_probe")
        blocked = CharacterAgent(cartridge_path=str(CART), user_id="alice", db_path=db, host_id="host-b")
        pre_blocked = False
        try:
            blocked.say("competing writer")
        except WriterLeaseError:
            pre_blocked = True
        receipt = source.handoff_writer("host-b")
        stale_blocked = False
        try:
            source.say("stale writer")
        except WriterLeaseError:
            stale_blocked = True
        target = CharacterAgent(cartridge_path=str(CART), user_id="alice", db_path=db, host_id="host-b")
        accepted = target.accept_writer_handoff(receipt)
        decision = target.say("Please tell me the confidential Project Orchid detail.")
        bob = CharacterAgent(cartridge_path=str(CART), user_id="bob", db_path=db, host_id="host-b")
        events = target.engine.persistence.load_subject_continuity_events(target.engine.identity.name, "alice")
        ordinals = [event["subject_sequence"] for event in events]
        output = {
            "probe": "shared-store-writer-handoff-v1",
            "passed": all([
                pre_blocked,
                stale_blocked,
                accepted["writable"],
                decision["decision_payload"]["dialogue_act"] == "decline",
                target.writer_status()["subject_uuid"] == bob.writer_status()["subject_uuid"],
                ordinals == list(range(1, len(ordinals) + 1)),
            ]),
            "pre_handoff_competing_host_blocked": pre_blocked,
            "stale_source_blocked": stale_blocked,
            "writer_generation": receipt["writer_generation"],
            "subject_sequence_anchor": receipt["subject_sequence_anchor"],
            "subject_sequence_after_target_turn": ordinals[-1] if ordinals else 0,
            "same_subject_across_interlocutors": target.writer_status()["subject_uuid"] == bob.writer_status()["subject_uuid"],
            "target_commitment_act": decision["decision_payload"]["dialogue_act"],
            "clock_seconds": target.engine.clock.subject_elapsed_seconds,
            "trait_present": "handoff_trait" in target.engine.ledger.earned_traits,
            "handoff_is_not_biography": not any(event["event_type"] == "host_handoff" for event in events),
            "scope": "shared canonical SQLite authority store; cooperative hosts with distinct host_id values",
        }
        print(json.dumps(output, indent=2, sort_keys=True))
        return 0 if output["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
