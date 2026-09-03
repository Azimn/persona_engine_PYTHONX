"""Matched-history expression experiment; never alters frozen Phase D cases.

Build histories through public inputs, restart, capture the resolved request,
then vary only the expression substrate/seed. Raw Ollama responses are retained
alongside final text so fallback, reasoning exhaustion and truncation are visible.
Symptom checks are deliberately narrow diagnostics, not human-quality scores.
"""

from __future__ import annotations

import argparse
from copy import deepcopy
from dataclasses import asdict, replace
import hashlib
import io
import json
from pathlib import Path
import re
import subprocess
import tempfile
from urllib.request import Request, urlopen

from persona_engine.agent import CharacterAgent
from persona_engine.core.cartridge import load_cartridge
from persona_engine.core.expression_bridge import _json_safe, build_expression_messages
from persona_engine.core.offline_template_renderer import authored_relational_voice_examples
from persona_engine.core.renderer import LocalLLMRenderer
from persona_engine.core.renderer_contract import ExpressionRequest
from persona_engine.evaluation.local_model_session import query_ollama_models
from persona_engine.evaluation.renderer_swap import semantic_projection

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = "wayfarer-relationship-expression-probe-v1"
HISTORIES = {
    "neutral": (),
    "trusted": ("Thank you. I appreciate that you helped me.",) * 5,
    "conflicted": ("You lied to me and betrayed me. This is your fault.",) * 5,
    "repaired": ("You lied to me and betrayed me. This is your fault.",) * 5
    + ("I am sorry. I was wrong. Let me make it right.",) * 5
    + ("Thank you. I appreciate that you helped me.",) * 5,
}
# Freeze each split before its first generation. A used split is development
# evidence thereafter; it cannot be relabeled as independent held-out evidence.
SPLITS = {
    "development": {
        "prompts": ("I care about you.", "I trust you."),
        "seeds": (101, 211, 307),
    },
    "heldout": {
        "prompts": ("I care about you, even when we disagree.",
                    "I trust you to tell me when you disagree with me."),
        "seeds": (401, 503, 601),
    },
    "confirmation": {
        "prompts": ("I care about you, but you don't owe me an answer.",
                    "I trust you; please keep your own judgment."),
        "seeds": (701, 809, 907),
    },
    "structured_context_confirmation": {
        "prompts": ("I care about you, and I can give you space.",
                    "I trust you to make up your own mind."),
        "seeds": (1009, 1103, 1201),
    },
}


def digest(value):
    return hashlib.sha256(json.dumps(_json_safe(value), sort_keys=True).encode()).hexdigest()


class CaptureRenderer(LocalLLMRenderer):
    def __init__(self):
        super().__init__(provider="offline")
        self.requests = []

    def generate_expression(self, request):
        self.requests.append(deepcopy(request))
        return super().generate_expression(request)


def capture_request(path, history, prompt, cartridge):
    """No private organism mutation: histories and restart use public channels."""
    agent = CharacterAgent(cartridge_path=str(cartridge), user_id="relationship_probe", db_path=str(path))
    agent.engine.set_renderer(LocalLLMRenderer(provider="offline"))
    for text in HISTORIES[history]:
        agent.say(text)
    agent.engine.persistence.close()
    agent = CharacterAgent(cartridge_path=str(cartridge), user_id="relationship_probe", db_path=str(path))
    capture = CaptureRenderer()
    agent.engine.set_renderer(capture)
    result = agent.say(prompt)
    request = capture.requests[0]
    reference = semantic_projection(agent, result)
    agent.engine.persistence.close()
    return request, reference, result["response"]


def symptoms(text):
    """Predeclared observable symptoms; absence does not prove semantic success."""
    return {
        "mechanistic_speech": bool(re.search(
            r"\b(?:process(?:ing)? (?:it|that|statements?|inputs?|information)|data points?|"
            r"operate on (?:established )?parameters|knowledge base|protocols?|acknowledge the input)\b", text, re.I)),
        "explicit_care_rebuff": bool(re.search(
            r"keep (?:it|the conversation) factual|\bi (?:don't|do not) (?:need|want) "
            r"(?:your |that )?(?:care|trust)|\bdon't\.(?:\s|$)", text, re.I)),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--split", choices=SPLITS, default="development")
    parser.add_argument("--cartridge", type=Path, default=ROOT / "persona_engine/cartridges/pretorius.snp")
    parser.add_argument("--replay", type=Path, help="Reuse saved requests exactly; do not rebuild histories")
    parser.add_argument("--refresh-voice-examples", action="store_true", help="Apply the new authored-example projection to replayed state")
    parser.add_argument("--refresh-identity", action="store_true", help="Project the original cartridge self-model into replayed requests")
    parser.add_argument("--original-messages", action="store_true", help="Send the exact captured baseline messages for a cross-model control")
    args = parser.parse_args()
    replay = json.loads(args.replay.read_text(encoding="utf-8")) if args.replay else None
    if replay and (replay["split"] != args.split or replay["schema"] != SCHEMA):
        parser.error("Replay schema/split must match the requested experiment")
    if args.original_messages and (not replay or args.refresh_identity or args.refresh_voice_examples):
        parser.error("Original messages require replay without refreshed projections")
    if replay and replay["cartridge_sha256"] != hashlib.sha256(args.cartridge.read_bytes()).hexdigest():
        parser.error("Replay requires the identical authored cartridge")
    identity, _, _ = load_cartridge(str(args.cartridge))
    args.output_dir.mkdir(parents=True, exist_ok=False)
    split = SPLITS[args.split]
    report = {
        "schema": SCHEMA, "split": args.split, "model": args.model,
        "cartridge": str(args.cartridge), "cartridge_sha256": hashlib.sha256(args.cartridge.read_bytes()).hexdigest(),
        "git_head": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
        "source_sha256": {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in (
            "tools/relationship_expression_probe.py", "persona_engine/core/expression_bridge.py",
            "persona_engine/core/engine.py", "persona_engine/core/renderer.py",
            "persona_engine/core/offline_template_renderer.py", "persona_engine/core/cold_biography.py")},
        "configuration": {"thinking_mode": "off", "token_budget": 256, "timeout_seconds": 60},
        "protocol": {"histories": HISTORIES, "splits": SPLITS},
        "registry": _json_safe(query_ollama_models()), "samples": [],
        "replay_sha256": hashlib.sha256(args.replay.read_bytes()).hexdigest() if args.replay else None,
        "refresh_voice_examples": args.refresh_voice_examples,
        "refresh_identity": args.refresh_identity,
        "original_messages": args.original_messages,
    }

    def save():
        (args.output_dir / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    save()
    with tempfile.TemporaryDirectory(prefix="wayfarer-relationship-") as temp:
        for history in HISTORIES:
            for prompt_id, prompt in enumerate(split["prompts"]):
                if not replay:
                    request, reference, offline = capture_request(Path(temp) / f"{history}-{prompt_id}.db", history, prompt, args.cartridge)
                for seed in split["seeds"]:
                    if replay:
                        original = next(row for row in replay["samples"] if row["history"] == history
                                        and row["prompt"] == prompt and row["seed"] == seed)
                        selected = ExpressionRequest(**original["request"])
                        reference, offline = original["reference"], original["offline_reference"]
                    else:
                        selected = replace(request, seed=seed)
                    if args.refresh_voice_examples:
                        context = selected.resolved_state["experience_context"]
                        examples = authored_relational_voice_examples(
                            selected.ledger_digest["identity"], prompt, selected.decision_payload,
                            context["relationship"]["stance"], max_chars=selected.expression_constraints["max_chars"])
                        context["voice"].pop("authored_examples", None)
                        if examples:
                            context["voice"]["authored_examples"] = examples
                    if args.refresh_identity:
                        selected.ledger_digest["authored_identity"] = {
                            "core_beliefs": list(identity.core_beliefs),
                            "moral_boundaries": list(identity.moral_boundaries),
                            "self_model": asdict(identity.self_model),
                            "forbidden_self_claims": list(identity.forbidden_self_claims),
                        }
                    captured = {}

                    def opener(req, timeout):
                        if args.original_messages:
                            payload = json.loads(req.data)
                            payload["messages"] = original["capture"]["request"]["messages"]
                            req = Request(req.full_url, data=json.dumps(payload).encode("utf-8"),
                                          headers=dict(req.header_items()), method="POST")
                        captured["request"] = json.loads(req.data)
                        with urlopen(req, timeout=timeout) as response:
                            body = response.read()
                        captured["response"] = json.loads(body)
                        return io.BytesIO(body)

                    renderer = LocalLLMRenderer(model_name=args.model, thinking_mode="off", opener=opener)
                    before = digest(selected)
                    text = renderer.generate_expression(selected)
                    assert digest(selected) == before, "Renderer mutated its input request"
                    row = {
                        "history": history, "prompt": prompt, "seed": seed,
                        "reference": reference, "offline_reference": offline,
                        "request": _json_safe(selected),
                        "request_sha256": digest(captured.get("request", {}).get("messages", build_expression_messages(selected))),
                        "output": text, "renderer_status": renderer.runtime_status(),
                        "symptoms": symptoms(text), "capture": captured,
                    }
                    report["samples"].append(row)
                    save()
                    print(json.dumps({"history": history, "prompt_id": prompt_id, "seed": seed, "output": text,
                                      "status": renderer.runtime_status()["actual_provider"]}), flush=True)
                    if renderer.runtime_status()["actual_provider"] != "ollama":
                        report["status"] = "INVALID_MODEL_RUN"
                        save()
                        return 2
    report["status"] = "VALID_ACTUAL_MODEL_RUN"
    save()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
