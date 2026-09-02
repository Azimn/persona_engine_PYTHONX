from __future__ import annotations

import json

from persona_engine.evaluation.local_model_session import (
    normalize_ollama_models,
    parse_parameter_billions,
    query_ollama_models,
    recommend_installed_models,
)


def test_parse_parameter_billions_supports_common_ollama_units():
    assert parse_parameter_billions("3.2B") == 3.2
    assert parse_parameter_billions("8B") == 8.0
    assert parse_parameter_billions("360M") == 0.36
    assert parse_parameter_billions("1.1T") == 1100.0
    assert parse_parameter_billions("unknown") is None


def test_normalize_models_excludes_embedding_models_and_assigns_tiers():
    payload = {
        "models": [
            {
                "name": "small-chat:latest",
                "digest": "sha256:small",
                "modified_at": "2026-09-01T12:00:00Z",
                "size": 2_000_000_000,
                "details": {"parameter_size": "3B", "quantization_level": "Q4_K_M", "family": "chat"},
            },
            {
                "name": "medium-chat:latest",
                "size": 5_000_000_000,
                "details": {"parameter_size": "8B", "quantization_level": "Q4_K_M", "family": "chat"},
            },
            {
                "name": "nomic-embed-text:latest",
                "size": 500_000_000,
                "details": {"parameter_size": "137M", "family": "nomic-bert"},
            },
        ]
    }
    models = normalize_ollama_models(payload)
    by_name = {model.name: model for model in models}
    assert by_name["small-chat:latest"].tier == "small"
    assert by_name["small-chat:latest"].digest == "sha256:small"
    assert by_name["small-chat:latest"].modified_at == "2026-09-01T12:00:00Z"
    assert by_name["medium-chat:latest"].tier == "medium"
    assert by_name["nomic-embed-text:latest"].eligible_for_text_eval is False


def test_recommendations_target_small_then_medium_without_selecting_large():
    models = normalize_ollama_models(
        {
            "models": [
                {"name": "tiny:latest", "details": {"parameter_size": "0.6B"}},
                {"name": "small:latest", "details": {"parameter_size": "3B"}},
                {"name": "medium:latest", "details": {"parameter_size": "8B"}},
                {"name": "huge:latest", "details": {"parameter_size": "70B"}},
            ]
        }
    )
    recommendation = recommend_installed_models(models)
    assert recommendation["smoke_model"] == "small:latest"
    assert recommendation["comparison_model"] == "medium:latest"
    assert recommendation["auto_selected_large_model"] is False


def test_coding_specialized_model_is_not_automatically_selected_for_persona_eval():
    models = normalize_ollama_models(
        {
            "models": [
                {"name": "qwen-coder:3b", "details": {"parameter_size": "3B", "family": "qwen"}},
                {"name": "general-chat:3b", "details": {"parameter_size": "3B", "family": "chat"}},
                {"name": "codegemma:7b", "details": {"parameter_size": "7B", "family": "gemma"}},
                {"name": "general-chat:8b", "details": {"parameter_size": "8B", "family": "chat"}},
            ]
        }
    )
    by_name = {model.name: model for model in models}
    assert by_name["qwen-coder:3b"].eligible_for_text_eval is False
    assert by_name["codegemma:7b"].eligible_for_text_eval is False
    recommendation = recommend_installed_models(models)
    assert recommendation["smoke_model"] == "general-chat:3b"
    assert recommendation["comparison_model"] == "general-chat:8b"


def test_query_ollama_models_parses_registry_without_network():
    class Response:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def read(self):
            return json.dumps(
                {
                    "models": [
                        {
                            "name": "chat:latest",
                            "digest": "sha256:registry",
                            "modified_at": "2026-09-01T12:00:00Z",
                            "size": 2_000_000_000,
                            "details": {"parameter_size": "3B", "family": "chat"},
                        }
                    ]
                }
            ).encode("utf-8")

    def opener(request, timeout):
        assert request.full_url.endswith("/api/tags")
        assert timeout == 0.25
        return Response()

    models, error = query_ollama_models("http://localhost:11434", timeout_seconds=0.25, opener=opener)
    assert error is None
    assert [model.name for model in models] == ["chat:latest"]
    assert models[0].digest == "sha256:registry"
