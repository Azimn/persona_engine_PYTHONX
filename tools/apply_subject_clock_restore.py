#!/usr/bin/env python3
"""Apply the minimum cross-interlocutor ContinuityClock ownership repair."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENGINE = ROOT / "persona_engine" / "core" / "engine.py"
TESTS = ROOT / "persona_engine" / "tests" / "test_continuity_clock.py"


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected one exact anchor, found {count}")
    return text.replace(old, new, 1)


def patch_engine() -> None:
    text = ENGINE.read_text(encoding="utf-8")
    text = replace_once(
        text,
        "        self._load_state()\n        self._restore_subject_owned_commitments()",
        "        self._load_state()\n        self._restore_subject_owned_clock()\n        self._restore_subject_owned_commitments()",
        "startup subject clock restoration",
    )

    anchor = "    def _restore_subject_owned_commitments(self) -> None:\n"
    method = '''    def _restore_subject_owned_clock(self) -> None:\n        """Reconcile interlocutor-scoped clock snapshots with subject history.\n\n        ``ContinuityClock`` is character-owned state. Existing snapshots remain\n        keyed by interlocutor for compatibility, but a newly opened relationship\n        must not fork the subject onto an earlier timeline. Canonical time roots\n        already carry the subject's accumulated elapsed time, so only an upward\n        reconciliation is required here. No psychological meaning is inferred.\n        """\n\n        events = self.persistence.load_subject_continuity_events(\n            self.identity.name,\n            self.user_id,\n            event_type="time_advance",\n        )\n        if not events:\n            return\n        payload = events[-1].get("payload") or {}\n        try:\n            canonical_elapsed = max(0.0, float(payload.get("subject_elapsed_seconds", 0.0)))\n        except (TypeError, ValueError):\n            return\n        if canonical_elapsed <= self.clock.subject_elapsed_seconds:\n            return\n        self.clock.subject_elapsed_seconds = canonical_elapsed\n        observed_wall = payload.get("observed_wall_time")\n        if isinstance(observed_wall, (int, float)):\n            self.clock.last_wall_time = float(observed_wall)\n\n'''
    text = replace_once(text, anchor, method + anchor, "subject clock method insertion")
    ENGINE.write_text(text, encoding="utf-8")


def patch_tests() -> None:
    text = TESTS.read_text(encoding="utf-8")
    marker = "def test_subject_clock_follows_one_subject_across_interlocutors():"
    if marker in text:
        return
    text += '''\n\ndef test_subject_clock_follows_one_subject_across_interlocutors():\n    with tempfile.TemporaryDirectory() as d:\n        db = os.path.join(d, "shared.db")\n        alice = CharacterAgent(cartridge_path=str(CART), user_id="alice", db_path=db)\n        alice.advance_time(8 * 60 * 60, source="subject_clock_test")\n        alice_elapsed = alice.engine.clock.subject_elapsed_seconds\n        alice_subject = alice.engine.persistence._resolve_subject(alice.engine.identity.name, "alice")[0]\n\n        bob = CharacterAgent(cartridge_path=str(CART), user_id="bob", db_path=db)\n        bob_subject = bob.engine.persistence._resolve_subject(bob.engine.identity.name, "bob")[0]\n        assert bob_subject == alice_subject\n        assert bob.engine.clock.subject_elapsed_seconds == alice_elapsed\n\n        bob.advance_time(60 * 60, source="subject_clock_test")\n        bob_elapsed = bob.engine.clock.subject_elapsed_seconds\n        assert bob_elapsed == alice_elapsed + 60 * 60\n\n        alice_again = CharacterAgent(cartridge_path=str(CART), user_id="alice", db_path=db)\n        assert alice_again.engine.clock.subject_elapsed_seconds == bob_elapsed\n\n        events = alice_again.engine.persistence.load_subject_continuity_events(\n            alice_again.engine.identity.name,\n            alice_again.engine.user_id,\n            event_type="time_advance",\n        )\n        assert [event["payload"]["subject_elapsed_seconds"] for event in events] == [\n            alice_elapsed,\n            bob_elapsed,\n        ]\n'''
    TESTS.write_text(text, encoding="utf-8")


def main() -> None:
    patch_engine()
    patch_tests()
    print("Applied minimal subject-owned clock restoration")


if __name__ == "__main__":
    main()
