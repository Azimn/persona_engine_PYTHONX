from persona_engine.core.conversational_agenda import agenda_from_expression_request
from persona_engine.core.renderer_contract import ExpressionRequest


def request(*, continuity=None, relationship=None):
    return ExpressionRequest(
        ledger_digest={"identity": "Pretorius"},
        resolved_state={
            "user_text": "Hello.",
            "experience_context": {
                "continuity": dict(continuity or {}),
                "relationship": dict(relationship or {}),
            },
        },
        arc_context={},
        evidence=[],
        retrieved_memories=[],
        private_thought_context="",
        decision_payload={"dialogue_act": "respond"},
        expression_constraints={"max_chars": 200},
        deception_obligations=[],
        seed=1,
    )


def test_empty_context_does_not_invent_agenda_or_initiative():
    agenda = agenda_from_expression_request(request())
    assert agenda.active_intention is None
    assert agenda.unresolved_thread is None
    assert agenda.social_goal is None
    assert agenda.initiative_allowed is False
    assert agenda.initiative_pressure == 0.05


def test_active_intention_and_open_loop_create_inspectable_initiative_pressure():
    agenda = agenda_from_expression_request(request(
        continuity={
            "selected_intention": "ask what happened next",
            "open_loop": "unresolved tension from: the abandoned plan",
        },
        relationship={
            "stance": "trusted",
            "familiarity": 0.8,
            "attachment": 0.6,
            "guardedness": 0.1,
            "tension": 0.4,
        },
    ))
    assert agenda.active_intention == "ask what happened next"
    assert agenda.unresolved_thread == "unresolved tension from: the abandoned plan"
    assert agenda.social_goal == "ask what happened next"
    assert agenda.initiative_allowed is True
    assert agenda.initiative_pressure > 0.7
    assert "continuity.selected_intention" in agenda.provenance
    assert "continuity.open_loop" in agenda.provenance


def test_guardedness_suppresses_but_does_not_erase_real_unfinished_business():
    open_context = {
        "selected_intention": "return to the question",
        "open_loop": "unresolved tension from: earlier disagreement",
    }
    low_guard = agenda_from_expression_request(request(
        continuity=open_context,
        relationship={"guardedness": 0.0, "familiarity": 0.7, "attachment": 0.5},
    ))
    high_guard = agenda_from_expression_request(request(
        continuity=open_context,
        relationship={"guardedness": 1.0, "familiarity": 0.7, "attachment": 0.5},
    ))
    assert high_guard.initiative_pressure < low_guard.initiative_pressure
    assert high_guard.unresolved_thread == low_guard.unresolved_thread


def test_shared_symbol_can_support_continuity_without_becoming_a_new_goal():
    agenda = agenda_from_expression_request(request(
        continuity={"shared_symbol": "the red umbrella"},
        relationship={"familiarity": 0.8, "attachment": 0.4, "guardedness": 0.0},
    ))
    assert agenda.shared_symbol == "the red umbrella"
    assert agenda.social_goal == "maintain shared continuity"
    assert agenda.active_intention is None
