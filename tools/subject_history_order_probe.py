#!/usr/bin/env python3
"""Probe whether one subject has one unambiguous canonical root-event order."""

from __future__ import annotations

import argparse
import json
import tempfile
from pathlib import Path

from persona_engine.agent import CharacterAgent

ROOT = Path(__file__).resolve().parents[1]
CART = ROOT / "persona_engine" / "cartridges" / "pretorius.snp"


def run() -> dict:
    with tempfile.TemporaryDirectory() as d:
        db = str(Path(d) / "shared.db")

        alice1 = CharacterAgent(cartridge_path=str(CART), user_id="alice", db_path=db)
        alice1.say("Alice first canonical turn.")

        bob = CharacterAgent(cartridge_path=str(CART), user_id="bob", db_path=db)
        bob.say("Bob canonical turn.")

        alice2 = CharacterAgent(cartridge_path=str(CART), user_id="alice", db_path=db)
        alice2.say("Alice second canonical turn.")

        events = alice2.engine.persistence.load_subject_continuity_events(
            alice2.engine.identity.name,
            alice2.engine.user_id,
            event_type="input",
        )
        roots = [
            {
                "user_id": event["user_id"],
                "sequence": int(event["sequence"]),
                "wall_time": float(event["wall_time"]),
                "event_uuid": event["event_uuid"],
                "user_text": (event.get("payload") or {}).get("user_text"),
            }
            for event in events
        ]
        sequences = [item["sequence"] for item in roots]
        unique = len(sequences) == len(set(sequences))
        strictly_increasing = all(b > a for a, b in zip(sequences, sequences[1:]))
        contiguous = sequences == list(range(sequences[0], sequences[0] + len(sequences))) if sequences else True
        same_subject = len({event["subject_uuid"] for event in events}) <= 1

        if not same_subject:
            diagnosis = "subject_identity_split"
        elif unique and strictly_increasing and contiguous:
            diagnosis = "subject_canonical_order_is_unambiguous"
        else:
            diagnosis = "canonical_sequence_partitioned_by_interlocutor"

        return {
            "probe": "subject-history-ordering-v1",
            "roots": roots,
            "sequence_values": sequences,
            "same_subject_uuid": same_subject,
            "sequence_unique_subject_wide": unique,
            "sequence_strictly_increasing_subject_wide": strictly_increasing,
            "sequence_contiguous_subject_wide": contiguous,
            "diagnosis": diagnosis,
            "interpretation": (
                "Wall time and SQLite insertion order may provide a practical sort, but the canonical sequence field "
                "should itself be an unambiguous order for one continuing subject if Wayfarer claims one canonical lived history."
            ),
        }


def markdown(result: dict) -> str:
    rows = "\n".join(
        f"| {index + 1} | `{item['user_id']}` | `{item['sequence']}` | `{item['user_text']}` |"
        for index, item in enumerate(result["roots"])
    )
    return f"""# Subject-Wide Canonical Ordering Probe

Probe: `{result['probe']}`

| Subject order by recorded wall time | Interlocutor | Stored sequence | Canonical input |
| ---: | --- | ---: | --- |
{rows}

Subject UUID remains shared: `{result['same_subject_uuid']}`  
Sequence values are unique subject-wide: `{result['sequence_unique_subject_wide']}`  
Sequence values are strictly increasing subject-wide: `{result['sequence_strictly_increasing_subject_wide']}`  
Sequence values are contiguous subject-wide: `{result['sequence_contiguous_subject_wide']}`  
Diagnosis: `{result['diagnosis']}`

This probe distinguishes an ordering property from the interlocutor-ownership property. Relationship views may remain actor-specific, but a single individual's canonical biography should not require `(user_id, sequence)` to determine which of two events was "sequence 1." Wall time is retained as evidence, but it is not a substitute for an explicit canonical order when the architecture claims a monotonic event sequence.

No sequence schema is changed by this probe.
"""


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json")
    parser.add_argument("--markdown")
    args = parser.parse_args()
    result = run()
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
