import sys
import types

from persona_engine.core.local_hf_renderer import LocalHFRenderer
from persona_engine.core.model_registry import ModelRegistry, ModelRegistryEntry, resolve_model
from persona_engine.core.renderer_contract import ExpressionRequest, PrivateCognitionRequest, PrivateCognitionResult


def test_model_registry_resolves_logical_qwen_entry():
    entry = resolve_model("persona-qwen3-1.7b-lora")
    assert entry.backend == "hf"
    assert entry.base_model_id == "Qwen/Qwen3-1.7B"
    assert entry.adapter_path is None


def test_model_registry_can_override_without_cartridge_path_hardcoding():
    registry = ModelRegistry({
        "test-persona": ModelRegistryEntry(
            name="test-persona",
            backend="hf",
            base_model_id="example/base",
            adapter_path="first",
        )
    })
    entry = registry.resolve("test-persona", adapter_path="second")
    assert entry.base_model_id == "example/base"
    assert entry.adapter_path == "second"


def test_local_hf_private_cognition_strict_json_success_without_loading_model():
    renderer = LocalHFRenderer("persona-qwen3-1.7b-lora")
    proposal = renderer._parse_private_cognition_json(
        '{"prose":"quiet pressure","attention_targets":["user"],"pressure_deltas":{"fear":0.1},'
        '"impulse_candidates":[{"type":"watch","strength":0.7,"target":"sound"}],'
        '"memory_activation_requests":["probe_for_motive"],"cognitive_theme_ids":["probe_for_motive"]}'
    )
    assert proposal.prose == "quiet pressure"
    assert proposal.pressure_deltas == {"fear": 0.1}
    assert proposal.impulse_candidates[0].type == "watch"


def test_local_hf_private_cognition_parse_error_fails_closed():
    renderer = LocalHFRenderer("persona-qwen3-1.7b-lora")
    proposal = renderer._parse_private_cognition_json("not json")
    assert proposal.prose == ""
    assert proposal.pressure_deltas == {}
    assert proposal.impulse_candidates == []


def test_local_hf_private_cognition_rejects_json_nan_constant():
    renderer = LocalHFRenderer("persona-qwen3-1.7b-lora")
    proposal = renderer._parse_private_cognition_json(
        '{"prose":"","attention_targets":[],"pressure_deltas":{"fear":NaN},'
        '"impulse_candidates":[],"memory_activation_requests":[],"cognitive_theme_ids":[]}'
    )
    assert proposal.pressure_deltas == {}


def test_local_hf_private_cognition_generation_error_fails_closed():
    class BrokenHF(LocalHFRenderer):
        def _generate_text(self, prompt, *, seed, max_new_tokens=None):
            raise RuntimeError("model unavailable")

    result = BrokenHF("persona-qwen3-1.7b-lora").generate_private_cognition(
        PrivateCognitionRequest({}, {}, {}, [], [], {}, seed=1)
    )
    assert isinstance(result, PrivateCognitionResult)
    assert result.proposal.pressure_deltas == {}
    assert result.diagnostics["failed_closed"] is True


def test_local_hf_renderer_load_uses_mocked_transformers_and_peft(monkeypatch):
    calls = {}

    class FakeInputs(dict):
        def to(self, device):
            calls["input_device"] = device
            return self

    class FakeTokenizer:
        @classmethod
        def from_pretrained(cls, model_id, **kwargs):
            calls["tokenizer_id"] = model_id
            return cls()

        def __call__(self, prompt, return_tensors):
            calls["prompt"] = prompt
            return FakeInputs(input_ids=[1])

        def decode(self, output, skip_special_tokens=True):
            return '{"prose":"","attention_targets":[],"pressure_deltas":{},"impulse_candidates":[],"memory_activation_requests":[],"cognitive_theme_ids":[]}'

    class FakeModel:
        device = "cpu"

        @classmethod
        def from_pretrained(cls, model_id, **kwargs):
            calls["model_id"] = model_id
            return cls()

        def generate(self, **kwargs):
            calls["generated"] = True
            return [[1, 2, 3]]

    class FakePeftModel:
        @classmethod
        def from_pretrained(cls, model, adapter_path, **kwargs):
            calls["adapter_path"] = adapter_path
            return model

    monkeypatch.setitem(sys.modules, "transformers", types.SimpleNamespace(
        AutoTokenizer=FakeTokenizer,
        AutoModelForCausalLM=FakeModel,
    ))
    monkeypatch.setitem(sys.modules, "peft", types.SimpleNamespace(PeftModel=FakePeftModel))

    renderer = LocalHFRenderer(
        "custom",
        registry_entry=ModelRegistryEntry(
            name="custom",
            backend="hf",
            base_model_id="base/model",
            adapter_path="adapter/path",
            tokenizer_id="tokenizer/model",
        ),
    )
    result = renderer.generate_private_cognition(PrivateCognitionRequest({}, {}, {}, [], [], {}, seed=3))
    assert calls["tokenizer_id"] == "tokenizer/model"
    assert calls["model_id"] == "base/model"
    assert calls["adapter_path"] == "adapter/path"
    assert calls["generated"] is True
    assert result.proposal.pressure_deltas == {}


def test_local_hf_expression_falls_back_on_generation_failure():
    class BrokenHF(LocalHFRenderer):
        def _generate_text(self, prompt, *, seed, max_new_tokens=None):
            raise RuntimeError("model unavailable")

    response = BrokenHF("persona-qwen3-1.7b-lora").generate_expression(ExpressionRequest(
        ledger_digest={},
        resolved_state={"user_text": "hello"},
        arc_context={},
        evidence=[],
        retrieved_memories=[],
        private_thought_context="",
        decision_payload={"dialogue_act": "respond"},
        expression_constraints={"max_chars": 80},
        deception_obligations=[],
        seed=1,
    ))
    assert response
    assert "ollama" not in response.lower()
