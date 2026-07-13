import os

import pytest

from persona_engine.core.local_hf_renderer import LocalHFRenderer
from persona_engine.core.renderer_contract import PrivateCognitionRequest


@pytest.mark.integration
@pytest.mark.skipif(
    os.environ.get("PERSONA_ENGINE_RUN_HF_INTEGRATION") != "1",
    reason="set PERSONA_ENGINE_RUN_HF_INTEGRATION=1 to run optional HF loading test",
)
def test_local_hf_renderer_optional_integration_loads_configured_model():
    model_name = os.environ.get("PERSONA_ENGINE_HF_MODEL_NAME", "persona-qwen3-1.7b-lora")
    renderer = LocalHFRenderer(model_name)
    result = renderer.generate_private_cognition(PrivateCognitionRequest({}, {}, {}, [], [], {}, seed=1))
    assert result.proposal is not None
