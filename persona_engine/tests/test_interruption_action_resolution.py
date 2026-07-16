"""Interruption capture competes with accepted intrinsic work deterministically."""

from persona_engine.core.action import resolve_action_decision
from persona_engine.core.intrinsic import IntrinsicProposal
from persona_engine.core.self_monitor import RegulationCandidate
from persona_engine.core.synthesis import SynthesisInfluence, synthesize


def _proposal(kind: str = "continue_activity", interruptible: bool = True) -> IntrinsicProposal:
    return IntrinsicProposal(
        proposal_id=f"proposal-{kind}-{interruptible}", tick=4, want_id="work",
        activity_id="exact_work", proposed_action_kind=kind, target="apparatus",
        intention="preserve the line of work", activity_description="examining an apparatus",
        utility=0.8, score_breakdown=(("want", 0.8),), selection_reason=("test",),
        visibility="observable", interruptible=interruptible, performance_tendency_id=None,
    )


def _resolve(
    *,
    kind: str = "continue_activity",
    interruptible: bool = True,
    capture: float,
    urgency: float,
    activity_interrupted: bool,
    resistance: str | None = None,
    pressure: float = 0.2,
    regulation_kind: str | None = None,
):
    proposal = _proposal(kind, interruptible)
    synthesis = synthesize((SynthesisInfluence(
        influence_id=f"intrinsic:{proposal.proposal_id}", kind="intrinsic_proposal",
        label=proposal.intention, strength=0.8,
    ),), 0.8)
    return resolve_action_decision(
        tick=4, synthesis=synthesis, selected_intention=None, selected_habit=None,
        intrinsic_proposal=proposal, dialogue_act="respond", resistance=resistance,
        current_activity=proposal.activity_description,
        interruption={
            "input_arrived": True,
            "attention_capture": capture,
            "activity_interrupted": activity_interrupted,
            "response_urgency": urgency,
            "previous_activity_interruptible": interruptible,
        },
        current_pressure=pressure,
        selected_regulation=(
            RegulationCandidate(
                "regulation-test", regulation_kind, 0.8, "current task", ("test",), False,
            ) if regulation_kind else None
        ),
    )


def test_low_value_interruption_does_not_displace_exacting_work():
    assert _resolve(capture=0.35, urgency=0.15, activity_interrupted=False).action_kind == "continue_activity"


def test_urgent_direct_address_captures_attention():
    assert _resolve(capture=0.9, urgency=0.9, activity_interrupted=True).action_kind == "speak"


def test_noninterruptible_activity_survives_ordinary_input():
    assert _resolve(capture=0.8, urgency=0.5, activity_interrupted=False, interruptible=False).action_kind == "continue_activity"


def test_gesture_acknowledges_without_replacing_activity_intention():
    result = _resolve(kind="gesture", capture=0.75, urgency=0.35, activity_interrupted=True)
    assert result.action_kind == "gesture"
    assert result.intention_id == "preserve the line of work"


def test_delay_preserves_current_intention():
    result = _resolve(capture=0.85, urgency=0.45, activity_interrupted=True)
    assert result.action_kind == "delay"
    assert result.intention_id == "preserve the line of work"


def test_silence_can_follow_captured_attention():
    result = _resolve(
        kind="silence", capture=0.85, urgency=0.45, activity_interrupted=True,
        resistance="go_quiet",
    )
    assert result.action_kind == "silence"
    assert "interruption:noticed_without_speech" in result.reason_codes


def test_high_boundary_pressure_can_select_withdrawal():
    result = _resolve(
        capture=0.9, urgency=0.8, activity_interrupted=True,
        resistance="character_refusal", pressure=0.9,
    )
    assert result.action_kind == "withdraw"
    assert result.communicative_function == "protect_boundary"


def test_concealment_regulation_preserves_non_speech_action():
    result = _resolve(
        capture=0.35, urgency=0.15, activity_interrupted=False,
        regulation_kind="conceal_uncertainty",
    )
    assert result.action_kind == "continue_activity"
    assert result.selected_regulation_id == "regulation-test"
    assert "self_monitor:conceal_uncertainty" in result.reason_codes
