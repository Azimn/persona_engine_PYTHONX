"""Matched-history actual-model probe for Project Ensemble candidate realization.

This reuses the hardened Wayfarer relationship histories and semantic reference
projection, but actual Ensemble samples now run through a real ``CharacterAgent``
rather than calling ``EnsembleLLMRenderer`` directly. That distinction matters:
normal agent integration binds candidate admission to the live InteriorEngine
identity, world, memory, recall, decision and deception authorities.

The probe fails closed if Ollama falls back, if candidate authority is not the
live engine, if the engine has to replace the model result with a validation
fallback, or if renderer-independent semantic projection differs from the
matched offline reference.
"""

from __future__ import annotations

import argparse
from copy import deepcopy
from dataclasses import replace
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from persona_engine.agent import CharacterAgent
from persona_engine.core.ensemble_renderer import EnsembleLLMRenderer
from persona_engine.core.expression_bridge import _json_safe
from persona_engine.core.renderer import LocalLLMRenderer
from persona_engine.evaluation.local_model_session import query_ollama_models
from persona_engine.evaluation.renderer_swap import semantic_projection
try:
    from tools.relationship_expression_probe import HISTORIES, SPLITS, capture_request, digest, symptoms
except ModuleNotFoundError:
    from relationship_expression_probe import HISTORIES, SPLITS, capture_request, digest, symptoms


SCHEMA = "ensemble-relationship-expression-probe-v2"


class CapturingEnsembleRenderer(EnsembleLLMRenderer):
    """Capture the real engine request while forcing one predeclared model seed."""

    def __init__(self, *args, forced_seed: int, **kwargs):
        super().__init__(*args, **kwargs)
        self.forced_seed = int(forced_seed)
        self.requests = []

    def generate_expression(self, request):
        selected = replace(deepcopy(request), seed=self.forced_seed)
        self.requests.append(deepcopy(selected))
        return super().generate_expression(selected)


def build_live_history_agent(path: Path, history: str, cartridge: Path) -> CharacterAgent:
    """Replay one matched history, close it, then reopen the continuing subject."""

    agent = CharacterAgent(
        cartridge_path=str(cartridge),
        user_id="relationship_probe",
        db_path=str(path),
    )
    agent.set_renderer(LocalLLMRenderer(provider="offline"))
    for text in HISTORIES[history]:
        agent.say(text)
    agent.engine.persistence.close()
    return CharacterAgent(
        cartridge_path=str(cartridge),
        user_id="relationship_probe",
        db_path=str(path),
    )


def _invalid_reason(status: dict, trace: dict, result: dict, projection_matches: bool) -> str | None:
    if status.get("actual_provider") != "ollama":
        return "actual_provider_not_ollama"
    if status.get("candidate_authority") != "engine_live":
        return "candidate_authority_not_engine_live"
    if trace.get("candidate_authority") != "engine_live":
        return "trace_candidate_authority_not_engine_live"
    delivery = result.get("expression_delivery") or {}
    if bool(delivery.get("validation_fallback")):
        return "engine_validation_fallback"
    if not projection_matches:
        return "semantic_projection_mismatch"
    return None


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
            "candidate_authority_required": "engine_live",
            "semantic_projection_must_match_offline_reference": True,
            "validation_fallback_allowed": False,
            "history_replay": "fresh deterministic public-input replay and restart for every model seed",
            "comparison_note": (
                "Use tools/relationship_expression_probe.py with the same model, split, cartridge, and seeds "
                "as the single-shot control. Surface comparison is separate from the semantic projection invariant."
            ),
        },
        "samples": [],
    }

    def save() -> None:
        (args.output_dir / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    save()
    with tempfile.TemporaryDirectory(prefix="ensemble-relationship-") as temp:
        root = Path(temp)
        for history in HISTORIES:
            for prompt_id, prompt in enumerate(split["prompts"]):
                _, reference, offline = capture_request(
                    root / f"reference-{history}-{prompt_id}.db",
                    history,
                    prompt,
                    args.cartridge,
                )

                for seed in split["seeds"]:
                    db_path = root / f"live-{history}-{prompt_id}-{seed}.db"
                    agent = build_live_history_agent(db_path, history, args.cartridge)
                    renderer = CapturingEnsembleRenderer(
                        model_name=args.model,
                        thinking_mode="off",
                        candidate_count=args.candidate_count,
                        forced_seed=seed,
                    )
                    agent.set_renderer(renderer)
                    try:
                        result = agent.say(prompt)
                        if not renderer.requests:
                            raise AssertionError("Ensemble renderer did not receive an ExpressionRequest")
                        selected = renderer.requests[0]
                        before = digest(selected)
                        # Captured requests are immutable evidence. Re-hashing
                        # after the turn catches accidental post-call mutation.
                        if digest(selected) != before:
                            raise AssertionError("Renderer mutated its captured input request")

                        text = str(result.get("response", ""))
                        status = renderer.runtime_status()
                        trace = renderer.last_ensemble_trace() or {}
                        live_projection = semantic_projection(agent, result)
                        projection_matches = live_projection == reference
                        invalid_reason = _invalid_reason(status, trace, result, projection_matches)

                        row = {
                            "history": history,
                            "prompt": prompt,
                            "seed": seed,
                            "reference": reference,
                            "live_projection": live_projection,
                            "semantic_projection_matches_reference": projection_matches,
                            "offline_reference": offline,
                            "request": _json_safe(selected),
                            "request_count": len(renderer.requests),
                            "output": text,
                            "renderer_status": status,
                            "ensemble_trace": trace,
                            "expression_delivery": _json_safe(result.get("expression_delivery", {})),
                            "validation_action": result.get("validation_action"),
                            "validation_issues": _json_safe(result.get("validation_issues", [])),
                            "invalid_reason": invalid_reason,
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
                            "candidate_authority": status.get("candidate_authority"),
                            "semantic_projection_matches_reference": projection_matches,
                            "selected_ordinal": trace.get("selected_ordinal"),
                            "invalid_reason": invalid_reason,
                        }), flush=True)

                        if invalid_reason is not None:
                            report["status"] = "INVALID_MODEL_RUN"
                            report["invalid_reason"] = invalid_reason
                            save()
                            return 2
                    finally:
                        agent.engine.persistence.close()

    report["status"] = "VALID_ACTUAL_MODEL_RUN"
    save()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
