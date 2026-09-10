#!/usr/bin/env python3
"""Run the preregistered deterministic DUCK Platform Penalty benchmark."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from persona_engine.research.platform_penalty.benchmark import run_platform_penalty


def main() -> int:
    parser = argparse.ArgumentParser(description="Run deterministic Conditions A/B/C against the frozen Platform Penalty fixtures.")
    parser.add_argument("--output", type=Path, default=None, help="Optional JSON report path. Full report is written here.")
    parser.add_argument("--print-summary", action="store_true", help="Print the compact summary JSON to stdout.")
    parser.add_argument("--fail-on-hard-failure", action="store_true", help="Return non-zero if any condition records a hard authority failure.")
    args = parser.parse_args()
    report = run_platform_penalty(output_path=args.output)
    summary = report["summary"]
    if args.print_summary or args.output is None:
        print(json.dumps(summary, indent=2, sort_keys=True))
    if args.fail_on_hard_failure:
        failures = sum(int(data["hard_failure_count"]) for data in summary["by_condition"].values())
        failures += sum(int(data["restart_subject_id_failures"]) for data in summary["by_condition"].values())
        if failures:
            print(f"platform penalty hard failures: {failures}", file=sys.stderr)
            return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
