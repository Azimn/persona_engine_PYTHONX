"""Small reproducible performance probe for the v0.2 simulated-life records."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import tempfile
import time
import tracemalloc

from persona_engine.agent import CharacterAgent
from persona_engine.core.embedding import HashEmbeddingProvider, NoEmbeddingProvider
from persona_engine.core.lived_experience import ExperienceStore, WorldEventLedger
from persona_engine.core.memory import MemoryStore, MemoryUnit
from persona_engine.core.vitality import LifeState, VitalityEventEngine


def _allocated_bytes(factory) -> int:
    tracemalloc.start()
    before = tracemalloc.take_snapshot()
    value = factory()
    after = tracemalloc.take_snapshot()
    size = sum(stat.size_diff for stat in after.compare_to(before, "lineno") if stat.size_diff > 0)
    tracemalloc.stop()
    assert value is not None
    return size


def run(cartridge: str) -> dict:
    def make_events():
        ledger = WorldEventLedger()
        for index in range(1000):
            ledger.create(tick=index, timestamp=float(index), event_type="benchmark", action="occurred", outcome=f"event {index}", source="benchmark")
        return ledger

    events = make_events()
    event_memory = _allocated_bytes(make_events)
    event_json = len(json.dumps(events.to_list(), separators=(",", ":")).encode("utf-8"))

    def make_experiences():
        store = ExperienceStore()
        for event in events.recent(1000):
            store.perceive(event, "benchmark", attention=0.8, salience=0.5, emotional_residue="neutral")
        return store

    experiences = make_experiences()
    experience_memory = _allocated_bytes(make_experiences)
    experience_json = len(json.dumps(experiences.to_list(), separators=(",", ":")).encode("utf-8"))

    def retrieval(provider) -> float:
        store = MemoryStore(provider)
        for index in range(1000):
            store.add(MemoryUnit(f"I remember benchmark event {index}.", created_at=float(index), salience=(index % 10) / 10.0))
        started = time.perf_counter()
        for _ in range(100):
            store.retrieve_explained("benchmark event 500", 2000.0, top_k=5)
        return (time.perf_counter() - started) * 1000.0 / 100.0

    no_embedding_ms = retrieval(NoEmbeddingProvider())
    hash_embedding_ms = retrieval(HashEmbeddingProvider(64))

    state = LifeState()
    vitality = VitalityEventEngine(42)
    started = time.perf_counter()
    for tick in range(10000):
        vitality.tick(state, tick)
    vitality_tick_ms = (time.perf_counter() - started) * 1000.0 / 10000.0

    started = time.perf_counter()
    for _ in range(1000):
        vitality.catch_up(LifeState(), 0, 86400.0, max_steps=12)
    catch_up_ms = (time.perf_counter() - started) * 1000.0 / 1000.0

    with tempfile.TemporaryDirectory() as directory:
        db = Path(directory) / "representative.db"
        agent = CharacterAgent(cartridge_path=cartridge, user_id="benchmark", db_path=str(db))
        agent.engine.world_events = events
        agent.engine.experiences = experiences
        agent.engine._persist()
        db_size = db.stat().st_size

    return {
        "world_events_1000_allocated_bytes": event_memory,
        "world_events_1000_json_bytes": event_json,
        "subjective_experiences_1000_allocated_bytes": experience_memory,
        "subjective_experiences_1000_json_bytes": experience_json,
        "retrieval_no_embeddings_ms": round(no_embedding_ms, 4),
        "retrieval_hash_embeddings_ms": round(hash_embedding_ms, 4),
        "vitality_tick_ms": round(vitality_tick_ms, 6),
        "offline_catch_up_one_day_ms": round(catch_up_ms, 6),
        "representative_db_bytes": db_size,
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cartridge", default="persona_engine/cartridges/neutral.snp")
    args = parser.parse_args(argv)
    print(json.dumps(run(args.cartridge), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
