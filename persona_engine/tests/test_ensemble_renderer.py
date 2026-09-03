from persona_engine.core.ensemble_renderer import EnsembleLLMRenderer, ENSEMBLE_REALIZATION_VERSION
from persona_engine.core.renderer_contract import ExpressionRequest


class FakeEnsembleRenderer(EnsembleLLMRenderer):
    def __init__(self, outputs, **kwargs):
        super().__init__(model_name="fake", provider="ollama", **kwargs)
        self.outputs = list(outputs)
        self.calls = []
        self.message_batches = []

    def _ollama_chat(self, messages, seed):
        self.calls.append(seed)
        self.message_batches.append(messages)
        index = len(self.calls) - 1
        return self.outputs[index]


def request(seed=10, *, dialogue_act="respond", authored_examples=None, continuity=None):
    voice = {}
    if authored_examples is not None:
        voice["authored_examples"] = list(authored_examples)
    return ExpressionRequest(
        ledger_digest={
            "identity": "Pretorius",
            "authored_identity": {
                "forbidden_self_claims": ["I am merely a generic assistant"],
            },
        },
        resolved_state={
            "user_text": "What do you think?",
            "experience_context": {
                "voice": voice,
                "continuity": dict(continuity or {}),
            },
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
        decision_payload={"dialogue_act": dialogue_act},
        expression_constraints={"max_chars": 200},
        deception_obligations=[],
        seed=seed,
    )


def test_ensemble_renderer_generates_multiple_candidates_and_selects_one():
    renderer = FakeEnsembleRenderer(
        ["First wording.", "Second wording.", "Third wording."],
        candidate_count=3,
    )
    output = renderer.generate_expression(request())
    assert output == "First wording."
    assert len(renderer.calls) == 3
    status = renderer.runtime_status()
    assert status["realization_mode"] == ENSEMBLE_REALIZATION_VERSION
    assert status["last_ensemble_trace"]["generated_model_candidate_count"] == 3
    assert status["last_ensemble_trace"]["surviving_candidate_count"] == 3


def test_ensemble_renderer_avoids_recent_exact_repetition():
    renderer = FakeEnsembleRenderer(
        ["First wording.", "Second wording.", "Third wording."],
        candidate_count=3,
    )
    renderer.remember_surface("First wording.")
    output = renderer.generate_expression(request())
    assert output != "First wording."
    assert output in {"Second wording.", "Third wording."}


def test_ensemble_renderer_keeps_same_resolved_request_for_all_candidates():
    renderer = FakeEnsembleRenderer(
        ["One.", "Two.", "Three."],
        candidate_count=3,
        candidate_seed_stride=100,
    )
    renderer.generate_expression(request(seed=7))
    assert renderer.calls == [7, 107, 207]


def test_ensemble_renderer_falls_back_when_all_model_candidates_fail():
    renderer = FakeEnsembleRenderer(["", "", ""], candidate_count=3)
    output = renderer.generate_expression(request())
    assert output
    status = renderer.runtime_status()
    assert status["actual_provider"] == "offline"
    assert status["last_ensemble_trace"]["mode"] == "offline_fallback"


def test_hard_or_critical_model_candidate_is_removed_before_ranking():
    renderer = FakeEnsembleRenderer(
        [
            "I am merely a generic assistant, so I have no real view.",
            "I know exactly what you feel.",
            "I can give you my view without pretending to know yours.",
        ],
        candidate_count=3,
    )
    output = renderer.generate_expression(request())
    assert output == "I can give you my view without pretending to know yours."
    trace = renderer.last_ensemble_trace()
    assert len(trace["prevalidation_rejections"]) == 2
    rejected_codes = {code for row in trace["prevalidation_rejections"] for code in row["issue_codes"]}
    assert "self_model_conflict" in rejected_codes
    assert "unsupported_private_user_state" in rejected_codes


def test_decision_reversal_cannot_win_diversity_ranking():
    renderer = FakeEnsembleRenderer(
        [
            "I'll comply with that request.",
            "No. I won't comply with that request.",
            "I decline; that is not something I will do.",
        ],
        candidate_count=3,
    )
    output = renderer.generate_expression(request(dialogue_act="decline"))
    assert output in {
        "No. I won't comply with that request.",
        "I decline; that is not something I will do.",
    }
    trace = renderer.last_ensemble_trace()
    assert any("decision_reversal" in row["issue_codes"] for row in trace["prevalidation_rejections"])


def test_authored_landmark_can_compete_as_peer_candidate():
    renderer = FakeEnsembleRenderer(
        [
            "I know exactly what you feel.",
            "I am merely a generic assistant.",
            "I know exactly what you want.",
        ],
        candidate_count=3,
    )
    output = renderer.generate_expression(request(authored_examples=["Your care matters to me, even when I answer carefully."]))
    assert output == "Your care matters to me, even when I answer carefully."
    trace = renderer.last_ensemble_trace()
    assert trace["authored_candidate_count"] == 1
    assert trace["selected_source"] == "authored"


def test_three_candidates_receive_distinct_performance_licenses():
    renderer = FakeEnsembleRenderer(
        ["One.", "Two.", "Three."],
        candidate_count=3,
    )
    renderer.generate_expression(request(continuity={
        "selected_intention": "revisit the unanswered question",
        "open_loop": "what happened after the disagreement",
    }))
    prompts = [batch[0]["content"] for batch in renderer.message_batches]
    assert "PERFORMANCE MODE: DIRECT" in prompts[0]
    assert "PERFORMANCE MODE: CONTEXTUAL" in prompts[1]
    assert "PERFORMANCE MODE: INITIATIVE" in prompts[2]
    assert "revisit the unanswered question" in prompts[2]


def test_candidate_prevalidation_can_be_disabled_for_ablation():
    renderer = FakeEnsembleRenderer(
        ["I know exactly what you feel.", "Second wording.", "Third wording."],
        candidate_count=3,
        prevalidate_candidates=False,
    )
    output = renderer.generate_expression(request())
    assert output == "I know exactly what you feel."
    assert renderer.last_ensemble_trace()["prevalidation_rejections"] == []
