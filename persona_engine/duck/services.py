"""Typed non-authoritative cognitive service ports.

Services may perform expensive or neural proposal generation concurrently, but
all results return as noncanonical CognitiveItems. Canonical mutation remains a
serialized organism/subject responsibility.
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, wait
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


def _validated(service: CognitiveService, context: ServiceContext) -> list[CognitiveItem]:
    proposed = service.propose(context)
    items: list[CognitiveItem] = []
    for item in proposed:
        if not isinstance(item, CognitiveItem):
            raise TypeError("cognitive service must return CognitiveItem objects")
        if item.canonical:
            raise ValueError("cognitive service returned canonical proposal")
        if item.subject_id != context.subject_id:
            raise ValueError("cognitive service proposal subject_id mismatch")
        items.append(item)
    return items


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
                items.extend(_validated(service, context))
            except Exception as exc:  # service failure degrades by subsystem
                errors.append(f"{getattr(service, 'service_name', type(service).__name__)}:{type(exc).__name__}:{exc}")
        return items, errors


class ParallelServiceRegistry(ServiceRegistry):
    """Run proposal-only specialists concurrently with deterministic collation."""

    def __init__(self, services: list[CognitiveService] | None = None, *, timeout_seconds: float = 10.0, max_workers: int = 8):
        super().__init__(services)
        self.timeout_seconds = max(0.01, float(timeout_seconds))
        self.max_workers = max(1, int(max_workers))

    def proposals(self, context: ServiceContext) -> tuple[list[CognitiveItem], list[str]]:
        if not self.services:
            return [], []
        services = sorted(self.services, key=lambda service: (str(getattr(service, "service_name", "")), type(service).__name__))
        executor = ThreadPoolExecutor(max_workers=min(self.max_workers, len(services)), thread_name_prefix="duck-service")
        future_to_service = {executor.submit(_validated, service, context): service for service in services}
        done, pending = wait(future_to_service, timeout=self.timeout_seconds)
        items: list[CognitiveItem] = []
        errors: list[str] = []
        for future, service in sorted(
            future_to_service.items(),
            key=lambda pair: (str(getattr(pair[1], "service_name", "")), type(pair[1]).__name__),
        ):
            name = str(getattr(service, "service_name", type(service).__name__))
            if future in pending:
                future.cancel()
                errors.append(f"{name}:TimeoutError:proposal deadline exceeded")
                continue
            try:
                proposed = future.result()
                proposed.sort(key=lambda item: item.item_id)
                items.extend(proposed)
            except Exception as exc:
                errors.append(f"{name}:{type(exc).__name__}:{exc}")
        executor.shutdown(wait=False, cancel_futures=True)
        return items, errors


class ReplayServiceRegistry(ServiceRegistry):
    """Return recorded noncanonical proposals for exact model-assisted replay."""

    def __init__(self, proposals_by_tick: dict[int, list[dict]] | None = None):
        super().__init__([])
        self.proposals_by_tick = {int(key): list(value) for key, value in (proposals_by_tick or {}).items()}

    def proposals(self, context: ServiceContext) -> tuple[list[CognitiveItem], list[str]]:
        items: list[CognitiveItem] = []
        for raw in self.proposals_by_tick.get(context.tick, []):
            raw = dict(raw)
            raw["memory_refs"] = tuple(raw.get("memory_refs", ()))
            raw["canonical"] = False
            item = CognitiveItem(**raw)
            if item.subject_id != context.subject_id:
                raise ValueError("recorded service proposal subject_id mismatch")
            items.append(item)
        return items, []

    @classmethod
    def from_traces(cls, traces) -> "ReplayServiceRegistry":
        captured: dict[int, list[dict]] = {}
        for trace in traces:
            raw_trace = trace.to_dict() if hasattr(trace, "to_dict") else dict(trace)
            values = raw_trace.get("service_proposals", [])
            if values:
                captured[int(raw_trace["tick"])] = [dict(value) for value in values]
        return cls(captured)


class NullServiceRegistry(ServiceRegistry):
    def __init__(self):
        super().__init__([])
