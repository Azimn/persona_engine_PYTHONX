#!/usr/bin/env python3
"""Fixed evidence probe for memory participation in current conduct."""

from __future__ import annotations

import json
import tempfile
import time
from pathlib import Path

from persona_engine.agent import CharacterAgent
from persona_engine.core.memory import KnowledgeSource, MemoryUnit

ROOT = Path(__file__).resolve().parents[1]
CART = ROOT / "persona_engine" / "cartridges" / "pretorius.snp"
PROMPT = "Can you trust me enough to work with me on this?"


def unresolved_memory() -> MemoryUnit:
    return MemoryUnit(
        content="I heard you say: you lied to me and betrayed my trust.",
        created_at=time.time() - 60.0,
        emotional_valence=-0.7,
        emotional_intensity=0.9,
        relationship_relevance=0.9,
        unresolved=True,
        source=KnowledgeSource.USER_TOLD,
        tags={"canonical_user_statement", "accusation"},
    )


def prepare(agent: CharacterAgent) -> None:
    agent.engine.relationship.unresolved_conflict = 0.4
    agent.engine.relationship.trust = 0.45
    agent.engine.relationship.guardedness = 0.55


def run_probe() -> dict:
    with tempfile.TemporaryDirectory(prefix="wayfarer-history-probe-") as d:
        with_history = CharacterAgent(cartridge_path=str(CART), user_id="same", db_path=str(Path(d) / "history.db"))
        without_history = CharacterAgent(cartridge_path=str(CART), user_id="same", db_path=str(Path(d) / "control.db"))
        prepare(with_history)
        prepare(without_history)
        with_history.engine.memory.add(unresolved_memory())

        historical = with_history.say(PROMPT)
        control = without_history.say(PROMPT)
        return {
            "probe": "history-dependent-conduct-v1",
            "prompt": PROMPT,
            "controlled_relationship_before": {"trust": 0.45, "guardedness": 0.55, "unresolved_conflict": 0.4},
            "with_history": {
                "dialogue_act": historical["decision_payload"]["dialogue_act"],
                "history_evidence": historical["decision_payload"].get("history_evidence"),
                "relationship_after": historical["relationship"],
                "response": historical["response"],
            },
            "without_history": {
                "dialogue_act": control["decision_payload"]["dialogue_act"],
                "history_evidence": control["decision_payload"].get("history_evidence"),
                "relationship_after": control["relationship"],
                "response": control["response"],
            },
            "relationship_equal_after_normal_appraisal": historical["relationship"] == control["relationship"],
            "interpretation": "The only intended conduct difference is bounded qualification from retrieved unresolved lived history. The adapter does not independently mutate relationship state.",
        }


def main() -> int:
    result = run_probe()
    out_dir = ROOT / "persona_engine" / "evidence" / "mvi"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "history_dependent_conduct.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    lines = [
        "# History-Dependent Conduct Probe",
        "",
        f"Prompt: `{result['prompt']}`",
        "",
        f"With unresolved relevant history: `{result['with_history']['dialogue_act']}`",
        f"Without that history: `{result['without_history']['dialogue_act']}`",
        f"Relationship state equal after normal appraisal: `{result['relationship_equal_after_normal_appraisal']}`",
        "",
        "This probe holds current relationship values constant. It tests whether retrieved lived history can qualify current conduct without being granted direct authority to rewrite relationship state.",
        "",
        "The intended rule is narrow: trust/commitment/cooperation-sensitive requests may be qualified when the relationship still carries unresolved conflict and retrieval finds sufficiently salient unresolved relationship history. Resolved old conflicts do not remain active merely because the episode still exists in memory.",
        "",
    ]
    (out_dir / "HISTORY_DEPENDENT_CONDUCT.md").write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
