from persona_engine.duck.motivation import DriveSystem
from persona_engine.duck.types import CandidateAction, DriveState


def test_drive_deficit_creates_urgency_and_action_value():
    drive = DriveState(name="certainty", target=1.0, level=0.2, urgency=0.0, persistence=1.0, decay_per_tick=0.0)
    system = DriveSystem({"certainty": drive})

    system.step()
    assert drive.urgency == 0.8

    action = CandidateAction(
        action_id="ask",
        action_type="seek_information",
        expected_self_effects={"drive:certainty": 0.3},
    )
    assert system.action_value(action) > 0.0


def test_satisfying_action_closes_motivational_loop():
    drive = DriveState(name="certainty", target=1.0, level=0.2, urgency=0.8, persistence=1.0, decay_per_tick=0.0)
    system = DriveSystem({"certainty": drive})
    before_level = drive.level
    before_urgency = drive.urgency

    applied = system.apply_effects({"drive:certainty": 0.3})

    assert applied == {"certainty": 0.3}
    assert drive.level > before_level
    assert drive.urgency < before_urgency
    assert drive.satisfaction_history == [0.3]
