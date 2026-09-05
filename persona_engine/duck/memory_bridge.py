"""Activation bridge from DUCK attention into the existing subject memory store."""

from __future__ import annotations

from .types import CognitiveItem, clamp


class SubjectMemoryActivation:
    """Retrieve subject-owned memories without making DUCK their authority.

    Wayfarer remains the memory owner. This adapter intentionally lives at the
    DUCK boundary so another subject implementation can provide a different
    retrieval method later.
    """

    def retrieve(self, subject, *, query: str, now: float, tick: int, subject_id: str, top_k: int = 3) -> list[CognitiveItem]:
        query = str(query or "").strip()
        if not query:
            return []
        agent = getattr(subject, "agent", None)
        engine = getattr(agent, "engine", None)
        store = getattr(engine, "memory", None)
        if store is None or not hasattr(store, "retrieve"):
            return []

        with engine.state_transaction():
            engine._require_writer()
            memories = store.retrieve(query, float(now), top_k=max(0, int(top_k)))
            engine._persist()

        items: list[CognitiveItem] = []
        for memory in memories:
            emotional = clamp(getattr(memory, "emotional_intensity", 0.0))
            relationship = clamp(getattr(memory, "relationship_relevance", 0.0))
            identity = clamp(getattr(memory, "identity_relevance", 0.0))
            unresolved = 1.0 if getattr(memory, "unresolved", False) else 0.0
            salience = clamp(0.15 + emotional * 0.35 + relationship * 0.20 + identity * 0.20 + unresolved * 0.25)
            items.append(CognitiveItem(
                item_id=f"memory:{tick}:{memory.id}",
                tick=tick,
                kind="memory_activation",
                source_module="subject_memory",
                subject_id=subject_id,
                payload={
                    "memory_id": memory.id,
                    "content": memory.content,
                    "source": getattr(getattr(memory, "source", None), "value", "unknown"),
                    "unresolved": bool(getattr(memory, "unresolved", False)),
                },
                confidence=1.0,
                salience=salience,
                self_relevance=clamp(max(0.20, relationship, identity)),
                novelty=0.05,
                threat=clamp(emotional * 0.35 if float(getattr(memory, "emotional_valence", 0.0)) < 0 else 0.0),
                valence=max(-1.0, min(1.0, float(getattr(memory, "emotional_valence", 0.0)))),
                arousal=emotional,
                memory_refs=(str(memory.id),),
                provenance={"authority": "subject_memory", "memory_id": str(memory.id)},
                canonical=False,
            ))
        return items
