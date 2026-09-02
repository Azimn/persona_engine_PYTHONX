"""Baseline probe for character-relative autobiographical memory encoding.

The probe holds one neutral user-reported event constant across several existing
cartridges and compares the typed USER_TOLD memory written by the production
turn path. It does not claim that the current encoding is wrong; it measures
whether character identity is presently an input to that memory representation.
"""

from __future__ import annotations

import json
import tempfile
from dataclasses import asdict
from pathlib import Path

from persona_engine.agent import CharacterAgent
from persona_engine.core.memory import KnowledgeSource


EVENT_TEXT = "I found a small silver locket in the hallway."
CARTRIDGES = (
    "persona_engine/cartridges/friendly.snp",
    "persona_engine/cartridges/pretorius.snp",
    "persona_engine/cartridges/rival.snp",
)


def _memory_signature(memory) -> dict:
    return {
        "content": memory.content,
        "emotional_valence": round(float(memory.emotional_valence), 6),
        "emotional_intensity": round(float(memory.emotional_intensity), 6),
        "relationship_relevance": round(float(memory.relationship_relevance), 6),
        "identity_relevance": round(float(memory.identity_relevance), 6),
        "unresolved": bool(memory.unresolved),
        "source": memory.source.value,
        "tags": sorted(memory.tags),
        "compressed": bool(memory.compressed),
    }


def run_probe() -> dict:
    cases = []
    signatures = []
    for cartridge in CARTRIDGES:
        with tempfile.TemporaryDirectory() as temp_dir:
            agent = CharacterAgent(
                cartridge_path=cartridge,
                user_id="encoding_probe_user",
                db_path=str(Path(temp_dir) / "state.db"),
            )
            agent.say(EVENT_TEXT)
            user_memories = [
                memory
                for memory in agent.engine.memory.memories
                if memory.source == KnowledgeSource.USER_TOLD
            ]
            if not user_memories:
                raise RuntimeError(f"no USER_TOLD memory produced for {cartridge}")
            memory = user_memories[-1]
            signature = _memory_signature(memory)
            signatures.append(json.dumps(signature, sort_keys=True))
            cases.append({
                "cartridge": cartridge,
                "character": agent.engine.identity.name,
                "temperament": agent.engine.identity.temperament,
                "memory": signature,
            })

    return {
        "probe": "memory-encoding-subjectivity-baseline-v1",
        "event_text": EVENT_TEXT,
        "case_count": len(cases),
        "unique_memory_signatures": len(set(signatures)),
        "all_memory_signatures_identical": len(set(signatures)) == 1,
        "character_profile_is_encoding_input": False,
        "cases": cases,
        "interpretation": (
            "For this neutral user-reported event, the ordinary USER_TOLD autobiographical "
            "record is structurally identical across contrasting cartridges. Character-specific "
            "state may affect later retrieval, appraisal, cognition, or response, but the stored "
            "memory representation itself does not currently encode a cartridge-relative meaning."
        ),
    }


def main() -> int:
    print(json.dumps(run_probe(), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
