"""Logical model registry for renderer backends.

Cartridges should refer to stable logical names. The registry maps those names
to provider-specific model IDs and optional adapter locations.
"""

from __future__ import annotations

from dataclasses import dataclass, replace


@dataclass(frozen=True)
class ModelRegistryEntry:
    name: str
    backend: str
    base_model_id: str
    adapter_path: str | None = None
    revision: str | None = None
    tokenizer_id: str | None = None
    local_files_only: bool = False


DEFAULT_MODEL_REGISTRY: dict[str, ModelRegistryEntry] = {
    "persona-qwen3-1.7b-lora": ModelRegistryEntry(
        name="persona-qwen3-1.7b-lora",
        backend="hf",
        base_model_id="Qwen/Qwen3-1.7B",
        adapter_path=None,
        tokenizer_id="Qwen/Qwen3-1.7B",
    ),
    "qwen3-1.7b-base": ModelRegistryEntry(
        name="qwen3-1.7b-base",
        backend="hf",
        base_model_id="Qwen/Qwen3-1.7B",
        tokenizer_id="Qwen/Qwen3-1.7B",
    ),
}


class ModelRegistry:
    def __init__(self, entries: dict[str, ModelRegistryEntry] | None = None):
        self._entries = dict(entries or DEFAULT_MODEL_REGISTRY)

    def register(self, entry: ModelRegistryEntry) -> None:
        self._entries[entry.name] = entry

    def resolve(self, logical_name: str, **overrides) -> ModelRegistryEntry:
        entry = self._entries.get(logical_name)
        if entry is None:
            raise KeyError(f"unknown logical model_name: {logical_name}")
        clean_overrides = {key: value for key, value in overrides.items() if value is not None}
        return replace(entry, **clean_overrides) if clean_overrides else entry


DEFAULT_REGISTRY = ModelRegistry()


def resolve_model(logical_name: str, **overrides) -> ModelRegistryEntry:
    return DEFAULT_REGISTRY.resolve(logical_name, **overrides)
