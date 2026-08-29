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

        persistence = alice2.engine.persistence
        events = persistence.load_subject_continuity_events(
            alice2.engine.identity.name,
            alice2.engine.user_id,
            event_type="input",
        )
        all_events = persistence.load_subject_continuity_events(
            alice2.engine.identity.name,
            alice2.engine.user_id,
        )
        roots = [
            {
                "user_id": event["user_id"],
                "sequence": int(event["sequence"]),
                "subject_sequence": int(event["subject_sequence"]),
                "wall_time": float(event["wall_time"]),
                "event_uuid": event["event_uuid"],
                "user_text": (event.get("payload") or {}).get("user_text"),
            }
            for event in events
        ]
        stream_sequences = [item["sequence"] for item in roots]
        subject_sequences = [item["subject_sequence"] for item in roots]
        all_subject_sequences = [int(event["subject_sequence"]) for event in all_events]
        unique = len(subject_sequences) == len(set(subject_sequences))
        strictly_increasing = all(b > a for a, b in zip(subject_sequences, subject_sequences[1:]))
        all_contiguous = all_subject_sequences == list(range(1, len(all_subject_sequences) + 1))
        same_subject = len({event["subject_uuid"] for event in all_events}) <= 1

        if not same_subject:
            diagnosis = "subject_identity_split"
        elif unique and strictly_increasing and all_contiguous:
            diagnosis = "subject_canonical_order_is_unambiguous"
        else:
            diagnosis = "subject_canonical_order_still_ambiguous"

        return {
            "probe": "subject-history-ordering-v2",
            "roots": roots,
            "stream_sequence_values": stream_sequences,
            "subject_sequence_values": subject_sequences,
            "all_subject_sequence_values": all_subject_sequences,
            "same_subject_uuid": same_subject,
            "subject_sequence_unique_across_interlocutors": unique,
            "subject_sequence_strictly_increasing_across_interlocutors": strictly_increasing,
            "subject_sequence_contiguous_across_all_canonical_events": all_contiguous,
            "diagnosis": diagnosis,
            "interpretation": (
                "Per-interlocutor sequence remains available for v1 replay compatibility, while subject_sequence provides the single explicit canonical order for the continuing individual."
            ),
        }


def markdown(result: dict) -> str:
    rows = "\n".join(
        f"| {index + 1} | `{item['user_id']}` | `{item['sequence']}` | `{item['subject_sequence']}` | `{item['user_text']}` |"
        for index, item in enumerate(result["roots"])
    )
    return f"""# Subject-Wide Canonical Ordering Probe

Probe: `{result['probe']}`

| Subject encounter order | Interlocutor | Existing stream sequence | Subject sequence | Canonical input |
| ---: | --- | ---: | ---: | --- |
{rows}

Subject UUID remains shared: `{result['same_subject_uuid']}`  
Subject ordinals are unique across interlocutors: `{result['subject_sequence_unique_across_interlocutors']}`  
Subject ordinals are strictly increasing across interlocutors: `{result['subject_sequence_strictly_increasing_across_interlocutors']}`  
Subject ordinals are contiguous across all canonical events: `{result['subject_sequence_contiguous_across_all_canonical_events']}`  
Diagnosis: `{result['diagnosis']}`

The existing `sequence` field remains the v1 per-interlocutor replay/export stream and is intentionally allowed to repeat across different interlocutors. The additive `subject_sequence` field is the minimum subject-owned ordering primitive. It gives one continuing individual one explicit canonical biography without turning relationship state into global state or replacing the established replay contract.
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
