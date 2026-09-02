#!/usr/bin/env python3
"""Verify that Wayfarer's one live test-count claim matches pytest.

CURRENT_STATUS.md owns the live numeric deterministic-suite status.
Other documents may keep explicitly historical counts but should point
readers at CURRENT_STATUS.md instead of maintaining a second live total.

In CI, pass --pytest-output so the checker consumes the suite run that
already happened. When run locally without that option, it runs pytest
once itself.
"""

from __future__ import annotations

import argparse
import re
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
CURRENT_STATUS = REPO_ROOT / "persona_engine" / "docs" / "CURRENT_STATUS.md"
AGENTS = REPO_ROOT / "AGENTS.md"
SUITE_RE = re.compile(r"(\d+)\s+passed,\s+(\d+)\s+skipped,\s+(\d+)\s+warnings?")


def _suite_summary(text: str) -> tuple[int, int, int]:
    matches = list(SUITE_RE.finditer(text))
    if not matches:
        raise ValueError("could not parse deterministic-suite summary")
    passed, skipped, warnings = matches[-1].groups()
    return int(passed), int(skipped), int(warnings)


def _current_checkpoint(text: str) -> str:
    heading = "## Current production checkpoint"
    start = text.find(heading)
    if start < 0:
        raise ValueError("CURRENT_STATUS.md is missing the current production checkpoint")
    next_heading = text.find("\n## ", start + len(heading))
    return text[start:] if next_heading < 0 else text[start:next_heading]


def _live_summary(pytest_output: Path | None) -> tuple[int, int, int]:
    if pytest_output is not None:
        return _suite_summary(pytest_output.read_text(encoding="utf-8", errors="replace"))
    result = subprocess.run(
        ["python", "-m", "pytest", "persona_engine/tests", "-q"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    combined = result.stdout + "\n" + result.stderr
    if result.returncode != 0:
        print(combined[-4000:])
        raise RuntimeError(f"pytest failed with exit code {result.returncode}")
    return _suite_summary(combined)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pytest-output", type=Path)
    args = parser.parse_args()

    status_text = CURRENT_STATUS.read_text(encoding="utf-8")
    agents_text = AGENTS.read_text(encoding="utf-8")
    checkpoint = _current_checkpoint(status_text)
    problems: list[str] = []

    claims = list(SUITE_RE.finditer(checkpoint))
    if len(claims) != 1:
        problems.append(
            "CURRENT_STATUS.md current production checkpoint must contain exactly one live deterministic-suite count."
        )
        documented = None
    else:
        documented = _suite_summary(checkpoint)

    required_pointer = "CURRENT_STATUS.md` is the only live numeric status source"
    if required_pointer not in agents_text:
        problems.append("AGENTS.md is missing the single-source current-status pointer.")
    if "Current production inventory" in agents_text:
        problems.append("AGENTS.md still contains a second live current-inventory claim.")

    try:
        live = _live_summary(args.pytest_output)
    except Exception as exc:
        problems.append(str(exc))
        live = None

    if documented is not None and live is not None and documented != live:
        problems.append(f"CURRENT_STATUS.md claims {documented}, but pytest reports {live}.")

    if problems:
        print("CURRENT STATUS SYNC CHECK FAILED:")
        for problem in problems:
            print(f"  - {problem}")
        return 1

    print(
        f"Current status matches pytest: {live[0]} passed, {live[1]} skipped, {live[2]} warning(s)."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
