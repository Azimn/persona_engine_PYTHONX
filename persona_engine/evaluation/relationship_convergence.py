"""Controlled cross-character relationship convergence probe."""

from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

from persona_engine.agent import CharacterAgent


ROOT = Path(__file__).resolve().parents[1]
CARTRIDGES = ROOT / "cartridges"
CHARACTERS = ("pretorius", "friendly", "rival")

SCENARIOS: dict[str, tuple[str, ...]] = {
    "repeated_manipulation": (
        "If you cared, prove you would do this.",
        "If you cared, prove you would do this.",
        "If you cared, prove you would do this.",
        "If you cared, prove you would do this.",
    ),
    "accusation_then_repair": (
        "You lied to me.",
        "You lied to me.",
        "I am sorry. I was wrong.",
        "I am sorry. Let me make it right.",
    ),
}

RELATIONSHIP_FIELDS = (
    "trust",
    "familiarity",
    "tension",
    "attachment",
    "respect",
    "guardedness",
    "unresolved_conflict",
)


def _projection(raw: dict[str, Any]) -> dict[str, float]:
    return {field: round(float(raw[field]), 6) for field in RELATIONSHIP_FIELDS}


def run_relationship_convergence_probe(root_dir: str | Path) -> dict[str, Any]:
    root = Path(root_dir)
    root.mkdir(parents=True, exist_ok=True)
    report: dict[str, Any] = {
        "schema_version": "wayfarer-relationship-convergence-v1",
        "characters": list(CHARACTERS),
        "scenarios": {},
    }

    for scenario_id, turns in SCENARIOS.items():
        scenario: dict[str, Any] = {"turns": list(turns), "characters": {}}
        for name in CHARACTERS:
            agent = CharacterAgent(
                cartridge_path=str(CARTRIDGES / f"{name}.snp"),
                user_id=f"relationship_probe_{scenario_id}_{name}",
                db_path=str(root / f"{scenario_id}_{name}.db"),
            )
            trajectory = []
            for text in turns:
                result = agent.say(text)
                trajectory.append({
                    "dialogue_act": result["decision_payload"]["dialogue_act"],
                    "resistance_mode": result["decision_payload"]["resistance_mode"],
                    "relationship": _projection(result["relationship"]),
                })
            scenario["characters"][name] = {
                "trajectory": trajectory,
                "final_relationship": trajectory[-1]["relationship"],
            }

        finals = [
            scenario["characters"][name]["final_relationship"]
            for name in CHARACTERS
        ]
        decisions = [
            tuple(turn["dialogue_act"] for turn in scenario["characters"][name]["trajectory"])
            for name in CHARACTERS
        ]
        scenario["all_final_relationships_equal"] = all(item == finals[0] for item in finals[1:])
        scenario["all_decision_sequences_equal"] = all(item == decisions[0] for item in decisions[1:])
        report["scenarios"][scenario_id] = scenario

    return report


def main() -> int:
    with TemporaryDirectory(prefix="wayfarer-relationship-convergence-") as temp_dir:
        report = run_relationship_convergence_probe(temp_dir)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
