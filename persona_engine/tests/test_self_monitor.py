"""Deterministic fallible self-monitor derivation."""

from persona_engine.core.relationship import RelationshipState
from persona_engine.core.self_monitor import SelfMonitor, SelfMonitorProfile
from persona_engine.core.synthesis import SynthesisInfluence
from persona_engine.core.world_authority import WorldAuthority


PRETORIUS = SelfMonitorProfile(
    introspective_accuracy=0.64, bias_awareness=0.46, uncertainty_tolerance=0.38,
    admission_threshold=0.78, concealment_bias=0.82,
    externalization_bias=0.58, correction_bias=0.66,
)
KIKI = SelfMonitorProfile(
    introspective_accuracy=0.70, bias_awareness=0.62, uncertainty_tolerance=0.70,
    admission_threshold=0.48, concealment_bias=0.34,
    externalization_bias=0.20, correction_bias=0.82,
)


def _evaluate(profile=PRETORIUS, seed=1450, **overrides):
    values = {
        "tick": 3, "actual_capacity": 0.72, "fatigue": 0.15,
        "dominant_pressure": 0.15, "identity_threat": 0.0,
        "recent_failure": False, "retrieval_confidences": (0.85, 0.80),
        "influences": (), "stable_seed": seed,
    }
    values.update(overrides)
    return SelfMonitor(profile).evaluate(**values)


def test_high_capacity_low_pressure_estimates_capacity_accurately():
    result = _evaluate(actual_capacity=0.88, dominant_pressure=0.05, fatigue=0.05, seed=1000)
    assert abs(result.perceived_capacity - result.actual_capacity) <= 0.10


def test_low_capacity_high_pressure_can_produce_defensive_overestimate():
    result = _evaluate(
        actual_capacity=0.22, fatigue=0.85, dominant_pressure=0.9,
        identity_threat=1.0, seed=1900,
    )
    assert result.perceived_capacity > result.actual_capacity
    assert result.attributed_cause in {"interlocutor", "circumstances"}


def test_kiki_profile_notices_more_uncertainty_than_pretorius_same_state():
    influences = (
        SynthesisInfluence("relationship:current", "relationship_conflict", "conflict", 0.7),
        SynthesisInfluence("memory:one", "memory", "counterevidence", 0.6, contradictory=True),
    )
    selected = None
    for seed in range(1000):
        pretorius = _evaluate(PRETORIUS, seed, actual_capacity=0.48, dominant_pressure=0.65, influences=influences)
        kiki = _evaluate(KIKI, seed, actual_capacity=0.48, dominant_pressure=0.65, influences=influences)
        if len(kiki.noticed_conflict_ids) > len(pretorius.noticed_conflict_ids):
            selected = (pretorius, kiki)
            break
    assert selected is not None
    assert len(selected[1].noticed_conflict_ids) > len(selected[0].noticed_conflict_ids)


def test_conflict_detection_is_deterministic_but_seed_sensitive():
    influences = tuple(
        SynthesisInfluence(f"open_loop:{index}", "open_loop", "conflict", 0.6)
        for index in range(4)
    )
    first = _evaluate(seed=12, actual_capacity=0.45, influences=influences)
    repeated = _evaluate(seed=12, actual_capacity=0.45, influences=influences)
    alternatives = [_evaluate(seed=seed, actual_capacity=0.45, influences=influences) for seed in range(13, 80)]
    assert first == repeated
    assert any(item.noticed_conflict_ids != first.noticed_conflict_ids for item in alternatives)
    assert all(len(item.noticed_conflict_ids) + len(item.missed_conflict_ids) == 4 for item in alternatives)


def test_low_memory_reliability_proposes_clarification_or_deferral():
    result = _evaluate(retrieval_confidences=(0.1, 0.2), dominant_pressure=0.6)
    kinds = {item.kind for item in result.regulation_candidates}
    assert kinds & {"ask_clarification", "defer_judgment"}


def test_identity_threat_and_concealment_can_propose_defensive_regulation():
    result = _evaluate(
        actual_capacity=0.35, identity_threat=1.0, dominant_pressure=0.8,
        retrieval_confidences=(0.4,), seed=1900,
    )
    kinds = {item.kind for item in result.regulation_candidates}
    assert kinds & {"conceal_uncertainty", "double_down", "withdraw"}


def test_recent_failure_and_correction_bias_proposes_self_correction():
    result = _evaluate(KIKI, recent_failure=True, retrieval_confidences=(0.5,), seed=1000)
    assert "self_correct" in {item.kind for item in result.regulation_candidates}


def test_evaluation_does_not_mutate_world_or_relationship():
    world = WorldAuthority()
    relationship = RelationshipState("user")
    before_world = world.to_list()
    before_relationship = dict(vars(relationship))
    _evaluate(influences=(SynthesisInfluence("relationship:current", "relationship_conflict", "x", 0.5),))
    assert world.to_list() == before_world
    assert vars(relationship) == before_relationship


def test_renderer_summary_excludes_actual_capacity_and_missed_conflicts():
    result = _evaluate(
        actual_capacity=0.2,
        influences=(SynthesisInfluence("open_loop:hidden", "open_loop", "x", 0.5),),
        seed=999,
    )
    summary = result.renderer_summary()
    assert str(result.actual_capacity) not in str(summary)
    assert "open_loop:hidden" not in str(summary)
