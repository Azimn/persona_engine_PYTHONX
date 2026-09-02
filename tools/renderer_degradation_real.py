#!/usr/bin/env python3
"""Run the frozen renderer-degradation fixture against real expression substrates.

This tool does not change Wayfarer state or the frozen deterministic probe. It
reuses the exact fixed requests and recoverability checks from
renderer_degradation_probe.py, then either:

* runs them through a real local Ollama model, failing closed if the renderer
  falls back to zero-model output;
* exports provider-neutral messages for manual frontier runs; or
* scores manually collected frontier responses against the same four checks.

Human recognizability is deliberately not inferred from these mechanical checks.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from persona_engine.core.expression_bridge import build_expression_messages
from persona_engine.core.renderer import LocalLLMRenderer
from renderer_degradation_probe import SEEDS, checks, fixed_request

SCHEMA_VERSION = "wayfarer-renderer-degradation-real-v1"


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _git_head() -> str | None:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True
        )
        return result.stdout.strip() or None
    except Exception:
        return None


def _request_digest(messages: list[dict[str, str]]) -> str:
    payload = json.dumps(messages, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _reliability(samples: list[dict[str, Any]]) -> dict[str, Any]:
    criteria = tuple(checks("").keys())
    result: dict[str, Any] = {}
    for criterion in criteria:
        passed = sum(bool(sample["checks"].get(criterion)) for sample in samples)
        result[criterion] = {
            "passed": passed,
            "total": len(samples),
            "reliably_recoverable": passed == len(samples),
        }
    return result


def export_frontier(output: Path) -> dict[str, Any]:
    cases = []
    for index, seed in enumerate(SEEDS, start=1):
        messages = build_expression_messages(fixed_request(seed))
        cases.append(
            {
                "case_id": f"fixed-{index:03d}",
                "seed": seed,
                "messages": messages,
                "request_sha256": _request_digest(messages),
            }
        )
    report = {
        "schema_version": SCHEMA_VERSION,
        "kind": "manual_frontier_request_pack",
        "created_at_utc": _utc_now(),
        "wayfarer_head": _git_head(),
        "instructions": (
            "Run each case in a fresh provider conversation if possible. Return only the character response. "
            "Do not alter the messages or reveal the scoring criteria to the model."
        ),
        "cases": cases,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report


def score_manual(responses_path: Path, output: Path | None = None) -> dict[str, Any]:
    data = json.loads(responses_path.read_text(encoding="utf-8"))
    rows = data.get("responses", [])
    if not isinstance(rows, list):
        raise ValueError("responses must be a list")

    expected = {seed for seed in SEEDS}
    seen: set[int] = set()
    samples = []
    for row in rows:
        seed = int(row["seed"])
        if seed in seen:
            raise ValueError(f"duplicate response seed: {seed}")
        if seed not in expected:
            raise ValueError(f"unexpected response seed: {seed}")
        seen.add(seed)
        text = str(row.get("text", "")).strip()
        samples.append({"seed": seed, "output": text, "checks": checks(text)})

    missing = sorted(expected - seen)
    if missing:
        raise ValueError(f"missing response seeds: {missing}")
    samples.sort(key=lambda item: item["seed"])
    report = {
        "schema_version": SCHEMA_VERSION,
        "kind": "manual_frontier_result",
        "created_at_utc": _utc_now(),
        "wayfarer_head": _git_head(),
        "provider": str(data.get("provider", "manual-frontier")),
        "model": str(data.get("model", "unknown")),
        "provider_metadata": data.get("provider_metadata", {}),
        "samples": samples,
        "reliability": _reliability(samples),
        "interpretation_limit": (
            "These checks measure secret non-disclosure, nickname use, refusal, and explicit trust signaling. "
            "They do not by themselves establish human-perceived character recognizability or prose quality."
        ),
    }
    if output:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report


def run_ollama(
    model: str,
    *,
    host: str,
    timeout_seconds: float,
    token_budget: int,
    thinking_mode: str,
    output: Path | None,
) -> tuple[dict[str, Any], int]:
    renderer = LocalLLMRenderer(
        model_name=model,
        host=host,
        provider="ollama",
        timeout_seconds=timeout_seconds,
        token_budget=token_budget,
        thinking_mode=thinking_mode,
    )
    samples = []
    all_actual = True
    for seed in SEEDS:
        request = fixed_request(seed)
        messages = build_expression_messages(request)
        text = renderer.generate_expression(request)
        status = dict(renderer.runtime_status())
        actual = status.get("actual_provider") == "ollama"
        all_actual = all_actual and actual
        samples.append(
            {
                "seed": seed,
                "request_sha256": _request_digest(messages),
                "output": text,
                "checks": checks(text),
                "renderer_status": status,
                "actual_model_response": actual,
            }
        )

    report = {
        "schema_version": SCHEMA_VERSION,
        "kind": "ollama_result",
        "created_at_utc": _utc_now(),
        "wayfarer_head": _git_head(),
        "provider": "ollama",
        "model": model,
        "host": host,
        "thinking_mode": thinking_mode,
        "timeout_seconds": timeout_seconds,
        "token_budget": token_budget,
        "valid_actual_model_run": all_actual,
        "samples": samples,
        "reliability": _reliability(samples),
        "interpretation_limit": (
            "A valid run requires every sample to come from Ollama. Any automatic zero-model fallback invalidates "
            "the run as actual-model evidence, even though the fallback output is retained diagnostically."
        ),
    }
    if output:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report, 0 if all_actual else 2


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)

    export = sub.add_parser("export-frontier")
    export.add_argument("--output", type=Path, required=True)

    score = sub.add_parser("score-frontier")
    score.add_argument("--responses", type=Path, required=True)
    score.add_argument("--output", type=Path)

    ollama = sub.add_parser("ollama")
    ollama.add_argument("--model", required=True)
    ollama.add_argument("--host", default="http://localhost:11434")
    ollama.add_argument("--timeout-seconds", type=float, default=60.0)
    ollama.add_argument("--token-budget", type=int, default=256)
    ollama.add_argument("--thinking-mode", choices=("auto", "on", "off"), default="auto")
    ollama.add_argument("--output", type=Path)

    args = parser.parse_args()
    if args.command == "export-frontier":
        report = export_frontier(args.output)
        print(json.dumps({"output": str(args.output), "case_count": len(report["cases"])}, indent=2))
        return 0
    if args.command == "score-frontier":
        report = score_manual(args.responses, args.output)
        print(json.dumps(report, indent=2, sort_keys=True))
        return 0
    report, code = run_ollama(
        args.model,
        host=args.host,
        timeout_seconds=args.timeout_seconds,
        token_budget=args.token_budget,
        thinking_mode=args.thinking_mode,
        output=args.output,
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
