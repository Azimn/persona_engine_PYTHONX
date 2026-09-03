from persona_engine.agent import CharacterAgent
from persona_engine.core.epistemic import (
    EpistemicEvidence,
    EpistemicStance,
    EvidenceSource,
)
from persona_engine.core.identity import CoreIdentity


SUBJECT_UUID = "11111111-1111-4111-8111-111111111111"


def identity():
    return CoreIdentity(
        name="EpistemicSubject",
        core_beliefs=("Evidence and belief are distinct.",),
        temperament="measured",
        entity_uuid=SUBJECT_UUID,
    )


def evidence(
    evidence_id: str,
    *,
    polarity: int = 1,
    source: EvidenceSource = EvidenceSource.TESTIMONY,
    source_ref: str = "jay",
):
    return EpistemicEvidence(
        evidence_id=evidence_id,
        proposition_key="orchid_location",
        proposition_text="the orchid is in the east room",
        polarity=polarity,
        source=source,
        source_ref=source_ref,
        observed_at=10.0,
        confidence=0.8,
    )


def test_epistemic_evidence_and_belief_survive_restart(tmp_path):
    db = str(tmp_path / "subject.db")
    agent = CharacterAgent(identity(), user_id="jay", db_path=db)

    agent.record_epistemic_evidence(evidence("e1"))
    unknown = agent.epistemic_state("orchid_location")
    assert unknown["proposition"]["stance"] == "unknown"

    agent.revise_belief(
        proposition_key="orchid_location",
        proposition_text="the orchid is in the east room",
        stance=EpistemicStance.TENTATIVE,
        confidence=0.55,
        evidence_refs=["e1"],
        revised_at=20.0,
        reason="single testimony",
    )

    restarted = CharacterAgent(identity(), user_id="jay", db_path=db)
    state = restarted.epistemic_state("orchid_location")

    assert state["proposition"]["stance"] == "tentative"
    assert state["proposition"]["confidence"] == 0.55
    assert state["proposition"]["evidence_refs"] == ["e1"]
    assert state["evidence"][0]["source"] == "testimony"


def test_epistemic_state_follows_subject_across_interlocutor_streams(tmp_path):
    db = str(tmp_path / "subject.db")
    jay_stream = CharacterAgent(identity(), user_id="jay", db_path=db, host_id="local")
    jay_stream.record_epistemic_evidence(evidence("e1"))
    jay_stream.revise_belief(
        proposition_key="orchid_location",
        proposition_text="the orchid is in the east room",
        stance="believed",
        confidence=0.72,
        evidence_refs=["e1"],
        revised_at=20.0,
        reason="accepted testimony",
    )

    alex_stream = CharacterAgent(identity(), user_id="alex", db_path=db, host_id="local")
    state = alex_stream.epistemic_state("orchid_location")

    assert jay_stream.writer_status()["subject_uuid"] == SUBJECT_UUID
    assert alex_stream.writer_status()["subject_uuid"] == SUBJECT_UUID
    assert state["proposition"]["stance"] == "believed"
    assert state["proposition"]["confidence"] == 0.72
    assert [item["evidence_id"] for item in state["evidence"]] == ["e1"]


def test_correction_changes_current_belief_without_erasing_prior_evidence_across_streams(tmp_path):
    db = str(tmp_path / "subject.db")
    first = CharacterAgent(identity(), user_id="jay", db_path=db)
    first.record_epistemic_evidence(evidence("e1"))
    first.revise_belief(
        proposition_key="orchid_location",
        proposition_text="the orchid is in the east room",
        stance="believed",
        confidence=0.70,
        evidence_refs=["e1"],
        revised_at=20.0,
        reason="accepted testimony",
    )

    second = CharacterAgent(identity(), user_id="alex", db_path=db)
    second.record_epistemic_evidence(
        evidence(
            "e2",
            polarity=-1,
            source=EvidenceSource.OBSERVATION,
            source_ref="vision:doorway",
        )
    )
    second.revise_belief(
        proposition_key="orchid_location",
        proposition_text="the orchid is in the east room",
        stance="disbelieved",
        confidence=0.91,
        evidence_refs=["e1", "e2"],
        revised_at=30.0,
        reason="direct contradictory observation",
    )

    restarted_first = CharacterAgent(identity(), user_id="jay", db_path=db)
    state = restarted_first.epistemic_state("orchid_location")

    assert state["proposition"]["stance"] == "disbelieved"
    assert state["proposition"]["evidence_refs"] == ["e1", "e2"]
    assert [item["evidence_id"] for item in state["evidence"]] == ["e1", "e2"]
    assert state["evidence"][0]["polarity"] == 1
    assert state["evidence"][1]["polarity"] == -1


def test_recording_testimony_or_model_inference_does_not_mutate_world_authority(tmp_path):
    db = str(tmp_path / "subject.db")
    agent = CharacterAgent(identity(), user_id="jay", db_path=db)
    before = agent.engine.world_authority.to_list()

    agent.record_epistemic_evidence(evidence("e1", source=EvidenceSource.TESTIMONY))
    agent.record_epistemic_evidence(
        evidence(
            "e2",
            source=EvidenceSource.MODEL_INFERENCE,
            source_ref="renderer:qwen",
        )
    )

    after = agent.engine.world_authority.to_list()
    state = agent.epistemic_state("orchid_location")

    assert after == before
    assert state["proposition"]["stance"] == "unknown"
    assert [item["source"] for item in state["evidence"]] == ["testimony", "model_inference"]
