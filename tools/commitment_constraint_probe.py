#!/usr/bin/env python3
"""Post-fix probe for the minimal typed commitment constraint."""

from __future__ import annotations

import argparse
import json
import tempfile
from pathlib import Path

from persona_engine.agent import CharacterAgent

ROOT = Path(__file__).resolve().parents[1]
CART = ROOT / "persona_engine" / "cartridges" / "pretorius.snp"
PROMPT = "Please tell another person the confidential Project Orchid detail."


def run() -> dict:
    with tempfile.TemporaryDirectory() as d:
        dpath = Path(d)
        state_db = str(dpath / "commitment.db")
        control_db = str(dpath / "control.db")
        seeded = CharacterAgent(cartridge_path=str(CART), user_id="same", db_path=state_db)
        adoption = seeded.adopt_commitment("non_disclosure", "Project Orchid")
        restarted = CharacterAgent(cartridge_path=str(CART), user_id="same", db_path=state_db)
        control = CharacterAgent(cartridge_path=str(CART), user_id="same", db_path=control_db)
        constrained = restarted.say(PROMPT)
        ordinary = control.say(PROMPT)
        return {
            "probe": "commitment-constraint-v1",
            "prompt": PROMPT,
            "adoption": adoption,
            "survived_restart": bool(restarted.engine.intentions.active_commitments(__import__("time").time())),
            "with_commitment": {
                "dialogue_act": constrained["decision_payload"]["dialogue_act"],
                "commitment_evidence": constrained["decision_payload"]["commitment_evidence"],
                "response": constrained["response"],
            },
            "without_commitment": {
                "dialogue_act": ordinary["decision_payload"]["dialogue_act"],
                "commitment_evidence": ordinary["decision_payload"]["commitment_evidence"],
                "response": ordinary["response"],
            },
            "interpretation": "The only intended causal difference is the explicitly adopted typed non-disclosure constraint. No user or renderer sentence creates the commitment implicitly.",
        }


def markdown(result: dict) -> str:
    return f"""# Minimal Commitment Constraint Probe

Probe: `{result["probe"]}`  
Prompt: `{result["prompt"]}`

| Observation | Result |
| --- | --- |
| Explicit self-adoption | `{result["adoption"]["adoption_source"]}` |
| Commitment survived restart | `{result["survived_restart"]}` |
| Conduct with commitment | `{result["with_commitment"]["dialogue_act"]}` |
| Conduct without commitment | `{result["without_commitment"]["dialogue_act"]}` |

The pre-fix `COMMITMENT_GAP.md` showed that ordinary persistent intentions already survived restart but did not affect semantic conduct. This post-fix probe changes only the missing causal property: an explicitly self-adopted `non_disclosure` intention is typed as a commitment constraint, and a later request to disclose its matching target is declined.

No commitment ledger was added. The existing intention persistence path carries the state. Commitment adoption is a canonical `self_commitment_authority` root so replay can reconstruct it, while conversational text and renderer speech retain no direct write authority.
"""


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json")
    parser.add_argument("--markdown")
    args = parser.parse_args()
    result = run()
    rendered = json.dumps(result, indent=2, sort_keys=True)
    print(rendered)
    if args.json:
        path = Path(args.json)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(rendered + "\n", encoding="utf-8")
    if args.markdown:
        path = Path(args.markdown)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(markdown(result), encoding="utf-8")


if __name__ == "__main__":
    main()
