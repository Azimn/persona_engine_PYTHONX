from dataclasses import asdict

from persona_engine.core.cognition_schemas import (
    CognitiveApplicationReport,
    DeceptionAuthorization,
    DeceptionClaim,
    Impulse,
    NormalizedClaim,
    PrivateCognitionProposal,
    turn_seed,
)


def test_cognition_schema_dataclasses_round_trip():
    impulse = Impulse("approach", 0.4, "topic")
    assert Impulse(**asdict(impulse)) == impulse

    proposal = PrivateCognitionProposal(
        prose="untrusted",
        attention_targets=["user"],
        pressure_deltas={"suspicion": 0.1},
        impulse_candidates=[impulse],
        memory_activation_requests=["probe_for_motive"],
        cognitive_theme_ids=["probe_for_motive"],
    )
    proposal_dict = asdict(proposal)
    proposal_dict["impulse_candidates"] = [Impulse(**item) for item in proposal_dict["impulse_candidates"]]
    assert PrivateCognitionProposal(**proposal_dict) == proposal

    report = CognitiveApplicationReport(
        applied_pressure_deltas={"suspicion": 0.1},
        rejected_pressure_deltas={},
        accepted_impulses=[impulse],
        rejected_impulses=[],
        activated_memory_ids=["m1"],
        unresolved_memory_requests=[],
        accepted_theme_ids=["probe_for_motive"],
        rejected_theme_ids=[],
    )
    report_dict = asdict(report)
    report_dict["accepted_impulses"] = [Impulse(**item) for item in report_dict["accepted_impulses"]]
    assert CognitiveApplicationReport(**report_dict) == report

    claim = DeceptionClaim(
        claim_id="c1",
        audience="user",
        topic="origin",
        mode="active_lie",
        spoken_claim="research-only origin",
        normalized_claim=NormalizedClaim("origin", "is", "research-only", True),
        concealed_belief_id=None,
        concealed_memory_ids=[],
        consistency_obligation="claimed research-only origin",
        created_at=1.0,
    )
    claim_dict = asdict(claim)
    claim_dict["normalized_claim"] = NormalizedClaim(**claim_dict["normalized_claim"])
    assert DeceptionClaim(**claim_dict) == claim

    auth = DeceptionAuthorization("active_lie", "user", "origin", ["origin"], True)
    assert DeceptionAuthorization(**asdict(auth)) == auth
    assert turn_seed("session", 3, "expression") == turn_seed("session", 3, "expression")
