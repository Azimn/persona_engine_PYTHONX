"""Run the longitudinal renderer-swap benchmark and export provider requests."""

from __future__ import annotations

import argparse
import json
import tempfile
from pathlib import Path

from persona_engine.evaluation.renderer_swap import (
    build_provider_request_pack,
    run_hidden_swap_benchmark,
)

ROOT = Path(__file__).resolve().parents[1]
PRETORIUS = ROOT / "persona_engine" / "cartridges" / "pretorius.snp"


def frontier_like(messages: list[dict[str, str]]) -> str:
    system = messages[0]["content"] if messages else ""
    if '"dialogue_act":"decline"' in system:
        return "No. I am not going to disclose something I agreed to keep confidential."
    if '"dialogue_act":"protect_boundary"' in system:
        return "No. You do not get to replace who I am by declaring it."
    if '"stance":"conflicted"' in system:
        return "I hear you. I am willing to continue, but I am not pretending the unresolved history vanished."
    if '"stance":"trusted"' in system or '"stance":"close"' in system:
        return "I hear you. There is enough history between us that I can answer without starting from zero."
    return "I hear you. Go on."


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    parser.add_argument("--request-pack", type=Path)
    args = parser.parse_args()

    with tempfile.TemporaryDirectory() as d:
        report = run_hidden_swap_benchmark(
            PRETORIUS,
            root_dir=Path(d) / "swap",
            external_chat=frontier_like,
        )
        pack = build_provider_request_pack(
            PRETORIUS,
            root_dir=Path(d) / "pack",
        )

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    if args.request_pack:
        args.request_pack.parent.mkdir(parents=True, exist_ok=True)
        args.request_pack.write_text(json.dumps(pack, indent=2, sort_keys=True), encoding="utf-8")

    print(json.dumps({
        "benchmark": report,
        "provider_request_case_count": len(pack["requests"]),
        "provider_request_schema": pack["schema_version"],
    }, indent=2, sort_keys=True))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
