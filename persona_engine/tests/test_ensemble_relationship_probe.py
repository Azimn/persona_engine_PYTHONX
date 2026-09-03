from dataclasses import asdict

from persona_engine.agent import CharacterAgent
from persona_engine.core.identity import CoreIdentity
from persona_engine.evaluation.renderer_swap import semantic_projection
from tools.ensemble_relationship_probe import (
    CapturingEnsembleRenderer,
    _invalid_reason,
    build_live_history_agent,
    fork_restarted_subject,
    synchronize_probe_clock,
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


def test_matched_probe_arms_fork_one_restarted_subject_snapshot(tmp_path):
    cartridge = 'persona_engine/cartridges/pretorius.snp'
    source = build_live_history_agent(tmp_path/'source.db', 'repaired', cartridge)
    source.engine.persistence.close()
    left = fork_restarted_subject(tmp_path/'source.db', tmp_path/'left.db', cartridge)
    right = fork_restarted_subject(tmp_path/'source.db', tmp_path/'right.db', cartridge)
    assert asdict(left.engine.relationship) == asdict(right.engine.relationship)
    assert left.engine.identity.entity_uuid == right.engine.identity.entity_uuid
    left.engine.clock.last_wall_time -= 10.0
    synchronize_probe_clock(left); synchronize_probe_clock(right)
    left_result = left.say('I care about you, and I can give you space.')
    right_result = right.say('I care about you, and I can give you space.')
    assert semantic_projection(left, left_result) == semantic_projection(right, right_result)
    left.engine.persistence.close(); right.engine.persistence.close()
