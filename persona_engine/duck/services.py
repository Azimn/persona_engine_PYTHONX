"""Typed non-authoritative cognitive service ports, including LLM adapters."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from .types import CognitiveItem


@dataclass(frozen=True)
class ServiceContext:
    tick: int
    subject_id: str
    purpose: str
    projection: dict


class CognitiveService(Protocol):
    service_name: str

    def propose(self, context: ServiceContext) -> list[CognitiveItem]: ...


class ServiceRegistry:
    def __init__(self, services: list[CognitiveService] | None = None):
        self.services = list(services or [])

    def add(self, service: CognitiveService) -> None:
        self.services.append(service)

    def proposals(self, context: ServiceContext) -> tuple[list[CognitiveItem], list[str]]:
        items: list[CognitiveItem] = []
        errors: list[str] = []
        for service in self.services:
            try:
                proposed = service.propose(context)
                for item in proposed:
                    if item.canonical:
                        raise ValueError("cognitive service returned canonical proposal")
                    items.append(item)
            except Exception as exc:  # service failure degrades by subsystem
                errors.append(f"{getattr(service, 'service_name', type(service).__name__)}:{type(exc).__name__}:{exc}")
        return items, errors


class NullServiceRegistry(ServiceRegistry):
    def __init__(self):
        super().__init__([])
