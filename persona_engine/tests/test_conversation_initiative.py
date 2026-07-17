"""Grounded initiative remains bounded, deterministic, and synthesis-owned."""

from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

import pytest

from persona_engine.agent import CharacterAgent
from persona_engine.core.conversation_initiative import (
    INITIATIVE_MOVES,
    assess_conversation_initiative,
    validate_initiative_realization,
)
from persona_engine.core.intrinsic import IntrinsicProposal
from persona_engine.core.memory import MemoryRetrieval, MemoryUnit
from persona_engine.playtest.host import DevelopmentalPlaytestHost
from persona_engine.playtest.scenario import load_scenario


ROOT = Path(__file__).resolve().parents[1]


def _proposal() -> IntrinsicProposal:
    return IntrinsicProposal(
        proposal_id="intrinsic_work", tick=4, want_id="work", activity_id="inspect",
        proposed_action_kind="observe", target="apparatus", intention="inspect the anomaly",
        activity_description="inspecting an anomalous result", utility=1.2,
        score_breakdown=(("want", 0.8),), selection_reason=("test",),
        visibility="observable", interruptible=True, performance_tendency_id=None,
    )


def test_empty_sources_explain_that_nothing_was_eligible():
    result = assess_conversation_initiative(
        actor_id=1, turn=2, obligation="acknowledge", initiative_budget=0.8,
    )

    assert result.proposal is None
    assert result.outcome == "no_source_eligible"
    assert result.eligible_sources == ()


def test_intrinsic_activity_can_propose_but_not_select_a_move():
    first = assess_conversation_initiative(
        actor_id=1, turn=4, obligation="acknowledge", initiative_budget=0.8,
        intrinsic_proposal=_proposal(),
    )
    repeated = assess_conversation_initiative(
        actor_id=1, turn=5, obligation="acknowledge", initiative_budget=0.8,
        intrinsic_proposal=_proposal(), recent_source_ids=("intrinsic_work",),
    )

    assert first.outcome == "proposal_available"
    assert first.proposal is not None
    assert first.proposal.proposed_move == "speculate"
    assert repeated.outcome == "no_source_eligible"


def test_direct_answer_obligation_inhibits_unsolicited_extension():
    result = assess_conversation_initiative(
        actor_id=1, turn=4, obligation="answer", initiative_budget=0.8,
        intrinsic_proposal=_proposal(),
    )

    assert result.proposal is not None
    assert result.outcome == "proposal_inhibited"


def test_accelerated_crossplay_advances_intrinsic_state_and_reports_silence_causes(tmp_path):
    scenario = replace(
        load_scenario(ROOT / "playtest_scenarios" / "kiki_pretorius_crossplay_30_days.yaml"),
        total_days=3,
    )
    host = DevelopmentalPlaytestHost(
        scenario=scenario, cartridges_dir=ROOT / "cartridges", db_dir=tmp_path,
    )

    result = host.run()

    assert all(agent.engine.intrinsic_state.want_levels for agent in host.agents.values())
    assert all(agent.engine._last_intrinsic_proposal is not None for agent in host.agents.values())
    assert sum(result.metrics["initiative_outcome_counts"].values()) == len(result.diagnostics)
    assert sum(result.metrics["interaction_outcome_counts"].values()) == len(result.diagnostics)
    assert sum(
        count
        for outcomes in result.metrics["initiative_source_outcome_counts"].values()
        for count in outcomes.values()
    ) == len(result.diagnostics)
    assert set(result.metrics["silence_reason_counts"]) <= {
        "nothing_eligible", "proposal_below_threshold", "proposal_inhibited",
        "proposal_denied", "selected_silence", "noninitiative_silence",
    }
    eligibility = result.metrics["initiative_memory_eligibility_by_participant"]
    assert eligibility
    assert all(item["total_memories_in_store"] > 0 for item in eligibility.values())
    assert all(item["pre_topic_autobiographical_count"] == 0 for item in eligibility.values())
    assert all(item["final_eligible_count"] == 0 for item in eligibility.values())


def test_simulated_day_is_bounded_instead_of_becoming_daylong_exertion(tmp_path):
    agent = CharacterAgent(
        cartridge_path=str(ROOT / "cartridges" / "pretorius.snp"),
        user_id="simulated_time", db_path=str(tmp_path / "time.db"),
    )
    initial_fatigue = agent.engine.body.fatigue

    summary = agent.advance_time(86400.0, now=1_800_000_000.0)

    assert summary["tide_steps"] == 4
    assert agent.engine.body.fatigue - initial_fatigue < 0.25
    assert agent.engine.intrinsic_state.want_levels


def test_sparse_world_changes_create_grounded_proposals_without_forcing_every_turn(tmp_path):
    scenario = load_scenario(
        ROOT / "playtest_scenarios" / "initiative_world_changes_7_days.yaml"
    )
    result = DevelopmentalPlaytestHost(
        scenario=scenario, cartridges_dir=ROOT / "cartridges", db_dir=tmp_path,
    ).run()

    world_change_turns = [
        item for item in result.diagnostics
        if item.get("initiative_source_kind") == "world_change"
    ]
    assert world_change_turns
    assert any(
        item.get("initiative_outcome") in {
            "proposal_selected", "proposal_denied_by_synthesis", "proposal_inhibited",
        }
        for item in world_change_turns
    )
    assert len(world_change_turns) < len(result.diagnostics)


def test_seeded_obviously_relevant_memory_clears_crossplay_eligibility(tmp_path):
    agent = CharacterAgent(
        cartridge_path=str(ROOT / "cartridges" / "pretorius.snp"),
        user_id="memory_eligibility", db_path=str(tmp_path / "memory.db"),
    )
    agent.engine.memory.add(MemoryUnit(
        id="apparatus_anomaly_episode",
        content="I observed that the apparatus anomaly stabilized after calibration.",
        created_at=1_700_000_000.0,
        salience=0.95,
        emotional_intensity=0.45,
        tags={"autobiographical", "apparatus", "anomaly"},
    ))

    result = agent.say(
        "The apparatus anomaly may have stabilized after calibration.",
        event_time=1_700_000_100.0,
    )
    eligibility = result["initiative_memory_eligibility"]

    assert eligibility["total_memories_in_store"] >= 1
    assert eligibility["pre_topic_autobiographical_count"] >= 1
    assert eligibility["relevance_pass_count"] >= 1
    assert eligibility["final_eligible_count"] >= 1
    assert "apparatus_anomaly_episode" in eligibility["relevance_pass_ids"]


def test_maximum_initiative_sources_remain_inside_authored_action_fence():
    memory = MemoryUnit(
        id="memory_max", content="I remember the apparatus result.", created_at=1.0,
        salience=1.0, emotional_intensity=1.0, tags={"autobiographical"},
    )
    assessment = assess_conversation_initiative(
        actor_id=1, turn=9, obligation="acknowledge", initiative_budget=1.0,
        contextual_memories=(MemoryRetrieval(memory, 1.0, {"active_topic_score": 1.0}),),
        open_loop=SimpleNamespace(
            topic_key="unfinished", topic="unfinished", urgency=1.0,
            emotional_charge=1.0,
        ),
        intrinsic_proposal=_proposal(),
        relationship_expectations=(SimpleNamespace(
            key="returns_to_open_loops", value="strongly_expected", confidence=1.0,
        ),),
        world_changes=({
            "event_id": "world_max", "event_type": "discovery",
            "action": "observed_change", "category": "rare_chaos",
        },),
    )

    assert len(assessment.eligible_sources) == 5
    assert assessment.proposal is not None
    assert assessment.proposal.proposed_move in INITIATIVE_MOVES
    assert set(assessment.proposal.to_dict()) == {
        "schema_version", "proposal_id", "actor_id", "turn", "source_kind",
        "source_id", "topic_key", "proposed_move", "strength", "reason_codes",
    }
    candidate = SimpleNamespace(
        initiative_proposal_id=assessment.proposal.proposal_id,
        move="honor_obligation",
        extension_move=assessment.proposal.proposed_move,
    )
    for action_kind in (
        "speak", "gesture", "continue_activity", "delay", "silence", "withdraw",
    ):
        validate_initiative_realization(
            proposal=assessment.proposal,
            conversation_candidate=candidate,
            action_decision=SimpleNamespace(
                action_kind=action_kind, target="current interlocutor",
            ),
        )
    for escaped_kind in ("world_action", "observe"):
        with pytest.raises(ValueError, match="escaped bounded action space"):
            validate_initiative_realization(
                proposal=assessment.proposal,
                conversation_candidate=candidate,
                action_decision=SimpleNamespace(
                    action_kind=escaped_kind, target="invented scene",
                ),
            )

    exhausted = assess_conversation_initiative(
        actor_id=1, turn=10, obligation="acknowledge", initiative_budget=1.0,
        contextual_memories=(MemoryRetrieval(memory, 1.0, {"active_topic_score": 1.0}),),
        open_loop=SimpleNamespace(
            topic_key="unfinished", topic="unfinished", urgency=1.0,
            emotional_charge=1.0,
        ),
        intrinsic_proposal=_proposal(),
        relationship_expectations=(SimpleNamespace(
            key="returns_to_open_loops", value="strongly_expected", confidence=1.0,
        ),),
        world_changes=({
            "event_id": "world_max", "event_type": "discovery",
            "action": "observed_change", "category": "rare_chaos",
        },),
        recent_source_ids=(
            "memory_max", "unfinished", "intrinsic_work",
            "returns_to_open_loops", "world_max",
        ),
    )
    assert exhausted.proposal is None
    assert exhausted.outcome == "no_source_eligible"
