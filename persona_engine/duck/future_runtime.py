"""Production-candidate composition root for the DUCK future-build experiment."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .capabilities import CapabilityRegistry
from .embodiment_port import EmbodiedWorldModel, EmbodimentPort, NullEmbodimentPort
from .endogenous import EndogenousReflectionService, EndogenousTriggerPolicy
from .executor import EmbodimentCapabilities
from .future_persistence import FutureRuntimePersistence
from .organism import DuckConfig, DuckOrganism
from .services import ParallelServiceRegistry, ServiceRegistry
from .subject_adapter import SubjectPort
from .temporal_patterns import TemporalPatternBank
from .timebase import TemporalAuthority, TemporalStamp, TimedSubjectProxy
from .types import CycleTrace, ExternalEvent


@dataclass(frozen=True)
class FutureRuntimeConfig:
    enable_endogenous_cognition: bool = True
    endogenous_threshold: float = 0.35
    endogenous_cooldown_ticks: int = 3
    max_background_cycles: int = 4
    poll_embodiment_before_step: bool = True
    default_external_elapsed_seconds: float = 1.0


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
        self.subject_proxy = TimedSubjectProxy(subject, default_elapsed_seconds=self.runtime_config.default_external_elapsed_seconds)
        self.embodiment = embodiment or NullEmbodimentPort()
        self.capabilities = capabilities or CapabilityRegistry()
        self.runtime_persistence = FutureRuntimePersistence(persistence.root) if persistence is not None and hasattr(persistence, "root") else None
        saved = self.runtime_persistence.load() if self.runtime_persistence and self.runtime_persistence.exists() else {}
        self.time = TemporalAuthority.from_dict(saved.get("time"))
        self.patterns = TemporalPatternBank.from_dict(saved.get("temporal_patterns"))
        self.endogenous_policy = EndogenousTriggerPolicy(
            threshold=self.runtime_config.endogenous_threshold,
            cooldown_ticks=self.runtime_config.endogenous_cooldown_ticks,
        )
        self.endogenous_policy.last_trigger_tick = int(saved.get("endogenous_last_trigger_tick", -10**9))
        self._event_counter = int(saved.get("event_counter", 0))
        self.body_history = [str(value) for value in saved.get("body_history", [])]
        if not self.body_history or self.body_history[-1] != self.embodiment.body_id:
            self.body_history.append(self.embodiment.body_id)

        if services is None:
            services = ParallelServiceRegistry([EndogenousReflectionService()])
        elif self.runtime_config.enable_endogenous_cognition:
            services.add(EndogenousReflectionService())

        body = self.embodiment.snapshot()
        world_model = EmbodiedWorldModel(self.embodiment, state.world_model_state if state else None)
        self.organism = DuckOrganism(
            self.subject_proxy,
            organism_id=organism_id,
            config=organism_config,
            world_model=world_model,
            services=services,
            execution_policy=self.capabilities.execution_policy(),
            embodiment=self._capabilities_from_body(body),
            persistence=persistence,
            state=state,
        )

    @staticmethod
    def _capabilities_from_body(body):
        return EmbodimentCapabilities(
            sensors=frozenset(body.sensors),
            effectors=frozenset(body.effectors),
            body_state=dict(body.state),
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

    def _runtime_state(self) -> dict[str, Any]:
        return {
            "event_counter": self._event_counter,
            "time": self.time.to_dict(),
            "temporal_patterns": self.patterns.to_dict(),
            "endogenous_last_trigger_tick": self.endogenous_policy.last_trigger_tick,
            "body_history": list(self.body_history),
            "subject_id": self.subject_id,
        }

    def _save_runtime_state(self) -> None:
        if self.runtime_persistence is not None:
            self.runtime_persistence.save(self._runtime_state())

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
        stamp = (
            self.time.observe(float(utc_epoch), logical_tick=self.tick, source=source)
            if utc_epoch is not None
            else self.time.logical_only(logical_tick=self.tick, source=source)
        )
        enriched["temporal_stamp"] = stamp.to_dict()
        pattern_key = enriched.get("temporal_pattern_key")
        if pattern_key and stamp.beat is not None:
            enriched["temporal_expectation"] = self.patterns.assess_then_observe(str(pattern_key), stamp.beat)
        event = ExternalEvent(
            event_id=event_id or self._next_event_id(source),
            kind=str(kind),
            payload=enriched,
            source=str(source),
            timestamp=float(utc_epoch) if utc_epoch is not None else float(self.tick),
            confidence=float(confidence),
        )
        self.organism.ingest(event)
        self._save_runtime_state()
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

    def swap_embodiment(self, embodiment: EmbodimentPort) -> None:
        """Attach a new body without changing the continuing subject."""
        self.embodiment = embodiment
        if not self.body_history or self.body_history[-1] != embodiment.body_id:
            self.body_history.append(embodiment.body_id)
        current_world = self.organism.current_state().world_model_state
        world_model = EmbodiedWorldModel(embodiment, current_world)
        self.organism.world_model = world_model
        self.organism.executor.world_model = world_model
        self.organism.executor.embodiment = self._capabilities_from_body(embodiment.snapshot())
        self._save_runtime_state()

    def set_services(self, services: ServiceRegistry) -> None:
        if self.runtime_config.enable_endogenous_cognition:
            services.add(EndogenousReflectionService())
        self.organism.set_services(services)

    def _inject_endogenous_trigger(self) -> ExternalEvent | None:
        if not self.runtime_config.enable_endogenous_cognition:
            return None
        trigger = self.endogenous_policy.evaluate(self.organism.current_state())
        if trigger is None:
            return None
        return self.ingest_observation(
            {
                **trigger.payload,
                "description": f"background cognition: {trigger.reason}",
                "salience": trigger.pressure,
                "self_relevance": 1.0,
                "endogenous_reason": trigger.reason,
                "private": True,
            },
            source="endogenous_scheduler",
            kind="internal_reflection",
            event_id=f"internal:reflection:{self.tick}:{trigger.reason}",
        )

    def _prepare_subject_elapsed(self) -> None:
        scheduler = self.organism.scheduler
        if scheduler.external:
            event = scheduler.external[0]
            if str(event.kind).startswith("internal_"):
                elapsed = 0.0
            else:
                stamp = event.payload.get("temporal_stamp", {}) if isinstance(event.payload, dict) else {}
                explicit = stamp.get("elapsed_since_prior_utc") if isinstance(stamp, dict) else None
                elapsed = self.runtime_config.default_external_elapsed_seconds if explicit is None else max(0.0, float(explicit))
        else:
            # A scheduler-created drive/commitment cycle is cognition occurring at
            # the current lived moment, not proof that another second has passed.
            elapsed = 0.0
        self.subject_proxy.prepare_elapsed(elapsed)

    def step(self) -> CycleTrace | None:
        if self.runtime_config.poll_embodiment_before_step:
            self.poll_embodiment()
        self._prepare_subject_elapsed()
        trace = self.organism.step()
        if trace is None:
            if self._inject_endogenous_trigger() is None:
                return None
            self._prepare_subject_elapsed()
            trace = self.organism.step()
        if trace is not None:
            self._save_runtime_state()
        return trace

    def run_until_quiet(self, *, max_cycles: int | None = None) -> list[CycleTrace]:
        limit = self.runtime_config.max_background_cycles if max_cycles is None else max(0, int(max_cycles))
        traces: list[CycleTrace] = []
        for _ in range(limit):
            trace = self.step()
            if trace is None:
                break
            traces.append(trace)
        return traces

    def save(self) -> str:
        digest = self.organism.save()
        self._save_runtime_state()
        return digest

    def current_temporal_stamp(self) -> TemporalStamp | None:
        return self.time.last_stamp

    def status(self) -> dict[str, Any]:
        stamp = self.current_temporal_stamp()
        return {
            "subject_id": self.subject_id,
            "tick": self.tick,
            "temporal_stamp": stamp.to_dict() if stamp else None,
            "body": self.embodiment.snapshot().to_dict(),
            "body_history": list(self.body_history),
            "capabilities": self.capabilities.snapshot(),
            "temporal_patterns": self.patterns.to_dict(),
            "metacognition": self.organism.metacognitive_report(),
        }
