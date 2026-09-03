import pytest

from persona_engine.core.epistemic import (
    EpistemicEvidence,
    EpistemicLedger,
    EpistemicStance,
    EvidenceSource,
)


def evidence(evidence_id, *, key="orchid_location", text="the orchid is in the east room", polarity=1, source=EvidenceSource.TESTIMONY):
    return EpistemicEvidence(
        evidence_id=evidence_id,
        proposition_key=key,
        proposition_text=text,
        polarity=polarity,
        source=source,
        source_ref="jay",
        observed_at=1.0,
        confidence=0.8,
    )


def test_testimony_is_evidence_not_automatic_belief():
    ledger = EpistemicLedger()
    ledger.record_evidence(evidence("e1"))
    state = ledger.current("orchid_location", "the orchid is in the east room")
    assert state.stance == EpistemicStance.UNKNOWN
    assert ledger.first_person_status("orchid_location").startswith("I do not currently have a settled belief")


def test_explicit_tentative_revision_cites_same_proposition_evidence():
    ledger = EpistemicLedger()
    ledger.record_evidence(evidence("e1"))
    revision = ledger.revise(
        proposition_key="orchid_location",
        proposition_text="the orchid is in the east room",
        stance=EpistemicStance.TENTATIVE,
        confidence=0.55,
        evidence_refs=["e1"],
        revised_at=2.0,
        source="subject_revision",
        reason="single testimony",
    )
    assert revision.before_stance == EpistemicStance.UNKNOWN
    assert revision.after_stance == EpistemicStance.TENTATIVE
    assert ledger.current("orchid_location").evidence_refs == ("e1",)


def test_correction_flips_current_stance_without_rewriting_original_evidence():
    ledger = EpistemicLedger()
    original = evidence("e1")
    correction = evidence("e2", polarity=-1, source=EvidenceSource.OBSERVATION)
    ledger.record_evidence(original)
    ledger.revise(
        proposition_key="orchid_location",
        proposition_text=original.proposition_text,
        stance=EpistemicStance.BELIEVED,
        confidence=0.7,
        evidence_refs=["e1"],
        revised_at=2.0,
        source="subject_revision",
        reason="accepted testimony",
    )
    ledger.record_evidence(correction)
    ledger.revise(
        proposition_key="orchid_location",
        proposition_text=original.proposition_text,
        stance=EpistemicStance.DISBELIEVED,
        confidence=0.9,
        evidence_refs=["e1", "e2"],
        revised_at=3.0,
        source="subject_revision",
        reason="direct contradictory observation",
    )
    assert ledger.evidence["e1"] == original
    assert ledger.current("orchid_location").stance == EpistemicStance.DISBELIEVED
    assert len(ledger.revisions) == 2


def test_cross_proposition_evidence_fails_closed():
    ledger = EpistemicLedger()
    ledger.record_evidence(evidence("e1", key="weather", text="it is raining"))
    with pytest.raises(ValueError):
        ledger.revise(
            proposition_key="orchid_location",
            proposition_text="the orchid is in the east room",
            stance=EpistemicStance.BELIEVED,
            confidence=0.7,
            evidence_refs=["e1"],
            revised_at=2.0,
            source="subject_revision",
            reason="invalid cross proposition evidence",
        )


def test_model_inference_preserves_source_and_does_not_become_fact():
    ledger = EpistemicLedger()
    item = evidence("e1", source=EvidenceSource.MODEL_INFERENCE)
    ledger.record_evidence(item)
    ledger.revise(
        proposition_key=item.proposition_key,
        proposition_text=item.proposition_text,
        stance=EpistemicStance.TENTATIVE,
        confidence=0.35,
        evidence_refs=["e1"],
        revised_at=2.0,
        source="validated_model_inference",
        reason="plausible interpretation only",
    )
    restored = EpistemicLedger.from_dict(ledger.to_dict())
    assert restored.evidence["e1"].source == EvidenceSource.MODEL_INFERENCE
    assert restored.current(item.proposition_key).stance == EpistemicStance.TENTATIVE
    assert restored.current(item.proposition_key).confidence == 0.35


def test_non_unknown_revision_requires_evidence():
    ledger = EpistemicLedger()
    with pytest.raises(ValueError):
        ledger.revise(
            proposition_key="weather",
            proposition_text="it is raining",
            stance=EpistemicStance.BELIEVED,
            confidence=0.8,
            evidence_refs=[],
            revised_at=2.0,
            source="subject_revision",
            reason="unsupported",
        )


def test_invalid_temporal_interval_fails_closed():
    with pytest.raises(ValueError):
        EpistemicEvidence(
            evidence_id="e1",
            proposition_key="door_state",
            proposition_text="the door is open",
            polarity=1,
            source=EvidenceSource.OBSERVATION,
            source_ref="vision",
            observed_at=5.0,
            confidence=1.0,
            claim_valid_from=10.0,
            claim_valid_until=9.0,
        )
