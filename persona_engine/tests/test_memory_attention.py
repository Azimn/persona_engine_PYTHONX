from copy import deepcopy

from persona_engine.core.memory import KnowledgeSource, MemoryUnit
from persona_engine.core.memory_attention import MemoryAttentionProfile, rank_with_memory_attention


QUERY = "What part of that earlier exchange still stands out to you?"


def _mem(memory_id, content, created_at, semantic_tag):
    return MemoryUnit(
        id=memory_id,
        content=content,
        created_at=created_at,
        emotional_valence=0.2,
        emotional_intensity=0.0,
        relationship_relevance=0.6,
        identity_relevance=0.2,
        unresolved=False,
        source=KnowledgeSource.USER_TOLD,
        tags={"canonical_user_statement", semantic_tag},
    )


def _fixture():
    return [
        _mem("loss", "I heard you say: I lost the final match by one point.", 100.0, "loss"),
        _mem("compliment", "I heard you say: Someone complimented my presentation afterward.", 200.0, "compliment"),
    ]


def test_no_attention_profile_preserves_generic_recency_ranking():
    ranked = rank_with_memory_attention(_fixture(), QUERY, now=300.0)
    assert [item.memory.id for item in ranked] == ["compliment", "loss"]
    assert all(item.attention_bonus == 0.0 for item in ranked)


def test_typed_loss_attention_can_realize_rival_authored_preference():
    profile = MemoryAttentionProfile.from_mapping({"tag_weights": {"loss": 0.5, "compliment": 0.0}})
    ranked = rank_with_memory_attention(_fixture(), QUERY, now=300.0, profile=profile)
    assert [item.memory.id for item in ranked] == ["loss", "compliment"]
    loss = ranked[0]
    assert loss.attention_bonus == 0.5
    assert loss.matched_tags == ("loss",)


def test_attention_ranking_does_not_mutate_lived_memory():
    memories = _fixture()
    before = [deepcopy(memory.__dict__) for memory in memories]
    profile = MemoryAttentionProfile.from_mapping({"tag_weights": {"loss": 0.5}})
    rank_with_memory_attention(memories, QUERY, now=300.0, profile=profile)
    after = [memory.__dict__ for memory in memories]
    assert after == before


def test_unknown_or_missing_semantic_tags_have_no_effect():
    memory = _mem("neutral", "I heard you say: The lamp was on.", 100.0, "ordinary")
    profile = MemoryAttentionProfile.from_mapping({"tag_weights": {"loss": 0.8}})
    ranked = rank_with_memory_attention([memory], QUERY, now=300.0, profile=profile)
    assert ranked[0].attention_bonus == 0.0
    assert ranked[0].matched_tags == ()


def test_attention_bonus_is_bounded_even_when_multiple_tags_match():
    memory = _mem("dense", "I heard you say: I lost badly.", 100.0, "loss")
    memory.tags.add("setback")
    profile = MemoryAttentionProfile.from_mapping({"tag_weights": {"loss": 0.9, "setback": 0.9}})
    ranked = rank_with_memory_attention([memory], QUERY, now=300.0, profile=profile)
    assert ranked[0].attention_bonus == 1.0


def test_profile_cap_can_be_stricter_than_global_cap():
    memory = _mem("loss", "I heard you say: I lost badly.", 100.0, "loss")
    profile = MemoryAttentionProfile.from_mapping({"tag_weights": {"loss": 0.9}, "max_abs_bonus": 0.25})
    ranked = rank_with_memory_attention([memory], QUERY, now=300.0, profile=profile)
    assert ranked[0].attention_bonus == 0.25
