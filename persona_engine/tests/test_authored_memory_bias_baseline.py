from persona_engine.evaluation.memory_bias_behavior import run_probe


def test_rival_authored_loss_bias_is_not_realized_by_generic_retrieval():
    result = run_probe()
    assert result["character"] == "Rival"
    assert result["retrieval_order"] == ["compliment", "loss"]
    assert result["authored_property_realized"] is False
    assert result["subject_profile_is_retrieval_input"] is False
