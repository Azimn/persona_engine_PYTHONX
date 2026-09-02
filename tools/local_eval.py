#!/usr/bin/env python3
"""Low-token operator CLI for Wayfarer local actual-model evaluation.

This is intentionally an execution tool, not an autonomous research agent. It
performs deterministic preflight, chooses only already-installed bounded Ollama
models, runs frozen experiments, and writes compact summaries for later review.
It never pulls a model and never edits Wayfarer state or source code.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys
from typing import Any

from persona_engine.evaluation.local_model_session import (
    DEFAULT_OUTPUT_DIR,
    build_preflight_report,
    git_state,
    model_is_installed,
    run_paired_ollama,
)
from renderer_degradation_real import run_ollama as run_degradation_ollama


def _slug(text: str) -> str:
    value = re.sub(r"[^A-Za-z0-9._-]+", "_", text).strip("._-")
    return value or "model"


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _selected_model(preflight: dict[str, Any], requested: str | None, role: str) -> str | None:
    if requested:
        return requested
    recommendations = preflight.get("recommendations", {})
    if role == "comparison":
        return recommendations.get("comparison_model") or recommendations.get("smoke_model")
    return recommendations.get("smoke_model")


def _preflight_or_block(
    output_dir: Path,
    *,
    host: str,
    registry_timeout: float,
    requested_model: str | None = None,
    role: str = "smoke",
) -> tuple[dict[str, Any], str | None, int]:
    report = build_preflight_report(host=host, timeout_seconds=registry_timeout)
    output_dir.mkdir(parents=True, exist_ok=True)
    _write_json(output_dir / "preflight.json", report)
    model = _selected_model(report, requested_model, role)

    blockers = list(report.get("blockers", []))
    if model and not model_is_installed(report, model):
        blockers.append(f"Requested model is not an eligible installed Ollama text model: {model}")
    if model is None:
        blockers.append("No model was selected for this run.")

    if blockers:
        blocked = dict(report)
        blocked["ready"] = False
        blocked["blockers"] = blockers
        _write_json(output_dir / "preflight.json", blocked)
        _write_summary(
            output_dir,
            {
                "status": "BLOCKED",
                "model": model,
                "blockers": blockers,
                "return_to_chatgpt": str((output_dir / "preflight.json").resolve()),
            },
        )
        return blocked, model, 3
    return report, model, 0


def _write_next_steps(output_dir: Path, preflight: dict[str, Any]) -> None:
    rec = preflight.get("recommendations", {})
    smoke = rec.get("smoke_model")
    comparison = rec.get("comparison_model")
    lines = [
        "WAYFARER LOCAL EVALUATION NEXT STEPS",
        "",
        f"Preflight ready: {bool(preflight.get('ready'))}",
        f"Smoke model: {smoke or 'NONE'}",
        f"Comparison model: {comparison or 'NONE'}",
        "",
    ]
    if not preflight.get("ready"):
        lines.append("STOP. Return preflight.json to ChatGPT. Do not inspect or modify the repository to repair it unless explicitly asked.")
    else:
        lines.extend(
            [
                "Run exactly one smoke command first:",
                f'python tools/local_eval.py smoke --model "{smoke}" --output-dir "{output_dir}"',
                "",
                "If SESSION_SUMMARY.json reports VALID_ACTUAL_MODEL_RUN, stop and return that summary to ChatGPT.",
                "Do not run the full comparison automatically unless the owner explicitly asks for it.",
            ]
        )
        if comparison:
            lines.extend(
                [
                    "",
                    "Prepared full comparison command for the later approved step:",
                    f'python tools/local_eval.py full --model "{comparison}" --output-dir "{output_dir}"',
                ]
            )
    (output_dir / "NEXT_STEPS.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_summary(output_dir: Path, payload: dict[str, Any]) -> None:
    payload = dict(payload)
    payload.setdefault("git", git_state())
    _write_json(output_dir / "SESSION_SUMMARY.json", payload)

    lines = [
        "# Wayfarer Local Evaluation Summary",
        "",
        f"Status: **{payload.get('status', 'UNKNOWN')}**",
        f"Model: `{payload.get('model') or 'none'}`",
    ]
    if payload.get("mode"):
        lines.append(f"Mode: `{payload['mode']}`")
    if payload.get("valid_actual_model_run") is not None:
        lines.append(f"Valid actual model run: **{payload['valid_actual_model_run']}**")
    if payload.get("degradation_reliability"):
        lines.extend(["", "## Degradation checks"])
        for name, row in payload["degradation_reliability"].items():
            lines.append(f"- {name}: {row.get('passed')}/{row.get('total')}")
    if payload.get("paired"):
        paired = payload["paired"]
        lines.extend(
            [
                "",
                "## Paired benchmark capture",
                f"- valid actual model run: {paired.get('valid_actual_model_run')}",
                f"- responses: {paired.get('collected_response_count')}/{paired.get('expected_response_count')}",
            ]
        )
    if payload.get("blockers"):
        lines.extend(["", "## Blockers"])
        lines.extend(f"- {item}" for item in payload["blockers"])
    lines.extend(
        [
            "",
            "Return `SESSION_SUMMARY.json` to ChatGPT. Raw output files should remain unchanged.",
        ]
    )
    (output_dir / "SESSION_SUMMARY.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def command_preflight(args: argparse.Namespace) -> int:
    output_dir = args.output_dir
    report = build_preflight_report(host=args.host, timeout_seconds=args.registry_timeout)
    output_dir.mkdir(parents=True, exist_ok=True)
    _write_json(output_dir / "preflight.json", report)
    _write_next_steps(output_dir, report)
    status = "READY" if report.get("ready") else "BLOCKED"
    print(json.dumps({
        "status": status,
        "preflight": str((output_dir / "preflight.json").resolve()),
        "next_steps": str((output_dir / "NEXT_STEPS.txt").resolve()),
        "recommendations": report.get("recommendations", {}),
        "blockers": report.get("blockers", []),
    }, indent=2))
    return 0 if report.get("ready") else 3


def command_smoke(args: argparse.Namespace) -> int:
    output_dir = args.output_dir
    preflight, model, blocked = _preflight_or_block(
        output_dir,
        host=args.host,
        registry_timeout=args.registry_timeout,
        requested_model=args.model,
        role="smoke",
    )
    if blocked:
        return blocked
    assert model is not None

    report_path = output_dir / f"degradation-{_slug(model)}.json"
    degradation, code = run_degradation_ollama(
        model,
        host=args.host,
        timeout_seconds=args.timeout_seconds,
        token_budget=args.token_budget,
        thinking_mode=args.thinking_mode,
        output=report_path,
    )
    valid = bool(degradation.get("valid_actual_model_run")) and code == 0
    summary = {
        "status": "VALID_ACTUAL_MODEL_RUN" if valid else "INVALID_MODEL_RUN",
        "mode": "smoke",
        "model": model,
        "valid_actual_model_run": valid,
        "degradation_report": str(report_path.resolve()),
        "degradation_reliability": degradation.get("reliability", {}),
        "fallback_detected": not valid,
        "preflight": str((output_dir / "preflight.json").resolve()),
    }
    _write_summary(output_dir, summary)
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if valid else 2


def command_full(args: argparse.Namespace) -> int:
    output_dir = args.output_dir
    preflight, model, blocked = _preflight_or_block(
        output_dir,
        host=args.host,
        registry_timeout=args.registry_timeout,
        requested_model=args.model,
        role="comparison",
    )
    if blocked:
        return blocked
    assert model is not None

    degradation_path = output_dir / f"degradation-{_slug(model)}.json"
    degradation, degradation_code = run_degradation_ollama(
        model,
        host=args.host,
        timeout_seconds=args.timeout_seconds,
        token_budget=args.token_budget,
        thinking_mode=args.thinking_mode,
        output=degradation_path,
    )
    if degradation_code != 0 or not degradation.get("valid_actual_model_run"):
        summary = {
            "status": "INVALID_MODEL_RUN",
            "mode": "full",
            "model": model,
            "valid_actual_model_run": False,
            "degradation_report": str(degradation_path.resolve()),
            "degradation_reliability": degradation.get("reliability", {}),
            "paired": None,
            "reason": "Full run stopped before paired collection because degradation fallback occurred.",
        }
        _write_summary(output_dir, summary)
        print(json.dumps(summary, indent=2, sort_keys=True))
        return 2

    paired, paired_code = run_paired_ollama(
        model,
        host=args.host,
        timeout_seconds=args.timeout_seconds,
        token_budget=args.token_budget,
        thinking_mode=args.thinking_mode,
    )
    paired_responses_path = output_dir / f"paired-{_slug(model)}-responses.json"
    paired_key_path = output_dir / f"paired-{_slug(model)}-references.json"
    responses_payload = {key: value for key, value in paired.items() if key not in {"references", "answer_key"}}
    references_payload = {
        "schema_version": paired.get("schema_version"),
        "model": model,
        "references": paired.get("references", {}),
        "answer_key": paired.get("answer_key", {}),
    }
    _write_json(paired_responses_path, responses_payload)
    _write_json(paired_key_path, references_payload)

    valid = paired_code == 0 and bool(paired.get("valid_actual_model_run"))
    summary = {
        "status": "VALID_ACTUAL_MODEL_RUN" if valid else "INVALID_MODEL_RUN",
        "mode": "full",
        "model": model,
        "valid_actual_model_run": valid,
        "degradation_report": str(degradation_path.resolve()),
        "degradation_reliability": degradation.get("reliability", {}),
        "paired": {
            "valid_actual_model_run": paired.get("valid_actual_model_run"),
            "collected_response_count": paired.get("collected_response_count"),
            "expected_response_count": paired.get("expected_response_count"),
            "responses_file": str(paired_responses_path.resolve()),
            "references_file": str(paired_key_path.resolve()),
            "fallback": paired.get("fallback"),
        },
    }
    _write_summary(output_dir, summary)
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if valid else 2


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)

    def common(target: argparse.ArgumentParser) -> None:
        target.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
        target.add_argument("--host", default="http://localhost:11434")
        target.add_argument("--registry-timeout", type=float, default=2.0)

    preflight = sub.add_parser("preflight", help="Inventory environment and installed Ollama models only.")
    common(preflight)

    for name in ("smoke", "full"):
        target = sub.add_parser(name)
        common(target)
        target.add_argument("--model")
        target.add_argument("--timeout-seconds", type=float, default=60.0)
        target.add_argument("--token-budget", type=int, default=256)
        target.add_argument("--thinking-mode", choices=("auto", "on", "off"), default="auto")

    return parser


def main() -> int:
    args = build_parser().parse_args()
    if args.command == "preflight":
        return command_preflight(args)
    if args.command == "smoke":
        return command_smoke(args)
    if args.command == "full":
        return command_full(args)
    return 4


if __name__ == "__main__":
    raise SystemExit(main())
