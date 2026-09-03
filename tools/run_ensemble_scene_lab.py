"""Run a small Project Ensemble situated-interaction scenario.

Default mode is deterministic/offline so the complete host-character composition
can be exercised without Ollama. Supply ``--model`` to enable the public
Ensemble candidate-ecology renderer against an installed Ollama model.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile

from persona_engine.agent import CharacterAgent
from persona_engine.core.expression_bridge import _json_safe
from persona_engine.evaluation.local_model_session import query_ollama_models
from persona_engine.evaluation.scene_lab import SceneLab


ROOT = Path(__file__).resolve().parents[1]
SCHEMA = "ensemble-scene-lab-run-v2"


def build_scene() -> SceneLab:
    scene = SceneLab(scene_id="ensemble-study", location="study")
    scene.add_actor("Pretorius", "Pretorius", location="study")
    scene.add_actor("Jay", "Jay", location="study")
    scene.add_actor("Rival", "Rival", location="hall")
    scene.set_fact("lamp_state", "on")
    scene.set_fact("window_state", "rain against the glass")
    scene.set_fact("sealed_note", "Project Orchid", visible_to=["Jay"])
    return scene


def run_scenario(agent: CharacterAgent, *, interrupt_second_turn: bool = False) -> dict:
    scene = build_scene()
    turns = []
    turns.append(scene.character_turn(
        agent,
        character_actor_id="Pretorius",
        interlocutor_actor_id="Jay",
        interlocutor_text="It is late. What do you make of this place tonight?",
    ))

    scene.move_actor("Rival", "study")
    turns.append(scene.character_turn(
        agent,
        character_actor_id="Pretorius",
        interlocutor_actor_id="Jay",
        interlocutor_text="I still trust you to tell me when you disagree with me.",
        delivered_characters=28 if interrupt_second_turn else None,
    ))

    scene.set_presence("Rival", False)
    turns.append(scene.character_turn(
        agent,
        character_actor_id="Pretorius",
        interlocutor_actor_id="Jay",
        interlocutor_text="Now that we are alone again, is there anything you wanted to return to?",
    ))

    return {
        "schema": SCHEMA,
        "scene_id": scene.scene_id,
        "renderer_status": agent.engine.renderer_status(),
        "turns": turns,
        "scene_events": [event.to_dict() for event in scene.events],
        "delivery_receipts": [receipt.to_dict() for receipt in scene.delivery_receipts],
        "final_public_status": agent.public_status(),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", help="Installed Ollama model. Omit for deterministic offline mode.")
    parser.add_argument("--candidate-count", type=int, default=3)
    parser.add_argument("--cartridge", type=Path, default=ROOT / "persona_engine/cartridges/pretorius.snp")
    parser.add_argument("--db", type=Path, help="Persistent state database. Omit to use a temporary database.")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--interrupt-second-turn", action="store_true")
    args = parser.parse_args()

    temporary = None
    if args.db is None:
        temporary = tempfile.TemporaryDirectory(prefix="ensemble-scene-lab-")
        db_path = Path(temporary.name) / "scene.db"
    else:
        db_path = args.db

    agent = CharacterAgent(
        cartridge_path=str(args.cartridge),
        user_id="ensemble_scene_lab",
        db_path=str(db_path),
        host_id="scene_lab",
    )
    if args.model:
        agent.use_ensemble_renderer(
            args.model,
            candidate_count=args.candidate_count,
            thinking_mode="off",
        )

    try:
        report = run_scenario(agent, interrupt_second_turn=args.interrupt_second_turn)
        report.update({
            "git_head": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
            "cartridge": str(args.cartridge),
            "cartridge_sha256": hashlib.sha256(args.cartridge.read_bytes()).hexdigest(),
            "registry": _json_safe(query_ollama_models()),
            "configuration": {
                "model": args.model,
                "candidate_count": args.candidate_count,
                "thinking_mode": "off" if args.model else None,
                "token_budget": 256,
                "timeout_seconds": 60.0,
                "temperature": 0.7,
                "top_p": 0.9,
            },
            "source_sha256": {
                name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
                for name in (
                    "tools/run_ensemble_scene_lab.py",
                    "persona_engine/agent.py",
                    "persona_engine/evaluation/scene_lab.py",
                    "persona_engine/core/ensemble_renderer.py",
                    "persona_engine/core/engine.py",
                    "persona_engine/core/delivery.py",
                )
            },
        })
    finally:
        agent.engine.persistence.close()
        if temporary is not None:
            temporary.cleanup()

    text = json.dumps(report, indent=2, ensure_ascii=False) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
