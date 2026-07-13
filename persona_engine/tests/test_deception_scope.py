from persona_engine.core.cognition_schemas import DeceptionClaim, NormalizedClaim
from persona_engine.core.deception_ledger import DeceptionLedger
from persona_engine.core.renderer import OutputValidator


def test_active_lie_scope_does_not_authorize_other_topic_memory_claim():
    ledger = DeceptionLedger()
    authorization = ledger.authorize(
        "active_lie",
        audience="user",
        topic="origin",
        scope=["origin", "research-only origin"],
        may_fabricate_memory=True,
    )
    violations = OutputValidator().check(
        "I remember the hidden laboratory under the city.",
        retrieved_memories=[],
        authorization=authorization,
    )
    assert any(v.startswith("unauthorized_fabrication") for v in violations)


def test_deception_ledger_records_and_filters_claims():
    ledger = DeceptionLedger()
    claim = DeceptionClaim(
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
    )
    ledger.record(claim)
    assert ledger.claims_for("user", "origin") == [claim]
    assert ledger.claims_for("user", "other") == []
