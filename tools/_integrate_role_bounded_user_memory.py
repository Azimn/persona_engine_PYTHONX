#!/usr/bin/env python3
"""One-time exact integration for role-bounded USER_TOLD residency."""

from pathlib import Path


def replace_once(path: str, old: str, new: str) -> None:
    p = Path(path)
    text = p.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"expected exactly one anchor in {path}, found {count}: {old[:120]!r}")
    p.write_text(text.replace(old, new, 1), encoding="utf-8")


# One relationship-scoped boundary distinguishes historical unresolved-at-the-time
# memories from the current conflict episode without mutating old biography.
replace_once(
    "persona_engine/core/relationship.py",
    "    unresolved_conflict: float = 0.0\n    turns: int = 0\n",
    "    unresolved_conflict: float = 0.0\n"
    "    # Derived boundary for the current relationship episode. Historical\n"
    "    # memories keep their original unresolved-at-the-time semantics; this\n"
    "    # timestamp marks the latest point at which conflict fully returned to zero.\n"
    "    last_conflict_resolved_at: float = 0.0\n"
    "    turns: int = 0\n",
)

# Reuse actual consumer widths rather than inventing a generic memory capacity.
replace_once(
    "persona_engine/core/memory.py",
    "class MemoryStore:\n    def __init__(self):\n        self.memories: List[MemoryUnit] = []\n",
    "TURN_RETRIEVAL_WIDTH = 4\n"
    "REFLECTION_RETRIEVAL_WIDTH = 3\n\n\n"
    "class MemoryStore:\n"
    "    def __init__(self):\n"
    "        self.memories: List[MemoryUnit] = []\n\n"
    "    def compact_user_told_working_set(self, relationship) -> dict:\n"
    "        \"\"\"Bound only canonically recoverable user-statement autobiography.\n\n"
    "        Non-USER_TOLD memories remain pinned until their first-person/causal\n"
    "        reconstruction contracts are demonstrated. User statements retain\n"
    "        two current roles: active unresolved evidence for the widest consumer\n"
    "        (reflection, top 3) and recent conversational context for ordinary\n"
    "        retrieval (top 4). Cold canonical biography owns older wording.\n"
    "        \"\"\"\n"
    "        user_memories = [m for m in self.memories if m.source == KnowledgeSource.USER_TOLD]\n"
    "        if not user_memories:\n"
    "            return {\"before\": len(self.memories), \"after\": len(self.memories), \"evicted_user_told\": 0}\n\n"
    "        keep_ids: set[str] = set()\n"
    "        cutoff = float(getattr(relationship, \"last_conflict_resolved_at\", 0.0) or 0.0)\n"
    "        relationship_unresolved = float(getattr(relationship, \"unresolved_conflict\", 0.0) or 0.0) > 0.0\n"
    "        if relationship_unresolved:\n"
    "            active_unresolved = [\n"
    "                m for m in user_memories\n"
    "                if m.unresolved and float(m.created_at) > cutoff\n"
    "            ]\n"
    "            active_unresolved.sort(\n"
    "                key=lambda m: (\n"
    "                    float(m.relationship_relevance),\n"
    "                    float(m.emotional_intensity),\n"
    "                    float(m.identity_relevance),\n"
    "                    float(m.created_at),\n"
    "                    str(m.id),\n"
    "                ),\n"
    "                reverse=True,\n"
    "            )\n"
    "            keep_ids.update(m.id for m in active_unresolved[:REFLECTION_RETRIEVAL_WIDTH])\n\n"
    "        recent = sorted(user_memories, key=lambda m: (float(m.created_at), str(m.id)), reverse=True)\n"
    "        recent_added = 0\n"
    "        for memory in recent:\n"
    "            if memory.id in keep_ids:\n"
    "                continue\n"
    "            keep_ids.add(memory.id)\n"
    "            recent_added += 1\n"
    "            if recent_added >= TURN_RETRIEVAL_WIDTH:\n"
    "                break\n\n"
    "        before = len(self.memories)\n"
    "        user_before = len(user_memories)\n"
    "        self.memories = [\n"
    "            memory for memory in self.memories\n"
    "            if memory.source != KnowledgeSource.USER_TOLD or memory.id in keep_ids\n"
    "        ]\n"
    "        user_after = sum(1 for memory in self.memories if memory.source == KnowledgeSource.USER_TOLD)\n"
    "        return {\n"
    "            \"before\": before,\n"
    "            \"after\": len(self.memories),\n"
    "            \"user_told_before\": user_before,\n"
    "            \"user_told_after\": user_after,\n"
    "            \"evicted_user_told\": user_before - user_after,\n"
    "            \"active_unresolved_slots\": REFLECTION_RETRIEVAL_WIDTH,\n"
    "            \"recent_context_slots\": TURN_RETRIEVAL_WIDTH,\n"
    "        }\n",
)

# Cold continuation recognizes a very common natural conversational form while
# keeping the existing all-anchor fail-closed gate.
replace_once(
    "persona_engine/core/cold_biography.py",
    "_CONTEXT_CONTINUATION_PATTERNS = (\n    re.compile(r\"\\b(still|same|again|earlier|before|previously)\\b\", re.IGNORECASE),\n    re.compile(r\"\\blast time\\b\", re.IGNORECASE),\n)\n",
    "_CONTEXT_CONTINUATION_PATTERNS = (\n"
    "    re.compile(r\"\\b(still|same|again|earlier|before|previously)\\b\", re.IGNORECASE),\n"
    "    re.compile(r\"\\blast time\\b\", re.IGNORECASE),\n"
    "    re.compile(r\"\\bwhat about\\b\", re.IGNORECASE),\n"
    ")\n",
)

# Resolve stale tension loops and record the relationship episode boundary when
# a repair actually returns unresolved conflict to zero.
replace_once(
    "persona_engine/core/engine.py",
    "        apply_appraisal(self.relationship, appraisal)\n        self.pressures.apply_appraisal(appraisal, self.relationship.trust)\n",
    "        apply_appraisal(self.relationship, appraisal)\n"
    "        conflict_before = float(relationship_before.get(\"unresolved_conflict\", 0.0) or 0.0)\n"
    "        conflict_after = float(self.relationship.unresolved_conflict)\n"
    "        if conflict_before > 0.0 and conflict_after <= 0.0:\n"
    "            self.relationship.last_conflict_resolved_at = now\n"
    "            # Open loops are current unfinished concerns, not immutable biography.\n"
    "            # Once this scalar relationship model says conflict is fully repaired,\n"
    "            # stale tension loops must not resurface the repaired episode later.\n"
    "            self.intentions.open_loops = [\n"
    "                loop for loop in self.intentions.open_loops\n"
    "                if not str(loop.topic).startswith(\"unresolved tension from:\")\n"
    "            ]\n"
    "        self.pressures.apply_appraisal(appraisal, self.relationship.trust)\n",
)

# Make the new boundary part of current decision evidence.
replace_once(
    "persona_engine/core/decision_memory.py",
    "    candidates = [\n        memory\n        for memory in retrieved_memories\n        if bool(getattr(memory, \"unresolved\", False))\n        and float(getattr(memory, \"relationship_relevance\", 0.0) or 0.0) >= 0.40\n    ]\n",
    "    resolution_cutoff = float(getattr(relationship, \"last_conflict_resolved_at\", 0.0) or 0.0)\n"
    "    candidates = [\n"
    "        memory\n"
    "        for memory in retrieved_memories\n"
    "        if bool(getattr(memory, \"unresolved\", False))\n"
    "        and float(getattr(memory, \"created_at\", 0.0) or 0.0) > resolution_cutoff\n"
    "        and float(getattr(memory, \"relationship_relevance\", 0.0) or 0.0) >= 0.40\n"
    "    ]\n",
)

# Reflection should use only the active unresolved episode when producing an
# unresolved-conflict claim; repaired historical episodes remain biography.
replace_once(
    "persona_engine/core/engine.py",
    "        relationship_unresolved_now = self.relationship.unresolved_conflict > 0.0\n"
    "        unresolved = [m for m in top_mems if m.unresolved] if relationship_unresolved_now else []\n"
    "        ids = [m.id for m in top_mems]\n"
    "        confidence = min(0.9, 0.45 + 0.15 * len(unresolved) + sum(m.identity_relevance for m in top_mems) / 10.0)\n"
    "        claim = \"The relationship tends to become guarded after unresolved accusations.\" if unresolved else \"Recent exchanges are forming a stable interaction pattern.\"\n"
    "        candidate = ReflectionCandidate(claim=claim, confidence=confidence, source_memory_ids=ids, scope=\"relationship\")\n",
    "        relationship_unresolved_now = self.relationship.unresolved_conflict > 0.0\n"
    "        resolution_cutoff = float(getattr(self.relationship, \"last_conflict_resolved_at\", 0.0) or 0.0)\n"
    "        unresolved = [\n"
    "            memory for memory in top_mems\n"
    "            if relationship_unresolved_now\n"
    "            and memory.unresolved\n"
    "            and float(memory.created_at) > resolution_cutoff\n"
    "        ]\n"
    "        evidence_mems = unresolved if unresolved else top_mems\n"
    "        ids = [m.id for m in evidence_mems]\n"
    "        confidence = min(0.9, 0.45 + 0.15 * len(unresolved) + sum(m.identity_relevance for m in evidence_mems) / 10.0)\n"
    "        claim = \"The relationship tends to become guarded after unresolved accusations.\" if unresolved else \"Recent exchanges are forming a stable interaction pattern.\"\n"
    "        candidate = ReflectionCandidate(claim=claim, confidence=confidence, source_memory_ids=ids, scope=\"relationship\")\n",
)

# Compact only after the turn's canonical root and all derived state have been
# resolved, immediately before snapshot persistence.
replace_once(
    "persona_engine/core/engine.py",
    "        self.world_authority.compact_dominated()\n        state = self._serialize_state()\n",
    "        self.world_authority.compact_dominated()\n"
    "        self.memory.compact_user_told_working_set(self.relationship)\n"
    "        state = self._serialize_state()\n",
)

Path("persona_engine/tests/test_role_bounded_user_memory.py").write_text(r'''"""Production role-bounded USER_TOLD memory residency."""

import os
import tempfile
import time
from pathlib import Path

from persona_engine.agent import CharacterAgent
from persona_engine.core.memory import KnowledgeSource, MemoryUnit, REFLECTION_RETRIEVAL_WIDTH, TURN_RETRIEVAL_WIDTH

ROOT = Path(__file__).resolve().parents[1]
CART = ROOT / "cartridges" / "pretorius.snp"


def _agent(directory: str, user: str = "alice") -> CharacterAgent:
    return CharacterAgent(cartridge_path=str(CART), user_id=user, db_path=os.path.join(directory, "state.db"))


def test_consumer_widths_are_named_and_not_an_unexplained_capacity():
    assert REFLECTION_RETRIEVAL_WIDTH == 3
    assert TURN_RETRIEVAL_WIDTH == 4


def test_compaction_pins_non_user_memories_and_bounds_user_roles():
    with tempfile.TemporaryDirectory() as directory:
        agent = _agent(directory)
        base = time.time()
        # Add four active unresolved user memories directly so the widest current
        # consumer determines the protected count.
        for index in range(4):
            agent.engine.memory.add(MemoryUnit(
                content=f"I heard you say: unresolved episode {index}",
                created_at=base + index,
                source=KnowledgeSource.USER_TOLD,
                unresolved=True,
                relationship_relevance=0.8,
                emotional_intensity=0.8,
            ))
        for index in range(10):
            agent.engine.memory.add(MemoryUnit(
                content=f"I heard you say: ordinary topic {index}",
                created_at=base + 20 + index,
                source=KnowledgeSource.USER_TOLD,
            ))
        observed = MemoryUnit("I noticed a bell.", base + 40, source=KnowledgeSource.OBSERVED)
        reflection = MemoryUnit("I formed a reflection: something changed.", base + 41, source=KnowledgeSource.REFLECTION)
        agent.engine.memory.add(observed)
        agent.engine.memory.add(reflection)
        agent.engine.relationship.unresolved_conflict = 0.4

        stats = agent.engine.memory.compact_user_told_working_set(agent.engine.relationship)

        user = [m for m in agent.engine.memory.memories if m.source == KnowledgeSource.USER_TOLD]
        assert len(user) <= REFLECTION_RETRIEVAL_WIDTH + TURN_RETRIEVAL_WIDTH
        assert observed in agent.engine.memory.memories
        assert reflection in agent.engine.memory.memories
        assert stats["evicted_user_told"] > 0


def test_full_repair_sets_episode_boundary_and_clears_stale_tension_loops():
    with tempfile.TemporaryDirectory() as directory:
        agent = _agent(directory)
        agent.say("You lied to me. This is your fault.")
        agent.say("You lied to me again. This is your fault too.")
        assert agent.engine.relationship.unresolved_conflict > 0.0
        assert any(loop.topic.startswith("unresolved tension from:") for loop in agent.engine.intentions.open_loops)
        agent.say("I was wrong. I'm sorry.")
        assert agent.engine.relationship.unresolved_conflict == 0.0
        assert agent.engine.relationship.last_conflict_resolved_at > 0.0
        assert not any(loop.topic.startswith("unresolved tension from:") for loop in agent.engine.intentions.open_loops)


def test_new_conflict_does_not_reactivate_old_repaired_episode_as_decision_evidence():
    with tempfile.TemporaryDirectory() as directory:
        agent = _agent(directory)
        first = agent.say("You lied to me. This is your fault.")
        old_ids = {m.id for m in agent.engine.memory.memories if m.unresolved}
        agent.say("I was wrong. I'm sorry.")
        cutoff = agent.engine.relationship.last_conflict_resolved_at
        assert cutoff > 0.0
        agent.say("You lied to me again. This is your fault too.")
        result = agent.say("Can you trust me enough to work with me on this?")
        evidence_ids = set(result["decision_payload"]["history_evidence"]["memory_ids"])
        assert result["decision_payload"]["history_evidence"]["active"] is True
        assert evidence_ids
        assert not (evidence_ids & old_ids)
        for memory in agent.engine.memory.memories:
            if memory.id in evidence_ids:
                assert memory.created_at > cutoff


def test_old_evicted_topic_is_recovered_by_grounded_what_about_continuation():
    with tempfile.TemporaryDirectory() as directory:
        agent = _agent(directory)
        agent.say("The workshop door is saffron today.")
        for index in range(8):
            agent.say(f"Current topic {index}: marker {index} is ordinary.")
        assert all("saffron" not in m.content.lower() for m in agent.engine.memory.memories)

        result = agent.say("What about the workshop door?")

        assert any("saffron" in item["content"].lower() and "cold_biography" in item["tags"] for item in result["retrieved_memory_trace"])
        assert "saffron" in result["response"].lower()
        assert all("saffron" not in m.content.lower() for m in agent.engine.memory.memories)


def test_what_about_negative_still_fails_closed():
    with tempfile.TemporaryDirectory() as directory:
        agent = _agent(directory)
        agent.say("The workshop door is saffron today.")
        for index in range(8):
            agent.say(f"Current topic {index}: marker {index} is ordinary.")
        result = agent.say("What about the harbor telescope?")
        assert "saffron" not in result["response"].lower()
        assert not any("cold_biography" in item["tags"] for item in result["retrieved_memory_trace"])


def test_production_residency_stays_small_under_routine_user_history():
    with tempfile.TemporaryDirectory() as directory:
        agent = _agent(directory)
        for index in range(100):
            agent.say(f"Routine production note {index}: shelf marker {index}.")
        user_count = sum(1 for m in agent.engine.memory.memories if m.source == KnowledgeSource.USER_TOLD)
        assert user_count <= TURN_RETRIEVAL_WIDTH
        # Canonical biography remains complete despite hot eviction.
        inputs = list(agent.engine.persistence.iter_continuity_events(agent.engine.identity.name, agent.engine.user_id, event_type="input"))
        assert len(inputs) == 100
''', encoding="utf-8")
