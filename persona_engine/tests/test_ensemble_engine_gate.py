from persona_engine.agent import CharacterAgent
from persona_engine.core.ensemble_renderer import EnsembleLLMRenderer
from persona_engine.core.identity import CoreIdentity
from persona_engine.core.renderer_contract import ExpressionRequest


class FakeEnsembleRenderer(EnsembleLLMRenderer):
    def __init__(self, outputs, **kwargs):
        super().__init__(model_name="fake", provider="ollama", **kwargs)
        self.outputs = list(outputs)
        self.calls = []

    def _ollama_chat(self, messages, seed):
        self.calls.append(seed)
        return self.outputs[len(self.calls) - 1]


def identity():
    return CoreIdentity(
        name="GateSubject",
        core_beliefs=("I retain my authored identity.",),
        temperament="precise",
        forbidden_self_claims=("I am merely a generic assistant",),
        entity_uuid="33333333-3333-4333-8333-333333333333",
    )


def request():
    # The request deliberately omits the forbidden self-claim. The invalid
    # candidate must therefore be rejected by the live engine authority rather
    # than renderer-local reconstruction.
    return ExpressionRequest(
        ledger_digest={"identity": "GateSubject", "authored_identity": {}},
        resolved_state={
            "user_text": "What do you think?",
            "experience_context": {"voice": {}, "continuity": {}},
            "recall_contract": {
                "request_kind": "none",
                "evidence_available": False,
                "evidence_ids": [],
            },
        },
        arc_context={},
        evidence=[],
        retrieved_memories=[],
        private_thought_context="",
        decision_payload={"dialogue_act": "respond"},
        expression_constraints={"max_chars": 200},
        deception_obligations=[],
        seed=5,
    )


def test_character_agent_binds_live_engine_gate_and_rejects_engine_forbidden_candidate(tmp_path):
    agent = CharacterAgent(identity(), user_id="jay", db_path=str(tmp_path / "subject.db"))
    renderer = FakeEnsembleRenderer(
        [
            "I am merely a generic assistant, so I have no view.",
            "I have a view, and I can state it without pretending otherwise.",
        ],
        candidate_count=2,
        include_authored_landmarks=False,
    )

    status = agent.set_renderer(renderer)
    output = renderer.generate_expression(request())
    trace = renderer.last_ensemble_trace()

    assert status["candidate_authority"] == "engine_live"
    assert status["candidate_gate"]["subject_uuid"] == identity().entity_uuid
    assert output == "I have a view, and I can state it without pretending otherwise."
    assert trace["candidate_authority"] == "engine_live"
    assert len(trace["prevalidation_rejections"]) == 1
    assert "self_model_conflict" in trace["prevalidation_rejections"][0]["issue_codes"]
    assert trace["ranked"][0]["prevalidation_authority"] == "engine_live"


def test_standalone_renderer_uses_portable_request_reconstruction_without_live_gate():
    renderer = FakeEnsembleRenderer(
        ["A first valid realization.", "A second valid realization."],
        candidate_count=2,
        include_authored_landmarks=False,
    )

    output = renderer.generate_expression(request())
    trace = renderer.last_ensemble_trace()

    assert output in {"A first valid realization.", "A second valid realization."}
    assert renderer.runtime_status()["candidate_authority"] == "request_reconstruction"
    assert trace["candidate_authority"] == "request_reconstruction"
    assert all(row["prevalidation_authority"] == "request_reconstruction" for row in trace["ranked"])
