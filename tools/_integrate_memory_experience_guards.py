#!/usr/bin/env python3
"""One-time exact integration for memory experience guards."""

from pathlib import Path


def replace_once(path: str, old: str, new: str) -> None:
    p = Path(path)
    text = p.read_text(encoding="utf-8")
    if old not in text:
        raise SystemExit(f"expected patch anchor missing in {path}: {old[:120]!r}")
    if text.count(old) != 1:
        raise SystemExit(f"patch anchor occurs {text.count(old)} times in {path}; refusing fuzzy edit")
    p.write_text(text.replace(old, new, 1), encoding="utf-8")


replace_once(
    "persona_engine/core/engine.py",
    "        unresolved = [m for m in top_mems if m.unresolved]\n",
    "        # A memory may truthfully record that an episode was unresolved at the\n"
    "        # time without implying that the relationship is still unresolved now.\n"
    "        # Reflection must therefore combine historical evidence with current\n"
    "        # relationship state, matching the conduct gate's repair semantics.\n"
    "        relationship_unresolved_now = self.relationship.unresolved_conflict > 0.0\n"
    "        unresolved = [m for m in top_mems if m.unresolved] if relationship_unresolved_now else []\n",
)

replace_once(
    "persona_engine/core/offline_template_renderer.py",
    "from .offline_dialogue import dialogue_for\n",
    "from .offline_dialogue import dialogue_for\nfrom .cold_biography import grounded_context_match\n",
)

replace_once(
    "persona_engine/core/offline_template_renderer.py",
    "        identity = str(digest.get(\"identity\", \"\")).strip()\n"
    "        memory_units = list(request.retrieved_memories or [])\n"
    "        memories = [str(getattr(memory, \"content\", memory)) for memory in memory_units]\n"
    "        contextual_memory = any(\n"
    "            \"contextual_readthrough\" in set(getattr(memory, \"tags\", set()) or set())\n"
    "            for memory in memory_units\n"
    "        )\n",
    "        identity = str(digest.get(\"identity\", \"\")).strip()\n"
    "        user_text = str(resolved.get(\"user_text\", \"\"))\n"
    "        memory_units = list(request.retrieved_memories or [])\n"
    "        memories = [str(getattr(memory, \"content\", memory)) for memory in memory_units]\n"
    "        contextual_memory = any(\n"
    "            \"contextual_readthrough\" in set(getattr(memory, \"tags\", set()) or set())\n"
    "            for memory in memory_units\n"
    "        )\n"
    "        grounded_live_memory = any(\n"
    "            \"cold_biography\" not in set(getattr(memory, \"tags\", set()) or set())\n"
    "            and grounded_context_match(user_text, str(getattr(memory, \"content\", memory)))\n"
    "            for memory in memory_units\n"
    "        )\n",
)

replace_once(
    "persona_engine/core/offline_template_renderer.py",
    "            \"user_text\": str(resolved.get(\"user_text\", \"\")),\n"
    "            \"system_text\": str(resolved.get(\"system_prompt\", \"\")),\n"
    "            \"decision_payload\": dict(request.decision_payload or {}),\n"
    "            \"memories\": memories,\n"
    "            \"contextual_memory\": contextual_memory,\n",
    "            \"user_text\": user_text,\n"
    "            \"system_text\": str(resolved.get(\"system_prompt\", \"\")),\n"
    "            \"decision_payload\": dict(request.decision_payload or {}),\n"
    "            \"memories\": memories,\n"
    "            \"contextual_memory\": contextual_memory,\n"
    "            \"grounded_live_memory\": grounded_live_memory,\n",
)

replace_once(
    "persona_engine/core/offline_template_renderer.py",
    "        if group == \"question\" and bool(context.get(\"contextual_memory\")):\n"
    "            # Grounded cold continuation is already authorized evidence. Expose\n"
    "            # it rather than hiding successful recollection behind a generic reply.\n"
    "            group = \"memory\"\n",
    "        if group == \"question\" and (\n"
    "            bool(context.get(\"contextual_memory\")) or bool(context.get(\"grounded_live_memory\"))\n"
    "        ):\n"
    "            # Grounded live or cold evidence is already available to expression.\n"
    "            # Expose it rather than making the minimum renderer appear amnesiac.\n"
    "            # The topical grounding gate prevents unrelated resident memories\n"
    "            # from being converted into apparent recollection.\n"
    "            group = \"memory\"\n",
)

replace_once(
    "tools/memory_consumer_role_probe.py",
    "        hot_after_projection = [_memory_summary(memory) for memory in selected]\n",
    "        projected_count = len(selected)\n        hot_after_projection = [_memory_summary(memory) for memory in selected]\n",
)
replace_once(
    "tools/memory_consumer_role_probe.py",
    "            \"resident_after_projection\": len(selected),\n",
    "            \"resident_after_projection\": projected_count,\n",
)

Path("persona_engine/tests/test_memory_experience_guards.py").write_text(r'''"""Experience-level guards for memory and repair semantics."""

import os
import tempfile
import time
from pathlib import Path

from persona_engine.agent import CharacterAgent

ROOT = Path(__file__).resolve().parents[1]
CART = ROOT / "cartridges" / "pretorius.snp"


def test_repaired_history_does_not_reenter_reflection_as_current_unresolved_conflict():
    with tempfile.TemporaryDirectory() as directory:
        agent = CharacterAgent(
            cartridge_path=str(CART),
            user_id="repair-reflection",
            db_path=os.path.join(directory, "state.db"),
        )
        agent.say("You lied to me. This is your fault.")
        agent.say("You lied to me again. This is your fault too.")
        assert agent.engine.relationship.unresolved_conflict == 0.2
        agent.say("I was wrong. I'm sorry.")
        assert agent.engine.relationship.unresolved_conflict == 0.0
        assert sum(1 for memory in agent.engine.memory.memories if memory.unresolved) >= 2
        assert "reflective_pattern" not in agent.engine.ledger.earned_traits

        agent.engine.energy = 0.1
        agent.engine.last_reflection_time = 0.0
        agent.engine._trigger_reflection(time.time() + 1_000.0)

        assert "reflective_pattern" not in agent.engine.ledger.earned_traits


def test_grounded_live_memory_is_visible_in_ordinary_followup_question():
    with tempfile.TemporaryDirectory() as directory:
        agent = CharacterAgent(
            cartridge_path=str(CART),
            user_id="live-grounding",
            db_path=os.path.join(directory, "state.db"),
        )
        agent.say("The workshop door is saffron today.")
        result = agent.say("What about the workshop door?")

        assert any("saffron" in item["content"].lower() for item in result["retrieved_memory_trace"])
        assert "saffron" in result["response"].lower()


def test_unrelated_live_memory_is_not_rendered_as_recollection():
    with tempfile.TemporaryDirectory() as directory:
        agent = CharacterAgent(
            cartridge_path=str(CART),
            user_id="live-negative",
            db_path=os.path.join(directory, "state.db"),
        )
        agent.say("The workshop door is saffron today.")
        result = agent.say("What about the harbor telescope?")

        assert "saffron" not in result["response"].lower()


def test_anchorless_question_does_not_turn_background_memory_into_recollection():
    with tempfile.TemporaryDirectory() as directory:
        agent = CharacterAgent(
            cartridge_path=str(CART),
            user_id="live-anchorless",
            db_path=os.path.join(directory, "state.db"),
        )
        agent.say("The workshop door is saffron today.")
        result = agent.say("What about it?")

        assert "saffron" not in result["response"].lower()
''', encoding="utf-8")
