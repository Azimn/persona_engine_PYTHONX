"""Production-candidate composition root for the DUCK future-build experiment.

This module intentionally composes mature existing DUCK/Wayfarer mechanisms
instead of replacing them. DuckOrganism remains the cognitive-cycle engine and
Wayfarer remains the persistent subject authority. The future runtime adds the
missing production seams: explicit civil/Beat time, a replaceable body port,
bounded background cognition, and declared effector/tool capabilities.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .capabilities import CapabilityRegistry
from .embodiment_port import EmbodiedWorldModel, EmbodimentPort, NullEmbodimentPort
from .endogenous import EndogenousReflectionService, EndogenousTriggerPolicy
from .executor import EmbodimentCapabilities
from .organism import DuckConfig, DuckOrganism
from .services import ParallelServiceRegistry, ServiceRegistry
from .subject_adapter import SubjectPort
from .timebase import TemporalAuthority, TemporalStamp
from .types import CycleTrace, ExternalEvent


@dataclass(frozen=True)
class FutureRuntimeConfig:
    enable_endogenous_cognition: bool = True
    endogenous_threshold: float = 0.35
    endogenous_cooldown_ticks: int = 3
    max_background_cycles: int = 4
    poll_embodiment_before_step: bool = True


class FutureDuckRuntime:
    """One production-facing shell around the subject-centered DUCK organism."""

    def __init__(
        self,
        subject: SubjectPort,
        *,
        organism_config: DuckConfig | None = None,
        runtime_config: FutureRuntimeConfig | None = None,
        embodiment: EmbodimentPort | None = None,
        capabilities: CapabilityRegistry | None = None,
        services: ServiceRegistry | None = None,
        persistence=None,
        state=None,
        organism_id: str | None = None,
    ):
        self.subject = subject
        self.runtime_config = runtime_config or FutureRuntimeConfig()
        self.time = TemporalAuthority()
        self.embodiment = embodiment or NullEmbodimentPort()
        self.capabilities = capabilities or CapabilityRegistry()
        self.endogenous_policy = EndogenousTriggerPolicy(
            threshold=self.runtime_config.endogenous_threshold,
            cooldown_ticks=self.runtime_config.endogenous_cooldown_ticks,
        )
        self._event_counter = 0

        if services is None:
            services = ParallelServiceRegistry([EndogenousReflectionService()])
        elif self.runtime_config.enable_endogenous_cognition:
            # Registry.add preserves the same proposal-only validation firewall.
            services.add(EndogenousReflectionService())

        body = self.embodiment.snapshot()
        world_model = EmbodiedWorldModel(self.embodiment, state.world_model_state if state else None)
        self.organism = DuckOrganism(
            subject,
            organism_id=organism_id,
            config=organism_config,
            world_model=world_model,
            services=services,
            execution_policy=self.capabilities.execution_policy(),
            embodiment=EmbodimentCapabilities(
                sensors=frozenset(body.sensors),
                effectors=frozenset(body.effectors),
                body_state=dict(body.state),
            ),
            persistence=persistence,
            state=state,
        )

    @property
    def subject_id(self) -> str:
        return self.organism.current_state().subject_id

    @property
    def tick(self) -> int:
        return self.organism.current_state().tick

    def _next_event_id(self, prefix: str) -> str:
        self._event_counter += 1
        return f"{prefix}:{self.tick}:{self._event_counter}"

    def ingest_observation(
        self,
        payload: dict[str, Any],
        *,
        source: str = "environment",
        kind: str = "observation",
        utc_epoch: float | None = None,
        event_id: str | None = None,
        confidence: float = 1.0,
    ) -> ExternalEvent:
        enriched = dict(payload)
        if utc_epoch is not None:
            enriched["utc_epoch"] = float(utc_epoch)
        enriched = self.time.stamp_payload(
            enriched,
            logical_tick=self.tick,
            source=source,
        )
        event = ExternalEvent(
            event_id=event_id or self._next_event_id(source),
            kind=str(kind),
            payload=enriched,
            source=str(source),
            timestamp=float(utc_epoch) if utc_epoch is not None else float(self.tick),
            confidence=float(confidence),
        )
        self.organism.ingest(event)
        return event

    def observe_civil_time(self, utc_epoch: float, *, source: str = "clock") -> ExternalEvent:
        return self.ingest_observation(
            {"description": "explicit civil-time observation", "salience": 0.02},
            source=source,
            kind="time_observation",
            utc_epoch=utc_epoch,
        )

    def poll_embodiment(self, *, utc_epoch: float | None = None) -> list[ExternalEvent]:
        events: list[ExternalEvent] = []
        for raw in self.embodiment.observe(tick=self.tick):
            raw = dict(raw)
            payload = dict(raw.pop("payload", raw))
            events.append(self.ingest_observation(
                payload,
                source=str(raw.pop("source", f"body:{self.embodiment.body_id}")),
                kind=str(raw.pop("kind", "observation")),
                utc_epoch=utc_epoch,
                event_id=raw.pop("event_id", None),
                confidence=float(raw.pop("confidence", 1.0)),
            ))
        return events

    def _inject_endogenous_trigger(self) -> ExternalEvent | None:
        if not self.runtime_config.enable_endogenous_cognition:
            return None
        trigger = self.endogenous_policy.evaluate(self.organism.current_state())
        if trigger is None:
            return None
        payload = {
            **trigger.payload,
            "description": f"background cognition: {trigger.reason}",
            "salience": trigger.pressure,
            "self_relevance": 1.0,
            "endogenous_reason": trigger.reason,
            "private": True,
        }
        return self.ingest_observation(
            payload,
            source="endogenous_scheduler",
            kind="internal_reflection",
            event_id=f"internal:reflection:{self.tick}:{trigger.reason}",
        )

    def step(self) -> CycleTrace | None:
        if self.runtime_config.poll_embodiment_before_step:
            self.poll_embodiment()
        trace = self.organism.step()
        if trace is not None:
            return trace
        if self._inject_endogenous_trigger() is None:
            return None
        return self.organism.step()

    def run_until_quiet(self, *, max_cycles: int | None = None) -> list[CycleTrace]:
        limit = self.runtime_config.max_background_cycles if max_cycles is None else max(0, int(max_cycles))
        traces: list[CycleTrace] = []
        for _ in range(limit):
            trace = self.step()
            if trace is None:
                break
            traces.append(trace)
        return traces

    def current_temporal_stamp(self) -> TemporalStamp | None:
        return self.time.last_stamp

    def status(self) -> dict[str, Any]:
        stamp = self.current_temporal_stamp()
        return {
            "subject_id": self.subject_id,
            "tick": self.tick,
            "temporal_stamp": stamp.to_dict() if stamp else None,
            "body": self.embodiment.snapshot().to_dict(),
            "capabilities": self.capabilities.snapshot(),
            "metacognition": self.organism.metacognitive_report(),
        }
