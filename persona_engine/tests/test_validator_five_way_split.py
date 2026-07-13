from persona_engine.core.cognition_schemas import DeceptionClaim, NormalizedClaim
from persona_engine.core.deception_ledger import DeceptionLedger
from persona_engine.core.memory import MemoryUnit
from persona_engine.core.renderer import OutputValidator


def test_validator_authorized_deception_passes_within_scope():
    ledger = DeceptionLedger()
    authorization = ledger.authorize("active_lie", "user", "origin", ["origin"], may_fabricate_memory=True)
    assert OutputValidator().check("I remember the origin clearly.", [], authorization=authorization) == []


def test_validator_unauthorized_fabrication_is_distinct():
    authorization = DeceptionLedger().authorize("active_lie", "user", "origin", ["origin"], may_fabricate_memory=True)
    violations = OutputValidator().check("I remember the locked basement.", [], authorization=authorization)
    assert any(v.startswith("unauthorized_fabrication") for v in violations)


def test_validator_accidental_hallucination_uses_existing_false_memory_tag():
    violations = OutputValidator().check("I remember the locked basement.", [])
    assert any(v.startswith("false_memory_claim") for v in violations)


def test_validator_detects_contradiction_of_active_deception_claim():
    ledger = DeceptionLedger([DeceptionClaim(
        claim_id="c1",
        audience="user",
        topic="origin",
        mode="active_lie",
        spoken_claim="claimed research-only origin",
        normalized_claim=NormalizedClaim("origin", "is", "research-only", True),
        concealed_belief_id=None,
        concealed_memory_ids=[],
        consistency_obligation="claimed research-only origin",
        created_at=1.0,
    )])
    violations = OutputValidator().check("About origin, it was not research-only.", [], deception_ledger=ledger)
    assert "deception_contradiction:c1" in violations


def test_validator_allows_truthful_revelation_when_decision_authorizes():
    ledger = DeceptionLedger([DeceptionClaim(
        claim_id="c1",
        audience="user",
        topic="origin",
        mode="active_lie",
        spoken_claim="claimed research-only origin",
        normalized_claim=NormalizedClaim("origin", "is", "research-only", True),
        concealed_belief_id=None,
        concealed_memory_ids=[],
        consistency_obligation="claimed research-only origin",
        created_at=1.0,
    )])
    violations = OutputValidator().check(
        "I need to confess the truth about origin.",
        [MemoryUnit("I need to confess the truth about origin.", created_at=1.0)],
        deception_ledger=ledger,
        decision_payload={"dialogue_act": "confess"},
    )
    assert not any(v.startswith("deception_contradiction") for v in violations)
