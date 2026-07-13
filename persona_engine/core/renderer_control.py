"""Renderer backend discovery and validated session configuration."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from typing import Any, Callable
from urllib.error import URLError
from urllib.request import Request, urlopen

from .model_capabilities import capabilities_for_model
from .model_registry import DEFAULT_MODEL_REGISTRY
from .renderer import LocalLLMRenderer


VALID_PROVIDERS = {"offline", "ollama", "local_hf"}
VALID_THINKING_MODES = {"auto", "on", "off"}


@dataclass(frozen=True)
class RendererConfig:
    provider: str = "offline"
    model_name: str = "offline-template"
    thinking_mode: str = "off"
    timeout_seconds: float = 60.0
    token_budget: int = 256

    def validate(self) -> "RendererConfig":
        if self.provider not in VALID_PROVIDERS:
            raise ValueError(f"unsupported renderer provider: {self.provider}")
        if self.thinking_mode not in VALID_THINKING_MODES:
            raise ValueError(f"unsupported thinking mode: {self.thinking_mode}")
        if not self.model_name.strip():
            raise ValueError("model_name must not be empty")
        if not 1.0 <= float(self.timeout_seconds) <= 600.0:
            raise ValueError("timeout_seconds must be between 1 and 600")
        if not 16 <= int(self.token_budget) <= 8192:
            raise ValueError("token_budget must be between 16 and 8192")
        return self

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class BackendDiscovery:
    provider: str
    available: bool
    models: tuple[str, ...]
    detail: str
    model_capabilities: dict[str, dict]

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["models"] = list(self.models)
        return payload


class RendererControlService:
    """Discovers renderer providers and creates renderer-only adapters."""

    def __init__(self, ollama_host: str = "http://127.0.0.1:11434", opener: Callable[..., Any] = urlopen):
        self.ollama_host = ollama_host.rstrip("/")
        self._opener = opener

    def _get_json(self, path: str, timeout: float = 1.5) -> dict[str, Any]:
        request = Request(f"{self.ollama_host}{path}", headers={"Accept": "application/json"})
        with self._opener(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))

    def discover(self) -> dict[str, Any]:
        available = False
        models: tuple[str, ...] = ()
        detail = "Ollama is not reachable; offline rendering remains available."
        try:
            payload = self._get_json("/api/tags")
            names = {
                str(item.get("name") or item.get("model") or "").strip()
                for item in payload.get("models", [])
                if isinstance(item, dict)
            }
            models = tuple(sorted(name for name in names if name))
            available = True
            detail = f"Ollama reachable with {len(models)} local model(s)."
        except (OSError, URLError, ValueError, TypeError, json.JSONDecodeError):
            pass

        providers = (
            BackendDiscovery(
                "offline",
                True,
                ("offline-template",),
                "Deterministic dependency-free renderer.",
                {"offline-template": capabilities_for_model("offline-template", "offline").to_dict()},
            ),
            BackendDiscovery(
                "ollama",
                available,
                models,
                detail,
                {name: capabilities_for_model(name, "ollama").to_dict() for name in models},
            ),
            BackendDiscovery(
                "local_hf",
                False,
                tuple(sorted(DEFAULT_MODEL_REGISTRY)),
                "Future local-HF provider; registry entries are visible but runtime selection is disabled.",
                {name: capabilities_for_model(name, "local_hf").to_dict() for name in sorted(DEFAULT_MODEL_REGISTRY)},
            ),
        )
        return {"providers": [provider.to_dict() for provider in providers]}

    def config_from_mapping(self, raw: dict[str, Any]) -> RendererConfig:
        provider = str(raw.get("provider", "offline"))
        default_model = "offline-template" if provider == "offline" else ""
        model_name = str(raw.get("model_name", default_model))
        recommended_thinking = capabilities_for_model(model_name, provider).recommended_thinking
        config = RendererConfig(
            provider=provider,
            model_name=model_name,
            thinking_mode=str(raw.get("thinking_mode", recommended_thinking)),
            timeout_seconds=float(raw.get("timeout_seconds", 60.0)),
            token_budget=int(raw.get("token_budget", 256)),
        ).validate()
        if config.provider == "ollama":
            ollama = next(item for item in self.discover()["providers"] if item["provider"] == "ollama")
            if not ollama["available"]:
                raise ValueError("Ollama is not reachable")
            if config.model_name not in ollama["models"]:
                raise ValueError(f"Ollama model is not installed: {config.model_name}")
            capabilities = capabilities_for_model(config.model_name, "ollama")
            if capabilities.supports_thinking is False and config.thinking_mode == "on":
                raise ValueError(f"thinking mode is not supported by the selected model profile: {config.model_name}")
        return config

    def build_renderer(self, config: RendererConfig):
        config.validate()
        if config.provider == "local_hf":
            raise ValueError("local_hf is registered for future use but is not enabled in the human UI")
        return LocalLLMRenderer(
            model_name=config.model_name,
            host=self.ollama_host,
            provider=config.provider,
            thinking_mode=config.thinking_mode,
            timeout_seconds=config.timeout_seconds,
            token_budget=config.token_budget,
        )
