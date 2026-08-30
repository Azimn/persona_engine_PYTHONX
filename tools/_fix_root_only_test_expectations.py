#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def replace_once(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    if old not in text:
        raise SystemExit(f"expected test block not found in {path}: {old!r}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")

ledger = ROOT / "persona_engine/tests/test_continuity_ledger.py"
replace_once(
    ledger,
    '        source.log_event("Character", "user", 2, "state_transition", {"pressure_after": {"fear": 0.2}})\n',
    '        source.log_event("Character", "user", 2, "input", {"text": "second root"})\n',
)
replace_once(
    ledger,
    '        p.log_event("Character", "user", 2, "state_transition", {"x": 2})\n',
    '        p.log_event("Character", "user", 2, "input", {"text": "two"})\n',
)

replay = ROOT / "persona_engine/tests/test_continuity_replay.py"
replace_once(
    replay,
    '        assert result.derived_events_skipped >= 2\n',
    '        # New production histories store causal roots only. Legacy derived\n        # rows are covered separately by test_root_only_continuity.py.\n        assert result.derived_events_skipped == 0\n',
)

subject_sequence = ROOT / "persona_engine/tests/test_subject_sequence.py"
replace_once(
    subject_sequence,
    '        p.log_event("Character", "alice", 3, "state_transition", {"x": 1})\n',
    '        p.log_event("Character", "alice", 3, "input", {"text": "alice two"})\n',
)

print("root-only test expectations aligned with causal-root writer")
