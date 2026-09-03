"""The relationship experiment must vary history without replacing the subject."""

from pathlib import Path

from tools.relationship_expression_probe import HISTORIES, SPLITS, capture_request, symptoms


def test_probe_preserves_history_and_resolved_decision_after_restart(tmp_path):
    cartridge = Path(__file__).resolve().parents[1] / "cartridges/pretorius.snp"
    states = {}
    for history in HISTORIES:
        request, reference, _ = capture_request(tmp_path / f"{history}.db", history, "I care about you.", cartridge)
        states[history] = (request, reference)
    assert len({ref["identity"]["entity_uuid"] for _, ref in states.values()}) == 1
    trusted, _ = states["trusted"]
    conflicted, _ = states["conflicted"]
    repaired, _ = states["repaired"]
    assert trusted.resolved_state["experience_context"]["relationship"]["stance"] == "trusted"
    assert conflicted.decision_payload["dialogue_act"] == "deflect"
    assert repaired.resolved_state["experience_context"]["relationship"]["unresolved_conflict"] == 0
    # Repaired trust does not imply that persistent anger vanished. Projection
    # must preserve the engine's withdrawal instead of forcing affectionate prose.
    assert repaired.decision_payload["dialogue_act"] == "withdraw"
    assert "authored_examples" not in repaired.resolved_state["experience_context"]["voice"]


def test_probe_splits_and_symptoms_do_not_relabel_quality_as_validity():
    for key in ("seeds", "prompts"):
        values = [value for split in SPLITS.values() for value in split[key]]
        assert len(values) == len(set(values))
    assert symptoms("I process statements as data points.")["mechanistic_speech"]
    assert symptoms("Keep it factual, please.")["explicit_care_rebuff"]
    assert not any(symptoms("That matters to me.").values())
