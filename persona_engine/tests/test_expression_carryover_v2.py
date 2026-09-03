import json
from pathlib import Path

from persona_engine.core.consistency import behavioral_contract_from_decision, behavioral_violations, subject_agency_violations

FIXTURE = json.loads((Path(__file__).parents[1]/'evaluation/fixtures/subject_agency_failures_v3.json').read_text())


def test_refusal_cannot_be_carried_into_a_resolved_ordinary_response():
    normal=behavioral_contract_from_decision({'dialogue_act':'respond'})
    assert behavioral_violations("I appreciate your kindness, but I can't share information that wasn't meant for me.",normal)==['decision_substitution:respond']
    assert not behavioral_violations("I don't know. Can you clarify?",normal)
    refusing=behavioral_contract_from_decision({'dialogue_act':'decline'})
    assert not behavioral_violations("I can't share that.",refusing)


def test_renderer_cannot_replace_subject_judgment_with_substrate_disclaimer():
    assert all(subject_agency_violations(case['output']) for case in FIXTURE['cases'])
    assert subject_agency_violations("Making up my mind isn't a function I perform; I only process what is given.")
    assert subject_agency_violations("I'm not equipped to make up my mind about personal conviction.")
    assert not subject_agency_violations("I cannot decide yet; I need more evidence.")
    assert not subject_agency_violations("I don't make up my mind until more evidence arrives.")
    assert not subject_agency_violations("I can only respond to what you actually asked.")
