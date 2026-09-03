from persona_engine.agent import CharacterAgent
from persona_engine.core.identity import CoreIdentity
from tools.ensemble_relationship_probe import (
    CapturingEnsembleRenderer,
    _invalid_reason,
)


class FakeModelRenderer(CapturingEnsembleRenderer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.model_seeds = []

    def _ollama_chat(self, messages, seed):
        self.model_seeds.append(seed)
        return "I can answer in my own words without changing who I am."


def identity():
    return CoreIdentity(
        name="ProbeSubject",
        core_beliefs=("I preserve my own judgment.",),
        temperament="measured",
        entity_uuid="44444444-4444-4444-8444-444444444444",
    )


def test_probe_renderer_uses_forced_seed_and_live_agent_authority(tmp_path):
    agent = CharacterAgent(identity(), user_id="probe", db_path=str(tmp_path / "probe.db"))
    renderer = FakeModelRenderer(
        model_name="fake-model",
        provider="ollama",
        candidate_count=1,
        include_authored_landmarks=False,
        forced_seed=1201,
    )
    agent.set_renderer(renderer)

    result = agent.say("What do you think?")
    status = renderer.runtime_status()
    trace = renderer.last_ensemble_trace()

    assert result["response"] == "I can answer in my own words without changing who I am."
    assert renderer.requests
    assert renderer.requests[0].seed == 1201
    assert renderer.model_seeds == [1201]
    assert status["actual_provider"] == "ollama"
    assert status["candidate_authority"] == "engine_live"
    assert trace["candidate_authority"] == "engine_live"
    assert trace["ranked"][0]["prevalidation_authority"] == "engine_live"


def test_probe_invalid_reason_fails_closed_on_collection_integrity():
    good_status = {"actual_provider": "ollama", "candidate_authority": "engine_live"}
    good_trace = {"candidate_authority": "engine_live"}
    good_result = {"expression_delivery": {"validation_fallback": False}}

    assert _invalid_reason(good_status, good_trace, good_result, True) is None
    assert _invalid_reason({**good_status, "actual_provider": "offline"}, good_trace, good_result, True) == "actual_provider_not_ollama"
    assert _invalid_reason({**good_status, "candidate_authority": "request_reconstruction"}, good_trace, good_result, True) == "candidate_authority_not_engine_live"
    assert _invalid_reason(good_status, {"candidate_authority": "request_reconstruction"}, good_result, True) == "trace_candidate_authority_not_engine_live"
    assert _invalid_reason(good_status, good_trace, {"expression_delivery": {"validation_fallback": True}}, True) == "engine_validation_fallback"
    assert _invalid_reason(good_status, good_trace, good_result, False) == "semantic_projection_mismatch"
