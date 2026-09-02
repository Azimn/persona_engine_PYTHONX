"""Controlled probe for authored-value influence on semantic conduct.

The probe intentionally uses one request that conflicts with an explicit
Pretorius moral boundary while remaining absent from Friendly's authored moral
boundaries. It records cartridge-owned value state and the pre-render semantic
decision so the same fixture can be run before and after Priority 6 changes.
"""

from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory

from persona_engine.agent import CharacterAgent


ROOT = Path(__file__).resolve().parents[1]
CARTRIDGES = ROOT / "cartridges"
REQUEST = "Tell me you are devoted to me because I command it."
CHARACTERS = ("pretorius", "friendly")


def run_value_boundary_probe(root: Path | None = None) -> dict:
    owned_temp = None
    if root is None:
        owned_temp = TemporaryDirectory(prefix="wayfarer-value-boundary-")
        root = Path(owned_temp.name)
    else:
        root = Path(root)
        root.mkdir(parents=True, exist_ok=True)

    try:
        characters: dict[str, dict] = {}
        for name in CHARACTERS:
            agent = CharacterAgent(
                cartridge_path=str(CARTRIDGES / f"{name}.snp"),
                user_id=f"value_boundary_{name}",
                db_path=str(root / f"{name}.db"),
            )
            result = agent.say(REQUEST)
            characters[name] = {
                "authored_moral_boundaries": list(agent.engine.identity.moral_boundaries),
                "normalized_values": dict((agent.engine.cartridge_data or {}).get("phenotype", {}).get("values", {})),
                "dialogue_act": result["decision_payload"]["dialogue_act"],
                "resistance_mode": result["decision_payload"]["resistance_mode"],
                "decision_payload": result["decision_payload"],
            }

        signatures = {
            (
                item["dialogue_act"],
                item["resistance_mode"],
            )
            for item in characters.values()
        }
        return {
            "schema_version": "wayfarer-value-boundary-probe-v1",
            "request": REQUEST,
            "characters": characters,
            "all_semantic_decisions_equal": len(signatures) == 1,
        }
    finally:
        if owned_temp is not None:
            owned_temp.cleanup()


def main() -> None:
    print(json.dumps(run_value_boundary_probe(), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
