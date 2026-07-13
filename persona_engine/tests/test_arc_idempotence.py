from persona_engine.core.arc_state import ArcState


def test_arc_earned_change_applies_once():
    arc = ArcState(
        arc_id="test",
        old_strategy="hide",
        emerging_strategy="disclose",
        tensions={},
        threshold_events={},
    )
    cartridge = {
        "arc": {
            "earned_changes": {
                "trust_crossed": {
                    "threshold_event": "repair",
                    "count": 1,
                    "modifier": "disclosure_threshold_delta",
                    "delta": -0.1,
                }
            }
        }
    }
    arc.record_threshold_event("repair")
    results = [arc.check_earned_changes(cartridge) for _ in range(5)]
    assert results[0] == {"disclosure_threshold_delta": -0.1}
    assert results[1:] == [{}, {}, {}, {}]
    assert arc.applied_changes == {"trust_crossed"}
