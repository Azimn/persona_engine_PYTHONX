"""Typed subject-relative appraisal for Project Ensemble.

This layer separates event description from what the event means to a specific
subject. It does not parse prose and it does not assign an emotion label. Hosts,
sensors, or future semantic annotators provide bounded event features; existing
character state supplies the subject context. The result is a compact causal
appraisal that can later influence attention, memory salience, interpretation,
action selection, disclosure and expression.

The original event remains unchanged. A new appraisal is a subject-owned view of
that event, not a rewritten fact.
"""

from __future__ import annotations

from dataclasses import dataclass


SUBJECT_APPRAISAL_SCHEMA = "ensemble-subject-appraisal-v1"


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


def _clamp_signed(value: float) -> float:
    return max(-1.0, min(1.0, float(value)))


@dataclass(frozen=True)
class SemanticEventAnnotation:
    """Subject-independent bounded features of an already observed event."""

    event_id: str
    event_type: str
    topic: str = ""
    interpersonal: float = 0.0
    goal_bearing: float = 0.0
    identity_bearing: float = 0.0
    boundary_pressure: float = 0.0
    cooperation_signal: float = 0.0
    novelty: float = 0.0
    uncertainty: float = 0.0
    directed_at_subject: bool = True
    tags: tuple[str, ...] = ()

    def __post_init__(self):
        if not self.event_id or not self.event_type:
            raise ValueError("event_id and event_type are required")
        for field_name in (
            "interpersonal",
            "goal_bearing",
            "identity_bearing",
            "boundary_pressure",
            "novelty",
            "uncertainty",
        ):
            value = float(getattr(self, field_name))
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{field_name} must be between 0 and 1")
        if not -1.0 <= float(self.cooperation_signal) <= 1.0:
            raise ValueError("cooperation_signal must be between -1 and 1")

    def to_dict(self) -> dict:
        return {
            "schema": SUBJECT_APPRAISAL_SCHEMA,
            "event_id": self.event_id,
            "event_type": self.event_type,
            "topic": self.topic,
            "interpersonal": self.interpersonal,
            "goal_bearing": self.goal_bearing,
            "identity_bearing": self.identity_bearing,
            "boundary_pressure": self.boundary_pressure,
            "cooperation_signal": self.cooperation_signal,
            "novelty": self.novelty,
            "uncertainty": self.uncertainty,
            "directed_at_subject": self.directed_at_subject,
            "tags": list(self.tags),
        }


@dataclass(frozen=True)
class SubjectAppraisalContext:
    """Current character-owned sensitivities relevant to this event."""

    relationship_importance: float = 0.0
    trust: float = 0.5
    attachment: float = 0.0
    guardedness: float = 0.0
    goal_preference: float = 0.0
    identity_sensitivity: float = 0.5
    perceived_control: float = 0.5

    def __post_init__(self):
        for field_name in (
            "relationship_importance",
            "trust",
            "attachment",
            "guardedness",
            "identity_sensitivity",
            "perceived_control",
        ):
            value = float(getattr(self, field_name))
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{field_name} must be between 0 and 1")
        if not -1.0 <= float(self.goal_preference) <= 1.0:
            raise ValueError("goal_preference must be between -1 and 1")


@dataclass(frozen=True)
class SubjectRelativeAppraisal:
    event_id: str
    goal_relevance: float
    relationship_relevance: float
    identity_relevance: float
    controllability: float
    threat_opportunity: float
    uncertainty: float
    salience: float
    social_meaning: str
    provenance: tuple[str, ...]
    schema: str = SUBJECT_APPRAISAL_SCHEMA

    def to_dict(self) -> dict:
        return {
            "schema": self.schema,
            "event_id": self.event_id,
            "goal_relevance": round(self.goal_relevance, 6),
            "relationship_relevance": round(self.relationship_relevance, 6),
            "identity_relevance": round(self.identity_relevance, 6),
            "controllability": round(self.controllability, 6),
            "threat_opportunity": round(self.threat_opportunity, 6),
            "uncertainty": round(self.uncertainty, 6),
            "salience": round(self.salience, 6),
            "social_meaning": self.social_meaning,
            "provenance": list(self.provenance),
        }


def _social_meaning(event: SemanticEventAnnotation, context: SubjectAppraisalContext, threat_opportunity: float) -> str:
    tags = {str(tag).strip().lower() for tag in event.tags}
    if event.boundary_pressure >= 0.6:
        return "pressure"
    if "apology" in tags or "repair" in tags:
        return "repair" if event.cooperation_signal >= 0.0 else "ambiguous_repair"
    if "betrayal" in tags:
        return "betrayal"
    if "rejection" in tags or "cancellation" in tags:
        if context.goal_preference > 0.25:
            return "relief_or_release"
        if context.relationship_importance >= 0.55:
            return "relational_disruption"
        return "plan_change"
    if event.cooperation_signal >= 0.45:
        return "cooperation"
    if event.cooperation_signal <= -0.45:
        return "opposition"
    if abs(threat_opportunity) < 0.12:
        return "ambiguous" if event.uncertainty >= 0.45 else "neutral"
    return "opportunity" if threat_opportunity > 0 else "threat"


def appraise_subjectively(
    event: SemanticEventAnnotation,
    context: SubjectAppraisalContext,
) -> SubjectRelativeAppraisal:
    """Compute subject-relative meaning without changing the event record."""

    goal_relevance = _clamp01(event.goal_bearing * abs(context.goal_preference))
    relationship_relevance = _clamp01(
        event.interpersonal
        * context.relationship_importance
        * (0.65 + 0.35 * max(context.attachment, context.trust))
    )
    identity_relevance = _clamp01(event.identity_bearing * context.identity_sensitivity)

    controllability = _clamp01(
        context.perceived_control
        * (1.0 - 0.35 * event.uncertainty)
        * (1.0 - 0.20 * event.boundary_pressure)
    )

    goal_direction = event.goal_bearing * context.goal_preference
    social_direction = event.interpersonal * event.cooperation_signal * (
        0.35 + 0.65 * context.relationship_importance
    )
    boundary_direction = -event.boundary_pressure * (
        0.55 + 0.45 * context.guardedness
    )
    identity_direction = -identity_relevance * 0.35 if event.boundary_pressure > 0.0 else 0.0
    threat_opportunity = _clamp_signed(
        0.55 * goal_direction
        + 0.30 * social_direction
        + 0.45 * boundary_direction
        + identity_direction
    )

    salience = _clamp01(max(
        goal_relevance,
        relationship_relevance,
        identity_relevance,
        event.boundary_pressure,
        0.55 * event.novelty + 0.30 * event.uncertainty,
    ))

    provenance = (
        "semantic_event_annotation",
        "subject.relationship",
        "subject.goal_preference",
        "subject.identity_sensitivity",
        "subject.perceived_control",
    )

    return SubjectRelativeAppraisal(
        event_id=event.event_id,
        goal_relevance=goal_relevance,
        relationship_relevance=relationship_relevance,
        identity_relevance=identity_relevance,
        controllability=controllability,
        threat_opportunity=threat_opportunity,
        uncertainty=_clamp01(event.uncertainty),
        salience=salience,
        social_meaning=_social_meaning(event, context, threat_opportunity),
        provenance=provenance,
    )
