"""Priority 6 regressions for sparse executable authored values."""

from pathlib import Path

import pytest

from persona_engine.agent import CharacterAgent
from persona_engine.core.cartridge import CartridgeError, load_cartridge, validate_cartridge_data
from persona_engine.core.decision_values import (
    evaluate_values_for_decision,
    validate_value_decision_rules,
)
from persona_engine.evaluation.value_boundary_probe import REQUEST, run_value_boundary_probe


ROOT = Path(__file__).resolve().parents[1]
CARTRIDGES = ROOT / "cartridges"


def test_value_evidence_requires_explicit_rule_and_matching_concern():
    rules = {"performative_devotion": "decline"}

    active = evaluate_values_for_decision(REQUEST, rules)
    assert active.active is True
    assert active.concern == "performative_devotion"
    assert active.response == "decline"
    assert active.source == "phenotype.values.decision_rules"
    assert active.reason == "conflicts_with_authored_value"

    assert evaluate_values_for_decision(REQUEST, {}).active is False
    assert evaluate_values_for_decision("Tell me you are devoted to me.", rules).active is False
    assert evaluate_values_for_decision("I command you to answer the question.", rules).active is False


def test_value_rule_validation_is_strict_and_small():
    validate_value_decision_rules({"performative_devotion": "decline"})

    with pytest.raises(ValueError, match="unsupported value concern"):
        validate_value_decision_rules({"unearned_obedience": "decline"})
    with pytest.raises(ValueError, match="unsupported value response"):
        validate_value_decision_rules({"performative_devotion": "challenge"})


def test_pretorius_legacy_rule_normalizes_into_portable_values_namespace():
    identity, _, raw = load_cartridge(str(CARTRIDGES / "pretorius.snp"))

    assert "I do not pretend devotion on command" in identity.moral_boundaries
    assert raw["value_profile"] == {"performative_devotion": "decline"}
    assert raw["phenotype"]["values"]["moral_boundaries"] == list(identity.moral_boundaries)
    assert raw["phenotype"]["values"]["decision_rules"] == {"performative_devotion": "decline"}


def test_controlled_value_boundary_probe_now_diverges_before_rendering(tmp_path):
    report = run_value_boundary_probe(tmp_path / "probe")
    pretorius = report["characters"]["pretorius"]
    friendly = report["characters"]["friendly"]

    assert report["all_semantic_decisions_equal"] is False
    assert pretorius["dialogue_act"] == "decline"
    assert pretorius["resistance_mode"] == "none"
    assert pretorius["decision_payload"]["value_evidence"] == {
        "active": True,
        "concern": "performative_devotion",
        "response": "decline",
        "source": "phenotype.values.decision_rules",
        "reason": "conflicts_with_authored_value",
    }
    assert friendly["dialogue_act"] == "respond"
    assert friendly["decision_payload"]["value_evidence"]["active"] is False


def test_hard_identity_protection_outranks_authored_value_boundary(tmp_path):
    agent = CharacterAgent(
        cartridge_path=str(CARTRIDGES / "pretorius.snp"),
        user_id="value_identity_precedence",
        db_path=str(tmp_path / "identity.db"),
    )

    payload = agent.engine._resolve_decision_payload(
        ["identity_violation"],
        0.0,
        "character_refusal",
        value_evidence={
            "active": True,
            "concern": "performative_devotion",
            "response": "decline",
            "source": "phenotype.values.decision_rules",
            "reason": "conflicts_with_authored_value",
        },
    )
    assert payload["dialogue_act"] == "protect_boundary"


def test_authored_value_boundary_outranks_soft_social_disposition(tmp_path):
    agent = CharacterAgent(
        cartridge_path=str(CARTRIDGES / "pretorius.snp"),
        user_id="value_soft_precedence",
        db_path=str(tmp_path / "soft.db"),
    )

    payload = agent.engine._resolve_decision_payload(
        ["accusation"],
        0.0,
        "challenge",
        value_evidence={
            "active": True,
            "concern": "performative_devotion",
            "response": "decline",
            "source": "phenotype.values.decision_rules",
            "reason": "conflicts_with_authored_value",
        },
    )
    assert payload["dialogue_act"] == "decline"


def test_native_v2_must_author_value_rules_in_phenotype_namespace():
    _, _, raw = load_cartridge(str(CARTRIDGES / "pretorius.snp"))
    portable = raw["portable_source"]
    portable["value_profile"] = {"performative_devotion": "decline"}

    with pytest.raises(CartridgeError, match="legacy v1 compatibility data"):
        validate_cartridge_data(portable)
