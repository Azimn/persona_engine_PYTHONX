from persona_engine.agent import CharacterAgent
from persona_engine.core.epistemic import EpistemicEvidence, EvidenceSource
from persona_engine.core.identity import CoreIdentity


SUBJECT_UUID = "22222222-2222-4222-8222-222222222222"


def identity():
    return CoreIdentity(
        name="InterpretiveSubject",
        core_beliefs=("Evidence and belief are distinct.",),
        temperament="measured",
        entity_uuid=SUBJECT_UUID,
    )


def orchid_evidence(evidence_id="orchid-e1"):
    return EpistemicEvidence(
        evidence_id=evidence_id,
        proposition_key="orchid_location",
        proposition_text="the orchid is in the east room",
        polarity=1,
        source=EvidenceSource.TESTIMONY,
        source_ref="jay",
        observed_at=10.0,
        confidence=0.8,
    )


def establish_orchid_belief(agent):
    agent.record_epistemic_evidence(orchid_evidence())
    agent.revise_belief(
        proposition_key="orchid_location",
        proposition_text="the orchid is in the east room",
        stance="believed",
        confidence=0.72,
        evidence_refs=["orchid-e1"],
        revised_at=20.0,
        reason="accepted testimony",
    )


def epistemic_prior_rows(result):
    return [
        row for row in result["interpretive_belief_trace"]
        if row["distortion"] == "epistemic_prior_read"
    ]


def test_relevant_settled_subject_belief_enters_noncanonical_interpretation(tmp_path):
    agent = CharacterAgent(identity(), user_id="jay", db_path=str(tmp_path / "subject.db"))
    establish_orchid_belief(agent)

    before_world = agent.engine.world_authority.to_list()
    result = agent.say("Where is the orchid?")
    rows = epistemic_prior_rows(result)

    assert len(rows) == 1
    prior = rows[0]
    assert prior["text"] == "I currently believe the orchid is in the east room."
    assert prior["confidence"] == 0.72
    assert prior["canonical"] is False
    assert prior["source_ids"] == ("subject_epistemic:orchid_location",)
    assert agent.engine.world_authority.to_list() == before_world


def test_epistemic_prior_survives_restart_and_interlocutor_change(tmp_path):
    db = str(tmp_path / "subject.db")
    jay = CharacterAgent(identity(), user_id="jay", db_path=db)
    establish_orchid_belief(jay)

    alex = CharacterAgent(identity(), user_id="alex", db_path=db)
    result = alex.say("Do you know where the orchid is?")
    rows = epistemic_prior_rows(result)

    assert alex.writer_status()["subject_uuid"] == SUBJECT_UUID
    assert len(rows) == 1
    assert rows[0]["source_ids"] == ("subject_epistemic:orchid_location",)
    assert rows[0]["text"] == "I currently believe the orchid is in the east room."


def test_unrelated_topic_does_not_activate_subject_epistemic_prior(tmp_path):
    agent = CharacterAgent(identity(), user_id="jay", db_path=str(tmp_path / "subject.db"))
    establish_orchid_belief(agent)

    result = agent.say("What time is dinner?")

    assert epistemic_prior_rows(result) == []


def test_unrevised_testimony_does_not_enter_interpretation(tmp_path):
    agent = CharacterAgent(identity(), user_id="jay", db_path=str(tmp_path / "subject.db"))
    agent.record_epistemic_evidence(orchid_evidence())

    state = agent.epistemic_state("orchid_location")
    result = agent.say("Where is the orchid?")

    assert state["proposition"]["stance"] == "unknown"
    assert epistemic_prior_rows(result) == []
    assert agent.engine.world_authority.to_list() == []
