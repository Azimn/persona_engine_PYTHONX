"""Capability declarations and execution policy for DUCK effectors/tools."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from .executor import ExecutionPolicy


@dataclass(frozen=True)
class CapabilityDescriptor:
    capability_id: str
    action_type: str
    provider: str
    enabled: bool = True
    requires_confirmation: bool = False
    risk_class: str = "low"
    metadata: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class CapabilityRegistry:
    """Registry only. It never loads arbitrary source code into the kernel."""

    def __init__(self, descriptors: list[CapabilityDescriptor] | None = None):
        self._items: dict[str, CapabilityDescriptor] = {}
        for item in descriptors or []:
            self.register(item)

    def register(self, descriptor: CapabilityDescriptor) -> None:
        if not descriptor.capability_id or not descriptor.action_type:
            raise ValueError("capabilities require stable id and action_type")
        self._items[descriptor.capability_id] = descriptor

    def unregister(self, capability_id: str) -> None:
        self._items.pop(str(capability_id), None)

    def descriptors(self) -> list[CapabilityDescriptor]:
        return [self._items[key] for key in sorted(self._items)]

    def execution_policy(self) -> ExecutionPolicy:
        if not self._items:
            return ExecutionPolicy()
        enabled = {item.action_type for item in self._items.values() if item.enabled}
        denied = {item.action_type for item in self._items.values() if not item.enabled}
        confirm = {item.action_type for item in self._items.values() if item.enabled and item.requires_confirmation}
        enabled.add("wait")
        return ExecutionPolicy(
            allowed_actions=frozenset(enabled),
            denied_actions=frozenset(denied),
            confirmation_required=frozenset(confirm),
        )

    def snapshot(self) -> dict[str, Any]:
        return {"capabilities": [item.to_dict() for item in self.descriptors()]}
