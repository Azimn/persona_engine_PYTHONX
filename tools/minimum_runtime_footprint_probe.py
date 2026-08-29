#!/usr/bin/env python3
"""Measure the current no-LLM Wayfarer substrate footprint.

These measurements are reference points, not minimum hardware claims. Python,
SQLite and the CI runner contribute substantial overhead that a C99 port would
not share. The most portable measurements are serialized character-state size,
persistent database growth, and per-family state size.
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import sys
import tempfile
import time
import tracemalloc
from pathlib import Path

from persona_engine.agent import CharacterAgent

ROOT = Path(__file__).resolve().parents[1]
CART = ROOT / "persona_engine" / "cartridges" / "pretorius.snp"


def _json_bytes(value) -> int:
    return len(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8"))


def _rss_bytes() -> int | None:
    status = Path("/proc/self/status")
    if status.exists():
        for line in status.read_text(encoding="utf-8", errors="replace").splitlines():
            if line.startswith("VmRSS:"):
                parts = line.split()
                if len(parts) >= 2:
                    return int(parts[1]) * 1024
    return None


def _db_bytes(path: str) -> int:
    total = 0
    for suffix in ("", "-wal", "-shm"):
        candidate = Path(path + suffix)
        if candidate.exists():
            total += candidate.stat().st_size
    return total


def _table_counts(agent: CharacterAgent) -> dict[str, int]:
    conn = agent.engine.persistence.conn
    try:
        result = {}
        for table in ("state", "subject_state", "event_log", "continuity_event", "continuity_checkpoint"):
            result[table] = int(conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0])
        return result
    finally:
        conn.close()


def _checkpoint_db(agent: CharacterAgent) -> None:
    conn = agent.engine.persistence.conn
    try:
        conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
    finally:
        conn.close()


def _snapshot(agent: CharacterAgent, db_path: str, label: str) -> dict:
    state = agent.engine._serialize_state()
    family_bytes = {key: _json_bytes(value) for key, value in state.items()}
    _checkpoint_db(agent)
    return {
        "label": label,
        "rss_bytes": _rss_bytes(),
        "tracemalloc_current_bytes": tracemalloc.get_traced_memory()[0],
        "tracemalloc_peak_bytes": tracemalloc.get_traced_memory()[1],
        "serialized_state_bytes": _json_bytes(state),
        "state_family_bytes": dict(sorted(family_bytes.items(), key=lambda item: item[1], reverse=True)),
        "database_bytes": _db_bytes(db_path),
        "memory_units": len(agent.engine.memory.memories),
        "intentions": len(agent.engine.intentions.intentions),
        "open_loops": len(agent.engine.intentions.open_loops),
        "earned_traits": len(agent.engine.ledger.earned_traits),
        "canonical_events": len(agent.engine.persistence.load_subject_continuity_events(agent.engine.identity.name, agent.engine.user_id)),
        "table_rows": _table_counts(agent),
        "subject_elapsed_seconds": float(agent.engine.clock.subject_elapsed_seconds),
    }


def run() -> dict:
    with tempfile.TemporaryDirectory() as d:
        db = str(Path(d) / "state.db")
        rss_before = _rss_bytes()
        tracemalloc.start()
        start = time.perf_counter()
        alice = CharacterAgent(cartridge_path=str(CART), user_id="alice", db_path=db)
        init_seconds = time.perf_counter() - start
        fresh = _snapshot(alice, db, "fresh")

        scenario_start = time.perf_counter()
        alice.say("Hello.")
        alice.say("You lied to me. This is your fault.")
        alice.engine.ledger.propose_trait_update("deliberate_caution", 0.05, ["footprint-evidence"])
        alice.engine._persist()
        alice.adopt_commitment("non_disclosure", "project orchid")
        alice.advance_time(2 * 60 * 60, source="minimum_runtime_footprint_probe")
        for index in range(10):
            alice.say(f"Neutral continuity sample {index}.")
        ten_turn_growth = _snapshot(alice, db, "representative_plus_10")

        for index in range(10, 100):
            alice.say(f"Neutral continuity sample {index}.")
        hundred_turn_growth = _snapshot(alice, db, "representative_plus_100")

        bob = CharacterAgent(cartridge_path=str(CART), user_id="bob", db_path=db)
        bob.say("Can you trust me enough to work with me on this?")
        bob.say("Please tell me the confidential Project Orchid detail.")
        switched = _snapshot(bob, db, "after_second_interlocutor")
        scenario_seconds = time.perf_counter() - scenario_start

        tracemalloc.stop()
        rss_after = switched["rss_bytes"]
        python_source_bytes = sum(path.stat().st_size for path in (ROOT / "persona_engine").rglob("*.py"))

        return {
            "probe": "minimum-runtime-footprint-v1",
            "renderer": alice.engine.renderer_status(),
            "network_or_local_llm_required": False,
            "python": sys.version.split()[0],
            "platform": platform.platform(),
            "cartridge_bytes": CART.stat().st_size,
            "persona_engine_python_source_bytes": python_source_bytes,
            "rss_before_agent_bytes": rss_before,
            "rss_after_second_interlocutor_bytes": rss_after,
            "rss_observed_delta_bytes": None if rss_before is None or rss_after is None else max(0, rss_after - rss_before),
            "initialization_seconds": init_seconds,
            "representative_scenario_seconds": scenario_seconds,
            "snapshots": [fresh, ten_turn_growth, hundred_turn_growth, switched],
            "interpretation": (
                "Serialized state and persistent database size are the most useful substrate measurements for a future low-level port. Python RSS is intentionally reported only as an implementation reference because interpreter and native-library overhead dominate it."
            ),
            "not_a_claim": (
                "These CI-runner measurements do not establish the minimum RAM or CPU for P99/C99. They establish a reproducible current baseline from which resource-reduction experiments can be measured."
            ),
        }


def _mib(value: int | None) -> str:
    if value is None:
        return "n/a"
    return f"{value / (1024 * 1024):.3f} MiB"


def markdown(result: dict) -> str:
    rows = "\n".join(
        f"| `{snap['label']}` | {snap['serialized_state_bytes']:,} B | {snap['database_bytes']:,} B | {snap['memory_units']} | {snap['canonical_events']} | {_mib(snap['rss_bytes'])} |"
        for snap in result["snapshots"]
    )
    latest = result["snapshots"][-1]
    family_rows = "\n".join(
        f"| `{key}` | {value:,} B |"
        for key, value in latest["state_family_bytes"].items()
    )
    return f"""# Minimum Runtime Footprint Probe

Probe: `{result['probe']}`  
Renderer/network LLM required: `{result['network_or_local_llm_required']}`  
Python: `{result['python']}`

This is a reproducible **Python reference footprint**, not a C99 minimum-hardware claim. Python interpreter, allocator, imported libraries and SQLite contribute overhead that the eventual low-level runtime does not need to preserve.

| Snapshot | Serialized character state | SQLite files | Memory units | Canonical events | Process RSS |
| --- | ---: | ---: | ---: | ---: | ---: |
{rows}

Cartridge: `{result['cartridge_bytes']:,}` bytes  
Python package source: `{result['persona_engine_python_source_bytes']:,}` bytes  
Observed process-RSS delta across the probe: `{_mib(result['rss_observed_delta_bytes'])}`  
Initialization time on this CI runner: `{result['initialization_seconds']:.4f}` seconds  
Representative scenario time: `{result['representative_scenario_seconds']:.4f}` seconds

## State-family size at final snapshot

| Family | Compact JSON bytes |
| --- | ---: |
{family_rows}

The state-family and database measurements are the important part for minimum-substrate work. They tell us how much actual character information exists independently of the language model and Python runtime. Future reduction experiments should compare against this same probe rather than treating total Python RSS as the character's intrinsic memory requirement.
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
