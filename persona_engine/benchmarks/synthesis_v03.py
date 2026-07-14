"""Reproducible performance probe for situated synthesis."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import tempfile
import time

from persona_engine.agent import CharacterAgent
from persona_engine.core.synthesis import SynthesisInfluence, derive_integration_capacity, synthesize


def run(cartridge: str, iterations: int = 10000) -> dict[str, float | int]:
    influences = tuple(
        SynthesisInfluence(
            influence_id=f"memory:{index}",
            kind="memory" if index % 3 else "evidence",
            label=f"bounded influence {index}",
            strength=(index % 10) / 10.0,
            immediate=index % 7 == 0,
            emotional_congruence=(index % 5) / 5.0,
            contradictory=index % 11 == 0,
            reality_support=(index % 4) / 4.0,
        )
        for index in range(32)
    )
    capacity = derive_integration_capacity(
        energy=0.55,
        fatigue=0.45,
        sensory_load=0.60,
        dominant_pressure=0.75,
        unresolved_conflict=0.30,
        open_loop_count=3,
        interruption_load=1.0,
        recent_failure=1.0,
    )

    started = time.perf_counter()
    result = None
    for _ in range(iterations):
        result = synthesize(influences, capacity)
    synthesis_ms = (time.perf_counter() - started) * 1000.0 / iterations
    assert result is not None
    serialized_bytes = len(json.dumps(result.to_dict(), separators=(",", ":")).encode("utf-8"))

    with tempfile.TemporaryDirectory() as directory:
        agent = CharacterAgent(
            cartridge_path=cartridge,
            user_id="synthesis_benchmark",
            db_path=str(Path(directory) / "benchmark.db"),
        )
        started = time.perf_counter()
        for _ in range(1000):
            agent.idle()
        idle_ms = (time.perf_counter() - started) * 1000.0 / 1000.0

    return {
        "bounded_influences": len(influences),
        "synthesis_kernel_ms_per_turn": round(synthesis_ms, 6),
        "serialized_synthesis_result_bytes": serialized_bytes,
        "total_existing_idle_cycle_ms": round(idle_ms, 6),
        "added_synthesis_idle_work": 0,
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cartridge", default="persona_engine/cartridges/neutral.snp")
    parser.add_argument("--iterations", type=int, default=10000)
    args = parser.parse_args(argv)
    print(json.dumps(run(args.cartridge, max(1, args.iterations)), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
