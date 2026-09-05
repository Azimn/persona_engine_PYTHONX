#!/usr/bin/env python3
"""Optional real-Ollama end-to-end probe for the DUCK future runtime.

This is intentionally not part of hosted CI because it requires the user's local
Ollama daemon and installed models. It verifies the property that matters here:
renderer substitution changes the expression substrate while the same persistent
subject and organism continue across the swap.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import tempfile

from persona_engine.duck.host import FutureDuckHost


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Run DUCK with one or two installed Ollama models")
    parser.add_argument("--model-a", required=True)
    parser.add_argument("--model-b", default="")
    parser.add_argument("--root", default="")
    parser.add_argument("--cartridge", default="")
    parser.add_argument("--ollama-host", default="http://127.0.0.1:11434")
    args = parser.parse_args(argv)

    temporary = None
    if args.root:
        root = Path(args.root)
    else:
        temporary = tempfile.TemporaryDirectory(prefix="duck-local-model-")
        root = Path(temporary.name)
    cartridge = args.cartridge or str(Path(__file__).resolve().parents[1] / "persona_engine" / "cartridges" / "neutral.snp")
    host = FutureDuckHost.open(root, cartridge_path=cartridge, user_id="local-model-probe", ollama_host=args.ollama_host)
    initial_subject = host.subject.subject_id
    initial_organism = host.runtime.organism.current_state().organism_id

    def use(model):
        host.set_renderer({"provider": "ollama", "model_name": model, "thinking_mode": "off", "token_budget": 192})
        return host.send("Tell me briefly what matters to you in this moment.")

    first = use(args.model_a)
    second = use(args.model_b) if args.model_b else None
    if host.subject.subject_id != initial_subject:
        raise RuntimeError("subject identity changed during model substitution")
    if host.runtime.organism.current_state().organism_id != initial_organism:
        raise RuntimeError("organism identity changed during model substitution")
    result = {
        "result": "PASS",
        "subject_id": initial_subject,
        "organism_id": initial_organism,
        "model_a": args.model_a,
        "response_a": first["response"],
        "model_b": args.model_b or None,
        "response_b": second["response"] if second else None,
        "final_tick": host.runtime.tick,
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    if temporary is not None:
        temporary.cleanup()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
