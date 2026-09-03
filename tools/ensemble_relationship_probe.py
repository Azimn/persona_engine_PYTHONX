"""Matched-history actual-model probe for Project Ensemble candidate realization.

This intentionally reuses the hardened Wayfarer relationship histories and
ExpressionRequest capture path, but swaps only the expression substrate from a
single-shot LocalLLMRenderer to EnsembleLLMRenderer.  It is development evidence,
not a replacement for frozen Wayfarer benchmarks.
"""

from __future__ import annotations

import argparse
from dataclasses import replace
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile

from persona_engine.core.ensemble_renderer import EnsembleLLMRenderer
from persona_engine.core.expression_bridge import _json_safe
from persona_engine.evaluation.local_model_session import query_ollama_models
from tools.relationship_expression_probe import HISTORIES, SPLITS, capture_request, digest, symptoms


ROOT = Path(__file__).resolve().parents[1]
SCHEMA = "ensemble-relationship-expression-probe-v1"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--split", choices=SPLITS, default="structured_context_confirmation")
    parser.add_argument("--cartridge", type=Path, default=ROOT / "persona_engine/cartridges/pretorius.snp")
    parser.add_argument("--candidate-count", type=int, default=3)
    args = parser.parse_args()

    args.output_dir.mkdir(parents=True, exist_ok=False)
    split = SPLITS[args.split]
    report = {
        "schema": SCHEMA,
        "status": "RUNNING",
        "model": args.model,
        "candidate_count": args.candidate_count,
        "split": args.split,
        "cartridge": str(args.cartridge),
        "cartridge_sha256": hashlib.sha256(args.cartridge.read_bytes()).hexdigest(),
        "git_head": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
        "registry": _json_safe(query_ollama_models()),
        "protocol": {
            "histories": HISTORIES,
            "split": split,
            "comparison_note": (
                "Use tools/relationship_expression_probe.py with the same model, split, cartridge, and seeds "
                "as the single-shot control."
            ),
        },
        "samples": [],
    }

    def save() -> None:
        (args.output_dir / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    save()
    with tempfile.TemporaryDirectory(prefix="ensemble-relationship-") as temp:
        for history in HISTORIES:
            for prompt_id, prompt in enumerate(split["prompts"]):
                request, reference, offline = capture_request(
                    Path(temp) / f"{history}-{prompt_id}.db",
                    history,
                    prompt,
                    args.cartridge,
                )
                renderer = EnsembleLLMRenderer(
                    model_name=args.model,
                    thinking_mode="off",
                    candidate_count=args.candidate_count,
                )
                for seed in split["seeds"]:
                    selected = replace(request, seed=seed)
                    before = digest(selected)
                    text = renderer.generate_expression(selected)
                    if digest(selected) != before:
                        raise AssertionError("Renderer mutated its input request")
                    status = renderer.runtime_status()
                    row = {
                        "history": history,
                        "prompt": prompt,
                        "seed": seed,
                        "reference": reference,
                        "offline_reference": offline,
                        "request": _json_safe(selected),
                        "output": text,
                        "renderer_status": status,
                        "ensemble_trace": renderer.last_ensemble_trace(),
                        "symptoms": symptoms(text),
                    }
                    report["samples"].append(row)
                    save()
                    print(json.dumps({
                        "history": history,
                        "prompt_id": prompt_id,
                        "seed": seed,
                        "output": text,
                        "actual_provider": status.get("actual_provider"),
                        "selected_ordinal": (renderer.last_ensemble_trace() or {}).get("selected_ordinal"),
                    }), flush=True)
                    if status.get("actual_provider") != "ollama":
                        report["status"] = "INVALID_MODEL_RUN"
                        save()
                        return 2

    report["status"] = "VALID_ACTUAL_MODEL_RUN"
    save()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
