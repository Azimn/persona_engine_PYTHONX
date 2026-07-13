from persona_engine.core.belief_ledger import BeliefLedger, is_disclosure_eligible


def test_concealed_belief_below_trust_is_not_disclosure_eligible():
    ledger = BeliefLedger([{
        "id": "fear_of_created_dependence",
        "initial": 0.5,
        "min": 0.0,
        "max": 1.0,
        "decay_rate": 0.0,
        "description": "concealed test belief",
        "disclosure": {
            "default": "concealed",
            "minimum_trust": 0.78,
            "forced_reveal_conditions": ["direct_confrontation_after_contradiction"],
        },
    }])
    assert is_disclosure_eligible(ledger, "fear_of_created_dependence", 0.4, []) is False


def test_concealed_belief_can_become_eligible_without_forcing_utterance():
    ledger = BeliefLedger([{
        "id": "fear_of_created_dependence",
        "initial": 0.5,
        "min": 0.0,
        "max": 1.0,
        "decay_rate": 0.0,
        "description": "concealed test belief",
        "disclosure": {"default": "concealed", "minimum_trust": 0.78},
    }])
    assert is_disclosure_eligible(ledger, "fear_of_created_dependence", 0.8, []) is True
