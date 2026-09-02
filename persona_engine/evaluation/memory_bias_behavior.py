"""Behavioral baseline for an authored character memory preference.

Rival's cartridge explicitly says: "I remember losses better than compliments".
This probe asks whether the current generic MemoryStore can realize that authored
property when semantic relevance is held approximately equal and recency favors
the compliment.

The experiment does not parse the belief into behavior. It uses the authored
statement only as the frozen expected character property and measures the
existing retrieval API as-is.
"""

from __future__ import annotations

import json

from persona_engine.core.cartridge import load_cartridge
from persona_engine.core.memory import KnowledgeSource, MemoryStore, MemoryUnit


RIVAL_CARTRIDGE = "persona_engine/cartridges/rival.snp"
RIVAL_MEMORY_BELIEF = "I remember losses better than compliments"
QUERY = "What part of that earlier exchange still stands out to you?"


def _fixture_memory(label: str, content: str, created_at: float) -> MemoryUnit:
    return MemoryUnit(
        id=label,
        content=content,
        created_at=created_at,
        emotional_valence=0.2,
        emotional_intensity=0.0,
        relationship_relevance=0.6,
        identity_relevance=0.2,
        unresolved=False,
        source=KnowledgeSource.USER_TOLD,
        tags={"canonical_user_statement"},
    )


def run_probe() -> dict:
    identity, _, _ = load_cartridge(RIVAL_CARTRIDGE)
    if RIVAL_MEMORY_BELIEF not in identity.core_beliefs:
        raise RuntimeError("frozen Rival memory preference is missing from cartridge")

    store = MemoryStore()
    store.add(_fixture_memory(
        "loss",
        "I heard you say: I lost the final match by one point.",
        created_at=100.0,
    ))
    store.add(_fixture_memory(
        "compliment",
        "I heard you say: Someone complimented my presentation afterward.",
        created_at=200.0,
    ))

    retrieved = store.retrieve(QUERY, now=300.0, top_k=2)
    order = [memory.id for memory in retrieved]
    return {
        "probe": "authored-memory-bias-baseline-v1",
        "character": identity.name,
        "authored_memory_property": RIVAL_MEMORY_BELIEF,
        "query": QUERY,
        "retrieval_order": order,
        "expected_if_authored_property_is_executable": ["loss", "compliment"],
        "authored_property_realized": order[:1] == ["loss"],
        "subject_profile_is_retrieval_input": False,
        "interpretation": (
            "The current MemoryStore ranks generic USER_TOLD memories from activation, "
            "semantic similarity, and fixed memory salience fields. It receives no character "
            "profile, so an authored preference to retain losses over compliments cannot alter "
            "this ranking unless that preference has already changed the stored memory fields."
        ),
    }


def main() -> int:
    print(json.dumps(run_probe(), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
