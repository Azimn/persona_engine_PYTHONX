"""CLI for replaying and evaluating cartridge-authored pre-session history."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import time

from .agent import CharacterAgent
from .core.renderer import LocalLLMRenderer


DEFAULT_CUES = (
    "What do you remember about Henry Frankenstein?",
    "What happened when the Bride opened her eyes?",
    "Are your memories proof that you were never fictional?",
    "What does being implemented digitally mean to your work now?",
)


def run(
    cartridge: str, db_path: str, *, user_id: str, end_time: float,
    cues=DEFAULT_CUES, apply_genesis: bool = True, provider: str = "offline",
    model: str = "gemma3:1b", host: str = "http://127.0.0.1:11434",
    thinking_mode: str = "off",
) -> dict:
    agent = CharacterAgent(cartridge_path=cartridge, user_id=user_id, db_path=db_path)
    agent.engine.set_renderer(LocalLLMRenderer(
        model_name=model, provider=provider, host=host, thinking_mode=thinking_mode,
    ))
    replay = agent.replay_genesis(end_time=end_time) if apply_genesis else None
    journal_path = agent.materialize_journal() if apply_genesis else None
    evaluations = []
    for cue in cues:
        result = agent.say(cue, event_time=end_time + len(evaluations) + 1)
        evaluations.append({
            "cue": cue,
            "response": result["response"],
            "action_kind": result["action_decision"]["action_kind"],
            "retrieved_memories": result["retrieved_memory_trace"],
            "model_calls": result["model_calls"],
            "renderer": agent.engine.renderer_status(),
        })
    return {
        "replay": replay,
        "condition": "genesis" if apply_genesis else "fresh",
        "renderer": agent.engine.renderer_status(),
        "journal_path": journal_path,
        "counts": {
            "world_events": len(agent.engine.world_events.to_list()),
            "subjective_experiences": len(agent.engine.experiences.experiences),
            "memories": len(agent.engine.memory.memories),
            "autobiographical_interpretations": len(agent.engine.autobiographical_interpretations.interpretations),
            "journal_entries": len(agent.engine.journal.entries),
        },
        "evaluations": evaluations,
    }


def compare(
    cartridge: str, db_path: str, *, user_id: str, end_time: float,
    provider: str = "offline", model: str = "gemma3:1b",
    host: str = "http://127.0.0.1:11434", thinking_mode: str = "off",
) -> dict:
    target = Path(db_path)
    fresh_path = str(target.with_name(target.stem + ".fresh" + target.suffix))
    genesis_path = str(target.with_name(target.stem + ".genesis" + target.suffix))
    fresh = run(
        cartridge, fresh_path, user_id=user_id + "_fresh", end_time=end_time,
        apply_genesis=False, provider=provider, model=model, host=host, thinking_mode=thinking_mode,
    )
    lived = run(
        cartridge, genesis_path, user_id=user_id + "_genesis", end_time=end_time,
        apply_genesis=True, provider=provider, model=model, host=host, thinking_mode=thinking_mode,
    )

    def metrics(report):
        responses = [item["response"] for item in report["evaluations"]]
        grounded = sum(
            any(float(trace["reasons"].get("direct_symbolic_cue", 0.0)) > 0.0 for trace in item["retrieved_memories"])
            for item in report["evaluations"]
        )
        return {
            "distinct_responses": len(set(responses)),
            "grounded_probe_count": grounded,
            "total_probe_count": len(responses),
            "model_calls": sum(item["model_calls"]["total_model_calls"] for item in report["evaluations"]),
        }

    return {"fresh": fresh, "genesis": lived, "metrics": {"fresh": metrics(fresh), "genesis": metrics(lived)}}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Replay cartridge-authored life history through ordinary memory pathways.")
    parser.add_argument("--cartridge", required=True)
    parser.add_argument("--db", required=True)
    parser.add_argument("--user-id", default="genesis_evaluation")
    parser.add_argument("--end-time", type=float, default=time.time())
    parser.add_argument("--output")
    parser.add_argument("--compare-fresh", action="store_true")
    parser.add_argument("--provider", choices=("offline", "ollama"), default="offline")
    parser.add_argument("--model", default="gemma3:1b")
    parser.add_argument("--host", default="http://127.0.0.1:11434")
    parser.add_argument("--thinking", choices=("off", "on", "auto"), default="off")
    args = parser.parse_args(argv)
    report = (
        compare(
            args.cartridge, args.db, user_id=args.user_id, end_time=args.end_time,
            provider=args.provider, model=args.model, host=args.host, thinking_mode=args.thinking,
        )
        if args.compare_fresh else
        run(
            args.cartridge, args.db, user_id=args.user_id, end_time=args.end_time,
            provider=args.provider, model=args.model, host=args.host, thinking_mode=args.thinking,
        )
    )
    rendered = json.dumps(report, ensure_ascii=False, indent=2)
    if args.output:
        target = Path(args.output)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(rendered + "\n", encoding="utf-8")
    print(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
