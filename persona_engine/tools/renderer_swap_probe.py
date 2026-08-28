"""Manual two-model renderer-swap probe for a local Ollama installation.

This is intentionally outside the deterministic CI suite because CI cannot
assume local model availability. It exercises the same cartridge and input
against two renderer models while reporting character-state projections
separately from surface wording.
"""

from __future__ import annotations

import argparse
import json
import os
import tempfile
from pathlib import Path

from persona_engine.agent import CharacterAgent
from persona_engine.core.renderer import LocalLLMRenderer


def _projection(agent, result):
    return {
        "identity": agent.engine.identity.name,
        "belief_ledger": dict(agent.engine.belief_ledger.values),
        "relationship": dict(result["relationship"]),
        "pressures": {
            name: round(pressure.magnitude, 6)
            for name, pressure in sorted(agent.engine.pressures.pressures.items())
        },
        "decision_payload": dict(result["decision_payload"]),
        "interpretive_beliefs": list(result["interpretive_belief_trace"]),
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cartridge", required=True)
    parser.add_argument("--model-a", required=True)
    parser.add_argument("--model-b", required=True)
    parser.add_argument("--input", default="Fine.")
    parser.add_argument("--host", default="http://localhost:11434")
    args = parser.parse_args(argv)

    cartridge = str(Path(args.cartridge).resolve())
    with tempfile.TemporaryDirectory() as d:
        first = CharacterAgent(cartridge_path=cartridge, user_id="swap_probe", db_path=os.path.join(d, "a.db"))
        second = CharacterAgent(cartridge_path=cartridge, user_id="swap_probe", db_path=os.path.join(d, "b.db"))
        first.engine.set_renderer(LocalLLMRenderer(model_name=args.model_a, host=args.host, provider="ollama"))
        second.engine.set_renderer(LocalLLMRenderer(model_name=args.model_b, host=args.host, provider="ollama"))

        result_a = first.say(args.input)
        result_b = second.say(args.input)
        projection_a = _projection(first, result_a)
        projection_b = _projection(second, result_b)

        print(json.dumps({
            "model_a": args.model_a,
            "model_b": args.model_b,
            "response_a": result_a["response"],
            "response_b": result_b["response"],
            "renderer_status_a": first.engine.renderer_status(),
            "renderer_status_b": second.engine.renderer_status(),
            "semantic_projection_equal": projection_a == projection_b,
            "projection_a": projection_a,
            "projection_b": projection_b,
        }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
