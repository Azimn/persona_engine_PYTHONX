import subprocess
import sys

from persona_engine.core.cognition_schemas import stable_turn_seed, turn_seed
from persona_engine.core.renderer import LocalLLMRenderer


def test_turn_seed_is_stable_for_replay_inputs():
    assert turn_seed("s", 1, "private_cognition") == turn_seed("s", 1, "private_cognition")
    assert turn_seed("s", 1, "private_cognition") != turn_seed("s", 2, "private_cognition")
    assert turn_seed("s", 1, "private_cognition") == stable_turn_seed("s", 1, "private_cognition")


def test_turn_seed_is_stable_across_process_launches():
    code = "from persona_engine.core.cognition_schemas import stable_turn_seed; print(stable_turn_seed('s', 1, 'expression'))"
    first = subprocess.check_output([sys.executable, "-c", code], text=True).strip()
    second = subprocess.check_output([sys.executable, "-c", code], text=True).strip()
    assert first == second


def test_mock_renderer_replay_is_deterministic_with_fixed_seed():
    messages = [{"role": "user", "content": "hello"}]
    seed = turn_seed("session", 1, "expression")
    first = LocalLLMRenderer(model_name="missing-model-for-mock").generate(messages, seed=seed)
    second = LocalLLMRenderer(model_name="missing-model-for-mock").generate(messages, seed=seed)
    assert first == second
