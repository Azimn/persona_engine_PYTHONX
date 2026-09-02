from __future__ import annotations

from argparse import Namespace
import hashlib
import json

from persona_engine.evaluation.local_model_session import (
    build_artifact_manifest,
    build_selected_model_evidence,
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


def test_query_ollama_models_parses_registry_without_network(tmp_path, monkeypatch):
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

    preflight = {
        "created_at_utc": "2026-09-02T12:00:00+00:00",
        "platform": "Windows-test",
        "python": "3.11.16",
        "ollama": {
            "host": "http://localhost:11434",
            "models": [model.to_dict() for model in models],
        },
    }
    evidence = build_selected_model_evidence(preflight, "chat:latest")
    assert evidence is not None
    assert evidence["model"]["digest"] == "sha256:registry"
    assert evidence["model"]["parameter_size"] == "3B"
    assert evidence["ollama_host"] == "http://localhost:11434"
    assert build_selected_model_evidence(preflight, "missing:latest") is None

    artifact = tmp_path / "result.json"
    artifact.write_text('{"ok": true}\n', encoding="utf-8")
    manifest = build_artifact_manifest({"result": artifact, "missing": tmp_path / "missing.json"})
    expected = hashlib.sha256(artifact.read_bytes()).hexdigest()
    assert manifest == {
        "result": {
            "filename": "result.json",
            "sha256": expected,
            "size_bytes": artifact.stat().st_size,
        }
    }

    from tools import local_eval

    output_dir = tmp_path / "session"

    def fake_preflight(output_dir_arg, **kwargs):
        assert output_dir_arg == output_dir
        output_dir_arg.mkdir(parents=True, exist_ok=True)
        (output_dir_arg / "preflight.json").write_text(
            json.dumps(preflight, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        return preflight, "chat:latest", 0

    def fake_degradation(model, *, host, timeout_seconds, token_budget, thinking_mode, output):
        assert model == "chat:latest"
        report = {
            "valid_actual_model_run": True,
            "reliability": {"refusal": {"passed": 5, "total": 5}},
        }
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(report, sort_keys=True) + "\n", encoding="utf-8")
        return report, 0

    monkeypatch.setattr(local_eval, "_preflight_or_block", fake_preflight)
    monkeypatch.setattr(local_eval, "run_degradation_ollama", fake_degradation)
    args = Namespace(
        output_dir=output_dir,
        host="http://localhost:11434",
        registry_timeout=0.25,
        model="chat:latest",
        timeout_seconds=1.5,
        token_budget=64,
        thinking_mode="off",
    )
    assert local_eval.command_smoke(args) == 0
    summary = json.loads((output_dir / "SESSION_SUMMARY.json").read_text(encoding="utf-8"))
    assert summary["evidence_identity"]["model"]["digest"] == "sha256:registry"
    assert summary["run_parameters"] == {
        "host": "http://localhost:11434",
        "timeout_seconds": 1.5,
        "token_budget": 64,
        "thinking_mode": "off",
    }
    assert set(summary["artifacts"]) == {"degradation", "preflight"}
    for row in summary["artifacts"].values():
        assert len(row["sha256"]) == 64
        assert row["size_bytes"] > 0
