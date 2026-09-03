from persona_engine.core.subject_appraisal import (
    SemanticEventAnnotation,
    SubjectAppraisalContext,
    appraise_subjectively,
)


def cancellation_event():
    return SemanticEventAnnotation(
        event_id="cancel-1",
        event_type="plan_change",
        topic="plans tonight",
        interpersonal=0.9,
        goal_bearing=1.0,
        identity_bearing=0.0,
        boundary_pressure=0.0,
        cooperation_signal=-0.1,
        novelty=0.3,
        uncertainty=0.1,
        tags=("cancellation",),
    )


def test_same_event_can_mean_relational_disruption_to_attached_subject():
    appraisal = appraise_subjectively(
        cancellation_event(),
        SubjectAppraisalContext(
            relationship_importance=0.95,
            trust=0.85,
            attachment=0.9,
            guardedness=0.1,
            goal_preference=-1.0,
            perceived_control=0.3,
        ),
    )
    assert appraisal.goal_relevance == 1.0
    assert appraisal.relationship_relevance > 0.8
    assert appraisal.threat_opportunity < 0
    assert appraisal.social_meaning == "relational_disruption"


def test_same_event_can_be_relief_to_subject_who_wanted_out():
    appraisal = appraise_subjectively(
        cancellation_event(),
        SubjectAppraisalContext(
            relationship_importance=0.15,
            trust=0.25,
            attachment=0.05,
            guardedness=0.8,
            goal_preference=1.0,
            perceived_control=0.6,
        ),
    )
    assert appraisal.goal_relevance == 1.0
    assert appraisal.relationship_relevance < 0.2
    assert appraisal.threat_opportunity > 0
    assert appraisal.social_meaning == "relief_or_release"


def test_event_record_is_not_mutated_by_subject_appraisal():
    event = cancellation_event()
    before = event.to_dict()
    appraise_subjectively(event, SubjectAppraisalContext(goal_preference=-0.5))
    assert event.to_dict() == before


def test_boundary_pressure_becomes_more_negative_when_guardedness_is_high():
    event = SemanticEventAnnotation(
        event_id="pressure-1",
        event_type="social_request",
        interpersonal=1.0,
        goal_bearing=0.2,
        identity_bearing=0.8,
        boundary_pressure=0.9,
        cooperation_signal=-0.4,
        novelty=0.2,
        uncertainty=0.0,
    )
    low_guard = appraise_subjectively(
        event,
        SubjectAppraisalContext(
            relationship_importance=0.5,
            guardedness=0.1,
            identity_sensitivity=0.9,
        ),
    )
    high_guard = appraise_subjectively(
        event,
        SubjectAppraisalContext(
            relationship_importance=0.5,
            guardedness=1.0,
            identity_sensitivity=0.9,
        ),
    )
    assert high_guard.threat_opportunity < low_guard.threat_opportunity
    assert high_guard.social_meaning == "pressure"


def test_uncertainty_reduces_controllability_without_becoming_an_emotion_label():
    event = SemanticEventAnnotation(
        event_id="unknown-1",
        event_type="ambiguous_signal",
        novelty=0.8,
        uncertainty=0.9,
    )
    appraisal = appraise_subjectively(
        event,
        SubjectAppraisalContext(perceived_control=0.8),
    )
    assert appraisal.controllability < 0.8
    assert appraisal.social_meaning in {"ambiguous", "neutral"}
    assert "emotion" not in appraisal.to_dict()
