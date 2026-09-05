from persona_engine.duck.metacognition import CalibrationMonitor


def test_prediction_error_changes_calibration_report():
    monitor = CalibrationMonitor()
    monitor.observe(world_error=0.0, self_error=0.0, simulation_confidence=0.8)
    good = monitor.report()
    monitor.observe(world_error=0.8, self_error=0.6, simulation_confidence=0.9)
    mixed = monitor.report()

    assert good["world_prediction_confidence"] == 1.0
    assert mixed["world_prediction_confidence"] < good["world_prediction_confidence"]
    assert mixed["uncertainty"] > good["uncertainty"]
    assert mixed["observations"] == 2
