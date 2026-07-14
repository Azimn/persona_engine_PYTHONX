from persona_engine.simulator import _fact_leak_warnings


def test_fact_leak_scan_ignores_sentence_initial_stop_words():
    warnings = _fact_leak_warnings("That phrase is uncertain.", {"user_input": "Fine."}, {"system_prompt": ""})
    assert warnings == []


def test_fact_leak_scan_does_not_treat_sentence_initial_capitalization_as_a_name():
    warnings = _fact_leak_warnings("Now the room is quiet.", {"visible_context": {"room_sound": "quiet"}}, {"system_prompt": ""})
    assert warnings == []


def test_fact_leak_scan_still_flags_unknown_concrete_objects():
    warnings = _fact_leak_warnings("I heard footsteps.", {"user_input": "What was that?"}, {"system_prompt": ""})
    assert any("footsteps" in warning for warning in warnings)
