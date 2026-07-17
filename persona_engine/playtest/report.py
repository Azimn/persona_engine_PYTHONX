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
    illusion_review = {
        "instructions": "Review the blind transcript before opening causal_trace.json.",
        "rating_scale": {"minimum": 1, "maximum": 5},
        "questions": [
            {"id": key, "prompt": prompt, "rating": None, "evidence_turns": [], "notes": ""}
            for key, prompt in (
                ("occupied", "Did the character seem occupied before or during contact?"),
                ("interests", "Did the character seem to have interests independent of the player?"),
                ("natural_memory", "Did remembered material enter the interaction naturally?"),
                ("caused_surprise", "Were surprising behaviors understandable in retrospect?"),
                ("repetition", "How free was the interaction from conspicuous repetition?"),
                ("prior_life", "Did the character seem to exist before the player arrived?"),
                ("non_assistant", "Did the character feel distinct from a generic helpful assistant?"),
                ("return_interest", "Would you voluntarily continue this interaction?"),
            )
        ],
    }
    (root / "illusion_review.json").write_text(
        json.dumps(illusion_review, indent=2, sort_keys=True), encoding="utf-8",
    )
