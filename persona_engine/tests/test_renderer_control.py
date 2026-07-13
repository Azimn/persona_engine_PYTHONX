"""Renderer discovery, configuration, and fallback contracts."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from persona_engine.core.renderer import LocalLLMRenderer
from persona_engine.core.renderer_control import RendererConfig, RendererControlService


class _Response:
    def __init__(self, payload):
        self._body = json.dumps(payload).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def read(self):
        return self._body


def test_discovery_lists_local_ollama_models():
    def opener(request, timeout):
        assert request.full_url.endswith("/api/tags")
        assert timeout > 0
        return _Response({"models": [{"name": "qwen3:8b"}, {"name": "gemma3:1b"}]})

    result = RendererControlService(opener=opener).discover()
    ollama = next(item for item in result["providers"] if item["provider"] == "ollama")
    assert ollama["available"] is True
    assert ollama["models"] == ["gemma3:1b", "qwen3:8b"]


def test_discovery_preserves_offline_when_ollama_is_unreachable():
    def opener(_request, timeout):
        raise OSError("offline")

    result = RendererControlService(opener=opener).discover()
    providers = {item["provider"]: item for item in result["providers"]}
    assert providers["offline"]["available"] is True
    assert providers["ollama"]["available"] is False


@pytest.mark.parametrize(
    "field,value",
    [("provider", "network"), ("thinking_mode", "sometimes"), ("timeout_seconds", 0), ("token_budget", 2)],
)
def test_renderer_config_rejects_invalid_values(field, value):
    raw = RendererConfig().to_dict()
    raw[field] = value
    with pytest.raises(ValueError):
        RendererControlService().config_from_mapping(raw)


def test_ollama_request_uses_thinking_timeout_and_token_budget():
    captured = {}

    def opener(request, timeout):
        captured["payload"] = json.loads(request.data.decode("utf-8"))
        captured["timeout"] = timeout
        return _Response({"message": {"content": "A live local response."}})

    renderer = LocalLLMRenderer(
        model_name="qwen3:8b",
        provider="ollama",
        thinking_mode="on",
        timeout_seconds=12,
        token_budget=384,
        opener=opener,
    )
    output = renderer.generate([{"role": "user", "content": "Hello"}], seed=7)
    assert output == "A live local response."
    assert captured["timeout"] == 12
    assert captured["payload"]["think"] is True
    assert captured["payload"]["options"]["num_predict"] == 384
    assert captured["payload"]["options"]["seed"] == 7
    assert renderer.runtime_status()["actual_provider"] == "ollama"


def test_ollama_failure_falls_back_with_visible_reason():
    def opener(_request, timeout):
        raise TimeoutError("late")

    renderer = LocalLLMRenderer(model_name="slow:model", provider="ollama", opener=opener)
    output = renderer.generate([{"role": "user", "content": "Hello"}], seed=3)
    status = renderer.runtime_status()
    assert output
    assert status["actual_provider"] == "offline"
    assert status["requested_provider"] == "ollama"
    assert "TimeoutError" in status["fallback_reason"]


def test_ui_renderer_configuration_is_isolated_per_cartridge(tmp_path):
    try:
        from fastapi.testclient import TestClient
    except Exception:
        return
    from persona_engine.ui import create_app

    root = Path(__file__).resolve().parents[1]
    control = RendererControlService(opener=lambda _request, timeout: _Response({"models": [{"name": "qwen3:8b"}]}))
    app = create_app(
        cartridge_path=str(root / "cartridges" / "neutral.snp"),
        db_path=str(tmp_path),
        user_id="renderer_isolation",
        renderer_control=control,
    )
    client = TestClient(app)

    configured = client.post("/api/renderer/config", json={
        "provider": "ollama",
        "model_name": "qwen3:8b",
        "thinking_mode": "on",
        "timeout_seconds": 25,
        "token_budget": 320,
    })
    assert configured.status_code == 200
    assert configured.json()["config"]["model_name"] == "qwen3:8b"

    switched = client.post("/api/session/select", json={"cartridge": "friendly.snp"})
    assert switched.json()["renderer"]["config"]["provider"] == "offline"

    restored = client.post("/api/session/select", json={"cartridge": "neutral.snp"})
    assert restored.json()["renderer"]["config"]["model_name"] == "qwen3:8b"
