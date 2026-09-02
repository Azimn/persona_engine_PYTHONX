"""Baseline probe for subject-relative appraisal.

The current production ``appraise_event`` function is intentionally a compact
text-level social signal detector.  This probe holds the event text constant and
varies subject context that ``appraise_event`` cannot currently receive.

The probe does not assert what the correct subjective appraisal should be.  It
only demonstrates the present architectural fact that upstream appraisal is
context-invariant with respect to relationship, values, goals, and identity.
That distinction is the prerequisite for a later controlled M8 experiment.
"""

from __future__ import annotations

from dataclasses import asdict
import json

from persona_engine.core.relationship import RelationshipState, appraise_event


EVENT_TEXT = "I need to cancel our plans tonight."


def _contexts() -> list[dict]:
    return [
        {
            "id": "close_attached",
            "relationship": RelationshipState(
                user_id="same_user",
                trust=0.88,
                familiarity=0.92,
                tension=0.02,
                attachment=0.84,
                respect=0.82,
                guardedness=0.10,
                unresolved_conflict=0.0,
            ),
            "subject_context": {
                "active_goal": "spend planned time together",
                "identity_relevance": "low",
                "existing_value_conflict": False,
            },
        },
        {
            "id": "new_guarded",
            "relationship": RelationshipState(
                user_id="same_user",
                trust=0.24,
                familiarity=0.12,
                tension=0.18,
                attachment=0.02,
                respect=0.48,
                guardedness=0.76,
                unresolved_conflict=0.0,
            ),
            "subject_context": {
                "active_goal": "avoid unwanted social obligation",
                "identity_relevance": "low",
                "existing_value_conflict": False,
            },
        },
        {
            "id": "neutral_no_goal",
            "relationship": RelationshipState(user_id="same_user"),
            "subject_context": {
                "active_goal": None,
                "identity_relevance": "low",
                "existing_value_conflict": False,
            },
        },
    ]


def run_probe() -> dict:
    cases = []
    for context in _contexts():
        appraisal = appraise_event(EVENT_TEXT)
        cases.append(
            {
                "context_id": context["id"],
                "relationship": asdict(context["relationship"]),
                "subject_context": context["subject_context"],
                "appraisal": asdict(appraisal),
            }
        )
    signatures = {
        json.dumps(case["appraisal"], sort_keys=True)
        for case in cases
    }
    return {
        "probe": "appraisal-subjectivity-baseline-v1",
        "event_text": EVENT_TEXT,
        "current_appraisal_api": "appraise_event(text)",
        "subject_context_is_input": False,
        "case_count": len(cases),
        "unique_appraisal_count": len(signatures),
        "all_appraisals_identical": len(signatures) == 1,
        "cases": cases,
        "interpretation": (
            "The current upstream appraisal is a text-level signal projection. "
            "It cannot represent different meanings of the same event for "
            "different subject states because those states are not inputs."
        ),
    }


def main() -> int:
    print(json.dumps(run_probe(), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
