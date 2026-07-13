from persona_engine.core.habit import HabitTracker


def test_private_cognition_evidence_weights_less_than_expressed_actions():
    private = HabitTracker()
    action = HabitTracker()
    for _ in range(10):
        private.add_evidence("guarded_probe", "probe", "ask indirectly", "private_cognition")
    for _ in range(3):
        action.add_evidence("guarded_probe", "probe", "ask indirectly", "expressed_action")
    assert private.habits["guarded_probe"].strength < action.habits["guarded_probe"].strength
    assert len(private.habits["guarded_probe"].evidence_log) == 10
