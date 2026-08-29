#!/usr/bin/env python3
"""Measure sequential cold-biography lookup cost as canonical history grows.

The fixture uses the same Persistence canonical-event insertion path but omits
full character turns so the measurement isolates archive lookup rather than
appraisal, rendering, checkpoints or other runtime work.
"""

from __future__ import annotations

import argparse
import json
import os
import statistics
import tempfile
import time
import tracemalloc
import uuid
from pathlib import Path

from persona_engine.core.cold_biography import retrieve_cold_biography
from persona_engine.core.persistence import Persistence

CHARACTER_ID = "Pretorius"
USER_ID = "alice"
QUERY = "Do you remember the observatory code word I told you?"
TARGET = "amber-otter"
DEFAULT_SIZES = (100, 1000, 5000, 10000)


def _seed(path: str, count: int) -> Persistence:
    persistence = Persistence(path)
    persistence.bind_subject(CHARACTER_ID, USER_ID, str(uuid.uuid4()))
    base_time = 1_700_000_000.0
    with persistence.transaction() as conn:
        for index in range(count):
            if index == 0:
                text = "Please remember this: the observatory code word is amber-otter."
            else:
                text = f"Routine catalog note {index}: ordinary shelf marker {index}."
            persistence._append_continuity_event_conn(
                conn,
                character_id=CHARACTER_ID,
                user_id=USER_ID,
                timestep=index + 1,
                event_type="input",
                payload={"user_text": text, "memory_types": ["user_input"]},
                wall_time=base_time + index,
                legacy_event_id=None,
            )
    return persistence


def _lookup(persistence: Persistence):
    return retrieve_cold_biography(
        persistence,
        CHARACTER_ID,
        USER_ID,
        QUERY,
        top_k=4,
    )


def _measure_one(count: int) -> dict:
    with tempfile.TemporaryDirectory() as directory:
        db = os.path.join(directory, "history.db")
        seed_start = time.perf_counter()
        persistence = _seed(db, count)
        seed_seconds = time.perf_counter() - seed_start

        start = time.perf_counter()
        first = _lookup(persistence)
        first_ms = (time.perf_counter() - start) * 1000.0

        repeats = []
        for _ in range(5):
            start = time.perf_counter()
            result = _lookup(persistence)
            repeats.append((time.perf_counter() - start) * 1000.0)
        median_ms = statistics.median(repeats)

        tracemalloc.start()
        before_current, _ = tracemalloc.get_traced_memory()
        peak_result = _lookup(persistence)
        after_current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        transient_peak = max(0, int(peak - before_current))
        retained_delta = max(0, int(after_current - before_current))

        conn = persistence.conn
        try:
            row_count = int(conn.execute("SELECT COUNT(*) FROM continuity_event").fetchone()[0])
        finally:
            conn.close()

        target_found = any(TARGET in memory.content.lower() for memory in peak_result)
        return {
            "canonical_input_events": row_count,
            "database_bytes": os.path.getsize(db),
            "seed_seconds": seed_seconds,
            "first_lookup_ms": first_ms,
            "repeat_lookup_ms": repeats,
            "median_repeat_lookup_ms": median_ms,
            "events_scanned_per_second_at_median": (count / (median_ms / 1000.0)) if median_ms > 0 else None,
            "tracemalloc_transient_peak_bytes": transient_peak,
            "tracemalloc_retained_delta_bytes": retained_delta,
            "returned_candidates": len(first),
            "target_found": target_found,
        }


def run(sizes=DEFAULT_SIZES) -> dict:
    rows = [_measure_one(int(size)) for size in sizes]
    all_grounded = all(row["target_found"] and row["returned_candidates"] == 1 for row in rows)
    peaks = [row["tracemalloc_transient_peak_bytes"] for row in rows]
    return {
        "probe": "cold-biography-latency-scaling-v1",
        "lookup_strategy": "sequential_sqlite_stream_plus_fixed_heap",
        "query": QUERY,
        "sizes": list(map(int, sizes)),
        "all_grounded": all_grounded,
        "measurements": rows,
        "peak_allocation_growth_ratio": (max(peaks) / max(1, min(peaks))) if peaks else None,
        "interpretation": "This benchmark measures the current intentionally simple O(n) cold-reader. It is evidence about latency and transient allocation on the CI Python runtime, not a direct C99 hardware claim.",
    }


def markdown(result: dict) -> str:
    lines = [
        "# Cold Biography Latency Scaling",
        "",
        f"Probe: `{result['probe']}`",
        "",
        "| Canonical inputs | DB bytes | First lookup ms | Median repeat ms | Transient peak bytes | Target found |",
        "| ---: | ---: | ---: | ---: | ---: | :---: |",
    ]
    for row in result["measurements"]:
        lines.append(
            f"| {row['canonical_input_events']} | {row['database_bytes']} | {row['first_lookup_ms']:.3f} | "
            f"{row['median_repeat_lookup_ms']:.3f} | {row['tracemalloc_transient_peak_bytes']} | {row['target_found']} |"
        )
    lines.extend([
        "",
        "The reader streams canonical input history and retains only the fixed-size candidate heap. Archive growth should therefore primarily appear as lookup latency rather than a proportional resident-memory requirement.",
        "",
        "No index is justified by this probe alone. An index should be added only if measured latency crosses a practical interaction budget on target-like hardware.",
    ])
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json")
    parser.add_argument("--markdown")
    parser.add_argument("--sizes", nargs="*", type=int, default=list(DEFAULT_SIZES))
    args = parser.parse_args()
    result = run(args.sizes)
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
    if not result["all_grounded"]:
        raise SystemExit("cold-biography latency fixture lost grounded target recall")


if __name__ == "__main__":
    main()
