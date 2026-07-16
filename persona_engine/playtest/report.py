"""Bounded playtest report artifacts."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any


def write_reports(output_dir: str | Path, result) -> None:
    root = Path(output_dir)
    root.mkdir(parents=True, exist_ok=True)
    (root / "playtest_report.json").write_text(json.dumps(result.to_dict(), indent=2, sort_keys=True), encoding="utf-8")
    (root / "blind_transcript.txt").write_text("\n".join(
        f"Day {item.day} {item.speaker_id}: {item.text or '[' + (item.observable_action or 'silence') + ']'}"
        for item in result.transcript
    ), encoding="utf-8")
    (root / "causal_trace.json").write_text(json.dumps(list(result.diagnostics), indent=2, sort_keys=True), encoding="utf-8")
    (root / "development_timeline.json").write_text(json.dumps(list(result.timeline), indent=2, sort_keys=True), encoding="utf-8")
    (root / "failure_findings.json").write_text(json.dumps([item.to_dict() for item in result.failures], indent=2), encoding="utf-8")
    (root / "judge_results.json").write_text(json.dumps(result.judge_results, indent=2, sort_keys=True), encoding="utf-8")
    with (root / "state_growth.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=("day", "participant_id", "serialized_state_bytes"))
        writer.writeheader()
        writer.writerows(result.state_growth)
    (root / "actor_moves.json").write_text(json.dumps([item.to_dict() for item in result.actor_moves], indent=2), encoding="utf-8")
