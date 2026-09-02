from __future__ import annotations

import pytest

from persona_engine.core.epistemic import (
    EpistemicLedger,
    EpistemicStance,
    EvidenceSource,
)
from persona_engine.core.world_authority import WorldAuthority


def test_testimony_is_evidence_not_automatic_belief_or_world_truth():
    ledger = EpistemicLedger()
    world = WorldAuthority()

    evidence = ledger.record_evidence(
        "bridge.closed",
        "the bridge is closed",
        polarity=1,
        source_class=EvidenceSource.TESTIMONY,
        source_ref="continuity:user_statement:alice:17",
        observed_at=10.0,
        confidence=1.0,
        evidence_id="alice_claim",
    )

    assert evidence.source_class == "testimony"
    assert ledger.current("bridge.closed") is None
    assert world.get_server_truth() == {}
    assert ledger.first_person_status("bridge.closed") == (
        "I do not currently have a settled belief about bridge.closed."
    )


def test_explicit_revision_creates_first_person_tentative_state_with_provenance():
    ledger = EpistemicLedger()
    ledger.record_evidence(
        "bridge.closed",
        "the bridge is closed",
        polarity=1,
        source_class="testimony",
        source_ref="continuity:user_statement:alice:17",
        observed_at=10.0,
        confidence=0.7,
        evidence_id="alice_claim",
    )

    revision = ledger.revise(
        "bridge.closed",
        "the bridge is closed",
        stance=EpistemicStance.TENTATIVE,
        confidence=0.6,
        evidence_ids=["alice_claim"],
        revision_source="validated_semantic_rule",
        reason="I have one uncorroborated testimony source.",
        revised_at=11.0,
    )

    assert revision.before_stance == "unknown"
    assert revision.after_stance == "tentative"
    assert revision.evidence_ids == ("alice_claim",)
    state = ledger.current("bridge.closed")
    assert state is not None
    assert state.evidence_ids == ("alice_claim",)
    assert ledger.first_person_status("bridge.closed") == (
        "I currently lean toward the bridge is closed, but I am not certain."
    )


def test_correction_changes_current_stance_without_rewriting_original_evidence():
    ledger = EpistemicLedger()
    original = ledger.record_evidence(
        "bridge.closed",
        "the bridge is closed",
        polarity=1,
        source_class="testimony",
        source_ref="continuity:user_statement:alice:17",
        observed_at=10.0,
        confidence=0.8,
        evidence_id="alice_original",
    )
    ledger.revise(
        "bridge.closed",
        "the bridge is closed",
        stance="believed",
        confidence=0.7,
        evidence_ids=[original.evidence_id],
        revision_source="validated_semantic_rule",
        reason="initial testimony accepted provisionally",
        revised_at=11.0,
    )

    correction = ledger.record_evidence(
        "bridge.closed",
        "the bridge is closed",
        polarity=-1,
        source_class="testimony",
        source_ref="continuity:user_statement:alice:18",
        observed_at=20.0,
        confidence=1.0,
        evidence_id="alice_correction",
    )
    revision = ledger.revise(
        "bridge.closed",
        "the bridge is closed",
        stance="disbelieved",
        confidence=0.9,
        evidence_ids=[original.evidence_id, correction.evidence_id],
        revision_source="validated_correction",
        reason="Alice explicitly corrected the earlier claim.",
        revised_at=21.0,
    )

    assert revision.before_stance == "believed"
    assert revision.after_stance == "disbelieved"
    assert ledger.evidence["alice_original"] == original
    assert ledger.evidence["alice_original"].polarity == 1
    assert ledger.evidence["alice_correction"].polarity == -1
    assert ledger.first_person_status("bridge.closed") == (
        "I currently do not believe the bridge is closed."
    )


def test_proposition_cannot_cite_evidence_for_another_claim():
    ledger = EpistemicLedger()
    ledger.record_evidence(
        "bridge.closed",
        "the bridge is closed",
        polarity=1,
        source_class="observation",
        source_ref="fact:bridge_sign",
        observed_at=10.0,
        evidence_id="bridge_evidence",
    )

    with pytest.raises(ValueError, match="another key"):
        ledger.revise(
            "weather.raining",
            "it is raining",
            stance="believed",
            confidence=0.9,
            evidence_ids=["bridge_evidence"],
            revision_source="test",
            reason="invalid cross-proposition citation",
        )


def test_epistemic_state_round_trip_preserves_provenance_and_current_stance():
    ledger = EpistemicLedger()
    ledger.record_evidence(
        "orchid.location_known",
        "the location of Project Orchid is known",
        polarity=1,
        source_class="model_inference",
        source_ref="model:qwen3:inference:42",
        observed_at=100.0,
        confidence=0.55,
        claim_valid_from=90.0,
        evidence_id="model_inference_42",
    )
    ledger.revise(
        "orchid.location_known",
        "the location of Project Orchid is known",
        stance="tentative",
        confidence=0.4,
        evidence_ids=["model_inference_42"],
        revision_source="validated_model_proposal",
        reason="model inference retained with uncertainty rather than promoted to truth",
        revised_at=101.0,
    )

    restored = EpistemicLedger.from_state(ledger.to_state())

    assert restored.to_state() == ledger.to_state()
    assert restored.evidence["model_inference_42"].source_class == "model_inference"
    assert restored.current("orchid.location_known").stance == "tentative"


def test_invalid_temporal_evidence_interval_fails_closed():
    ledger = EpistemicLedger()

    with pytest.raises(ValueError, match="must not precede"):
        ledger.record_evidence(
            "shop.open",
            "the shop is open",
            polarity=1,
            source_class="world_authority",
            source_ref="fact:shop_hours",
            observed_at=50.0,
            claim_valid_from=100.0,
            claim_valid_until=90.0,
        )
