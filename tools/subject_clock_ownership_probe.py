#!/usr/bin/env python3
"""Probe whether one continuing subject has one clock across interlocutors."""

from __future__ import annotations

import argparse
import json
import tempfile
from pathlib import Path

from persona_engine.agent import CharacterAgent

ROOT = Path(__file__).resolve().parents[1]
CART = ROOT / "persona_engine" / "cartridges" / "pretorius.snp"
EIGHT_HOURS = 8 * 60 * 60


def _subject_uuid(agent: CharacterAgent) -> str:
    return agent.engine.persistence._resolve_subject(agent.engine.identity.name, agent.engine.user_id)[0]


def run() -> dict:
    with tempfile.TemporaryDirectory() as d:
        db = str(Path(d) / "shared.db")

        alice = CharacterAgent(cartridge_path=str(CART), user_id="alice", db_path=db)
        alice_before = float(alice.engine.clock.subject_elapsed_seconds)
        alice.advance_time(EIGHT_HOURS, source="subject_clock_ownership_probe")
        alice_after = float(alice.engine.clock.subject_elapsed_seconds)
        alice_subject = _subject_uuid(alice)

        bob = CharacterAgent(cartridge_path=str(CART), user_id="bob", db_path=db)
        bob_subject = _subject_uuid(bob)
        bob_elapsed = float(bob.engine.clock.subject_elapsed_seconds)

        alice_restart = CharacterAgent(cartridge_path=str(CART), user_id="alice", db_path=db)
        alice_restart_elapsed = float(alice_restart.engine.clock.subject_elapsed_seconds)

        canonical_time_events = bob.engine.persistence.load_subject_continuity_events(
            bob.engine.identity.name,
            bob.engine.user_id,
            event_type="time_advance",
        )
        latest_canonical_elapsed = None
        if canonical_time_events:
            latest_canonical_elapsed = float((canonical_time_events[-1].get("payload") or {}).get("subject_elapsed_seconds", 0.0))

        same_subject = alice_subject == bob_subject
        alice_restart_preserved = abs(alice_restart_elapsed - alice_after) < 1e-6
        bob_matches_canonical = latest_canonical_elapsed is not None and abs(bob_elapsed - latest_canonical_elapsed) < 1e-6

        if not same_subject:
            diagnosis = "subject_identity_split"
        elif not alice_restart_preserved:
            diagnosis = "clock_not_persistent_even_with_same_interlocutor"
        elif bob_matches_canonical:
            diagnosis = "subject_clock_is_shared_across_interlocutors"
        else:
            diagnosis = "subject_clock_partitioned_by_interlocutor"

        return {
            "probe": "subject-clock-ownership-v1",
            "same_subject_uuid": same_subject,
            "alice_elapsed_before_seconds": alice_before,
            "alice_elapsed_after_seconds": alice_after,
            "alice_restart_elapsed_seconds": alice_restart_elapsed,
            "bob_elapsed_seconds": bob_elapsed,
            "latest_canonical_subject_elapsed_seconds": latest_canonical_elapsed,
            "alice_restart_preserved": alice_restart_preserved,
            "bob_matches_canonical_subject_time": bob_matches_canonical,
            "canonical_time_event_count": len(canonical_time_events),
            "diagnosis": diagnosis,
            "expected_minimum_property": (
                "Changing interlocutors must not fork the continuing individual's elapsed subject time."
            ),
        }


def markdown(result: dict) -> str:
    return f"""# Subject Clock Ownership Probe

Probe: `{result['probe']}`

| Observation | Result |
| --- | ---: |
| Alice/Bob same subject UUID | `{result['same_subject_uuid']}` |
| Alice elapsed after explicit 8h | `{result['alice_elapsed_after_seconds']}` seconds |
| Alice elapsed after restart | `{result['alice_restart_elapsed_seconds']}` seconds |
| Bob elapsed on same database | `{result['bob_elapsed_seconds']}` seconds |
| Latest canonical subject elapsed | `{result['latest_canonical_subject_elapsed_seconds']}` seconds |
| Same-interlocutor restart preserved | `{result['alice_restart_preserved']}` |
| Bob matches canonical subject time | `{result['bob_matches_canonical_subject_time']}` |
| Diagnosis | `{result['diagnosis']}` |

The minimum property under test is ownership, not psychology. `ContinuityClock` should remain one monotonic clock for one `subject_uuid`; changing the active relationship context must not create a second timeline. This probe does not infer sleep, loneliness, relationship cooling, or any other off-screen behavior from elapsed time.

No clock persistence rule is changed by this probe.
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
