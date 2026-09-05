"""Run a deterministic no-LLM DUCK organism smoke scenario."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from persona_engine.agent import CharacterAgent
from persona_engine.core.identity import CoreIdentity
from persona_engine.duck import DuckOrganism, ExternalEvent, WayfarerSubjectAdapter


def run(db_path: str) -> dict:
    identity = CoreIdentity(
        name="DuckSmoke",
        core_beliefs=("I persist through my history.",),
        temperament="curious",
        entity_uuid="33333333-3333-4333-8333-333333333333",
    )
    agent = CharacterAgent(identity, user_id="operator", db_path=db_path)
    organism = DuckOrganism(WayfarerSubjectAdapter(agent), organism_id="duck-smoke")
    organism.ingest(ExternalEvent(
        event_id="smoke-event",
        kind="observation",
        payload={
            "description": "A sealed box appears on the table.",
            "salience": 0.70,
            "novelty": 0.85,
            "self_relevance": 0.35,
            "action_candidates": [{
                "action_id": "inspect-box",
                "action_type": "inspect",
                "expected_world_effects": {"knowledge_gain": 0.4},
                "expected_self_effects": {"drive:exploration": 0.2, "drive:certainty": 0.1},
                "risk": 0.02,
                "uncertainty": 0.10,
            }],
        },
        source="smoke_world",
        timestamp=1.0,
    ))
    traces = organism.run_until_idle(max_cycles=4)
    return {
        "status": "PASS",
        "subject_id": organism.current_state().subject_id,
        "organism_id": organism.current_state().organism_id,
        "tick": organism.current_state().tick,
        "cycles": len(traces),
        "last_action": organism.current_state().action_ledger[-1]["intention"]["action"]["action_type"] if traces else None,
        "metacognition": organism.metacognitive_report(),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    with tempfile.TemporaryDirectory(prefix="duck-smoke-") as temp:
        result = run(str(Path(temp) / "subject.db"))
    text = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
