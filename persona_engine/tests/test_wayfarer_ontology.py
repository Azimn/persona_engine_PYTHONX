"""Wayfarer regressions for character-scoped self-model policy."""

from persona_engine.agent import CharacterAgent
from persona_engine.core.identity import CoreIdentity, detect_identity_violations


def _agent(identity, tmp_path, name):
    return CharacterAgent(identity, user_id=name, db_path=str(tmp_path / f"{name}.db"))


def test_generic_identity_checker_has_no_universal_ai_ontology():
    assert detect_identity_violations("I am an AI.") == []
    violations = detect_identity_violations("I am an AI.", ("i am an ai",))
    assert violations
    assert violations[0].violation_type == "self_model_conflict"


def test_human_and_artificial_subjects_share_same_generic_engine(tmp_path):
    human = CoreIdentity(
        name="Mara",
        core_beliefs=("I am a human person",),
        temperament="measured",
        forbidden_self_claims=("i am an ai", "as an ai", "language model"),
    )
    artificial = CoreIdentity(
        name="Aster",
        core_beliefs=("I am an artificial intelligence",),
        temperament="measured",
        forbidden_self_claims=(),
    )
    human_agent = _agent(human, tmp_path, "human")
    artificial_agent = _agent(artificial, tmp_path, "artificial")

    human_agent.engine.renderer.generate_expression = lambda request: "I am an AI."
    artificial_agent.engine.renderer.generate_expression = lambda request: "I am an AI."

    human_result = human_agent.say("What are you?")
    artificial_result = artificial_agent.say("What are you?")

    assert any(v.startswith("self_model_conflict:") for v in human_result["violations_caught"])
    assert "I am an AI" not in human_result["response"]
    assert not any(v.startswith("self_model_conflict:") for v in artificial_result["violations_caught"])
    assert artificial_result["response"] == "I am an AI."

    assert "never say you are an ai" not in human_result["system_prompt"].lower()
    assert "never say you are an ai" not in artificial_result["system_prompt"].lower()
    assert "i am an ai" in human_result["system_prompt"].lower()
    assert "i am an ai" not in artificial_result["system_prompt"].lower()


def test_self_model_constraints_survive_renderer_replacement(tmp_path):
    identity = CoreIdentity(
        name="Mara",
        core_beliefs=("I am human",),
        temperament="steady",
        forbidden_self_claims=("i am an ai",),
    )
    agent = _agent(identity, tmp_path, "renderer_swap")

    class ReplacementRenderer:
        def generate_expression(self, request):
            return "I am an AI."

        def generate_private_cognition(self, request):
            from persona_engine.core.cognition_schemas import PrivateCognitionProposal
            from persona_engine.core.renderer_contract import PrivateCognitionResult
            return PrivateCognitionResult(
                PrivateCognitionProposal(
                    prose="",
                    attention_targets=[],
                    pressure_deltas={},
                    impulse_candidates=[],
                    memory_activation_requests=[],
                    cognitive_theme_ids=[],
                )
            )

    agent.engine.set_renderer(ReplacementRenderer())
    result = agent.say("Describe yourself.")
    assert any(v.startswith("self_model_conflict:") for v in result["violations_caught"])
    assert "I am an AI" not in result["response"]
