from persona_engine.core.consistency import behavioral_contract_from_decision, behavioral_violations


def test_refusal_cannot_be_carried_into_a_resolved_ordinary_response():
    normal=behavioral_contract_from_decision({'dialogue_act':'respond'})
    assert behavioral_violations("I appreciate your kindness, but I can't share information that wasn't meant for me.",normal)==['decision_substitution:respond']
    assert not behavioral_violations("I don't know. Can you clarify?",normal)
    refusing=behavioral_contract_from_decision({'dialogue_act':'decline'})
    assert not behavioral_violations("I can't share that.",refusing)
