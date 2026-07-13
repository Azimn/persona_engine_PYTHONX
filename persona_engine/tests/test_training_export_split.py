from persona_engine.core.finetune.export_training_data import expression_record, private_cognition_record


def test_training_export_keeps_private_cognition_and_expression_tasks_split():
    private = private_cognition_record({}, {}, {}, [], [], "...", {"applied_pressure_deltas": {}})
    expression = expression_record({}, {}, {}, [], [], "...", {"dialogue_act": "respond"}, {}, [], "hello")
    assert private["task"] == "private_cognition"
    assert "decision_payload" not in private["inputs"]
    assert expression["task"] == "expression"
    assert expression["inputs"]["decision_payload"]["dialogue_act"] == "respond"


def test_training_export_keeps_rejected_effects_out_of_default_target():
    private = private_cognition_record(
        {},
        {},
        {},
        [],
        [],
        "...",
        accepted_cognitive_effects={"applied_pressure_deltas": {"fear": 0.1}},
        proposed_cognitive_effects={"pressure_deltas": {"unknown": 9.0}},
        rejection_reasons={"unknown": "unknown pressure name"},
    )
    assert private["targets"]["cognitive_effects"] == {"applied_pressure_deltas": {"fear": 0.1}}
    assert "unknown" not in str(private["targets"]["cognitive_effects"])
    assert private["diagnostics"]["proposed_cognitive_effects"]["pressure_deltas"]["unknown"] == 9.0
