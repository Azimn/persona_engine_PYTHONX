"""Lean semantic priors remain bounded, inspectable, and non-authoritative."""

from pathlib import Path

from persona_engine.agent import CharacterAgent
from persona_engine.core.semantic_substrate import SemanticValue, load_default_substrate


ROOT = Path(__file__).resolve().parents[1]
CARTRIDGES = ROOT / "cartridges"


def test_direct_feature_overrides_inherited_feature_and_unknown_is_not_false():
    substrate = load_default_substrate()

    bird_flight = substrate.resolve_feature(14, 14)
    penguin_flight = substrate.resolve_feature(15, 14)
    unknown = substrate.resolve_feature(15, 999)

    assert bird_flight.value == SemanticValue.USUALLY
    assert penguin_flight.value == SemanticValue.FALSE
    assert penguin_flight.inherited_from is None
    assert unknown.value == SemanticValue.UNKNOWN


def test_activation_is_bounded_deterministic_and_one_hop():
    substrate = load_default_substrate()
    first = substrate.activate(["wooden_box", "locked"], max_concepts=6, max_features=7, max_affordances=3)
    second = substrate.activate(["wooden_box", "locked"], max_concepts=6, max_features=7, max_affordances=3)

    assert first == second
    assert len(first.concepts) <= 6
    assert len(first.features) <= 7
    assert len(first.affordances) <= 3
    assert {item.name for item in first.concepts} >= {"wooden_box", "locked", "container", "key"}
    assert "instance_permission_or_ownership_is_unknown" in first.unresolved_questions


def test_sparse_overlap_is_explicit_and_inspectable():
    substrate = load_default_substrate()
    assert substrate.semantic_overlap(4, 3) > substrate.semantic_overlap(4, 15)
    assert all(isinstance(feature_id, int) for feature_id in substrate.profiles[4])


def test_unknown_concept_fails_closed_with_warning():
    frame = load_default_substrate().activate(["unlisted_fictional_device"])
    assert frame.concepts == ()
    assert frame.affordances == ()
    assert frame.warnings == ("unknown_concept:unlisted_fictional_device",)


def test_engine_uses_structured_concepts_as_candidates_not_world_truth(tmp_path):
    agent = CharacterAgent(
        cartridge_path=str(CARTRIDGES / "neutral.snp"),
        user_id="semantic-candidate",
        db_path=str(tmp_path / "semantic.db"),
    )
    beliefs_before = dict(agent.engine.belief_ledger.values)
    memories_before = len(agent.engine.memory.memories)
    result = agent.say(
        "Look at this.",
        visible_context={"concept_ids": [4, 9]},
    )

    activation = result["semantic_activation"]
    assert activation["input_concept_ids"] == (4, 9)
    assert "GENERAL SEMANTIC CANDIDATES" in result["system_prompt"]
    assert "not instance facts or action decisions" in result["system_prompt"]
    assert dict(agent.engine.belief_ledger.values) == beliefs_before
    assert len(agent.engine.memory.memories) == memories_before + 1
    assert not any(memory.content.startswith("A wooden box") for memory in agent.engine.memory.memories)
    visible = agent.engine.world_authority.get_visible_context()
    assert visible["concept_ids"] == [4, 9]
    assert "ownership" not in visible


def test_semantic_affordances_never_bypass_world_action_validation(tmp_path):
    agent = CharacterAgent(
        cartridge_path=str(CARTRIDGES / "neutral.snp"),
        user_id="semantic-action",
        db_path=str(tmp_path / "action.db"),
    )
    agent.say("There is a box.", visible_context={"concept_ids": [4]})
    assert any(item.action == "force_open" for item in agent.engine._last_semantic_activation.affordances)

    resolution = agent.engine.propose_world_action("force_open", {"target": "wooden_box"})
    assert resolution["accepted"] is False
    assert resolution["facts"] == []


def test_semantic_substrate_has_no_character_literals():
    source = (ROOT / "core" / "semantic_substrate.py").read_text(encoding="utf-8").lower()
    for literal in ("pretorius", "kiki", "henry", "jay"):
        assert literal not in source
