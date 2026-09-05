"""Production-candidate composition root for the DUCK future-build experiment."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .capabilities import CapabilityRegistry
from .embodiment_port import EmbodiedWorldModel, EmbodimentCognitiveService, EmbodimentPort, NullEmbodimentPort
from .endogenous import EndogenousReflectionService, EndogenousTriggerPolicy
from .executor import EmbodimentCapabilities
from .expression import DeterministicExpressionPort, ExpressionActionPreparer, ExpressionJournal, WayfarerExpressionPort
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
        expression_port=None,
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
        archive_lookup = getattr(persistence, "find_expression", None) if persistence is not None else None
        self.expression_journal = ExpressionJournal.from_dict(
            saved.get("expression_journal"),
            archive_lookup=archive_lookup if callable(archive_lookup) else None,
        )
        if expression_port is None:
            agent = getattr(subject, "agent", None)
            expression_port = WayfarerExpressionPort(agent) if agent is not None else DeterministicExpressionPort()
        self.expression_port = expression_port
        self.expression_preparer = ExpressionActionPreparer(self.expression_port, self.expression_journal)
        self.endogenous_policy = EndogenousTriggerPolicy(
            threshold=self.runtime_config.endogenous_threshold,
            cooldown_ticks=self.runtime_config.endogenous_cooldown_ticks,
        )
        self.endogenous_policy.last_trigger_tick = int(saved.get("endogenous_last_trigger_tick", -10**9))
        self._event_counter = int(saved.get("event_counter", 0))
        self.body_history = [str(value) for value in saved.get("body_history", [])]
        self.delivery_receipts = [dict(value) for value in saved.get("delivery_receipts", [])]
        if not self.body_history or self.body_history[-1] != self.embodiment.body_id:
            self.body_history.append(self.embodiment.body_id)

        services = services or ParallelServiceRegistry([])
        self._install_builtin_services(services)

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
        self.organism.executor.action_preparer = self.expression_preparer

    @staticmethod
    def _capabilities_from_body(body):
        return EmbodimentCapabilities(
            sensors=frozenset(body.sensors),
            effectors=frozenset(body.effectors),
            body_state=dict(body.state),
        )

    def _install_builtin_services(self, services: ServiceRegistry) -> None:
        names = {str(getattr(service, "service_name", type(service).__name__)) for service in services.services}
        if self.runtime_config.enable_endogenous_cognition and "endogenous_reflection" not in names:
            services.add(EndogenousReflectionService())
            names.add("endogenous_reflection")
        if "embodiment_state" not in names:
            services.add(EmbodimentCognitiveService(lambda: self.embodiment))

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
            "expression_journal": self.expression_journal.to_dict(),
            "endogenous_last_trigger_tick": self.endogenous_policy.last_trigger_tick,
            "body_history": list(self.body_history),
            "delivery_receipts": list(self.delivery_receipts[-256:]),
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

    def ingest_user_message(
        self,
        text: str,
        *,
        source: str = "user",
        utc_epoch: float | None = None,
        event_id: str | None = None,
    ) -> ExternalEvent:
        """Convert conversational input into perception plus an ordinary action option."""
        message = str(text)
        return self.ingest_observation(
            {
                "description": message,
                "observed_text": message,
                "salience": 0.92,
                "self_relevance": 0.72,
                "temporal_pattern_key": f"interaction:{source}",
                "action_candidates": [{
                    "action_id": f"respond:{self.tick}:{event_id or 'message'}",
                    "action_type": "communicate",
                    "parameters": {
                        "dialogue_act": "respond",
                        "semantic_goal": "respond_to_user_message",
                        "user_text": message,
                        "max_chars": 500,
                    },
                    "expected_world_effects": {"social_contact": 0.28, "conversation_progress": 0.35},
                    "expected_self_effects": {"drive:affiliation": 0.16, "drive:certainty": 0.04},
                    "feasibility": 0.99,
                    "cost": 0.02,
                    "risk": 0.05,
                    "uncertainty": 0.12,
                    "reversibility": 0.90,
                }],
            },
            source=source,
            kind="user_message",
            utc_epoch=utc_epoch,
            event_id=event_id,
        )

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
            event_utc = raw.pop("utc_epoch", utc_epoch)
            payload = dict(raw.pop("payload", raw))
            events.append(self.ingest_observation(
                payload,
                source=str(raw.pop("source", f"body:{self.embodiment.body_id}")),
                kind=str(raw.pop("kind", "observation")),
                utc_epoch=event_utc,
                event_id=raw.pop("event_id", None),
                confidence=float(raw.pop("confidence", 1.0)),
            ))
        return events

    def swap_embodiment(self, embodiment: EmbodimentPort, *, announce: bool = True) -> ExternalEvent | None:
        previous = self.embodiment.snapshot()
        self.embodiment = embodiment
        current = embodiment.snapshot()
        if not self.body_history or self.body_history[-1] != embodiment.body_id:
            self.body_history.append(embodiment.body_id)
        current_world = self.organism.current_state().world_model_state
        world_model = EmbodiedWorldModel(embodiment, current_world)
        self.organism.world_model = world_model
        self.organism.executor.world_model = world_model
        self.organism.executor.embodiment = self._capabilities_from_body(current)
        self.organism.executor.action_preparer = self.expression_preparer
        self._save_runtime_state()
        if not announce:
            return None
        return self.ingest_observation(
            {
                "description": "embodiment changed",
                "previous_body": previous.to_dict(),
                "current_body": current.to_dict(),
                "self_relevance": 1.0,
                "salience": 0.90,
            },
            source="embodiment",
            kind="body_transfer",
            event_id=f"body-transfer:{self.tick}:{current.body_id}",
        )

    def set_services(self, services: ServiceRegistry) -> None:
        self._install_builtin_services(services)
        self.organism.set_services(services)

    def set_expression_port(self, expression_port) -> None:
        self.expression_port = expression_port
        self.expression_preparer.port = expression_port

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
            elapsed = 0.0
        self.subject_proxy.prepare_elapsed(elapsed)

    def _execution_context(self) -> dict[str, Any]:
        return {}

    def _reconcile_execution(self, trace: CycleTrace) -> None:
        outcome = trace.outcome or {}
        execution = outcome.get("execution", {}) if isinstance(outcome, dict) else {}
        metadata = execution.get("metadata", {}) if isinstance(execution, dict) else {}
        receipt = metadata.get("speech_delivery_receipt") if isinstance(metadata, dict) else None
        if receipt:
            receipt_id = str(receipt.get("receipt_id", ""))
            if receipt_id and not any(str(item.get("receipt_id", "")) == receipt_id for item in self.delivery_receipts):
                self.delivery_receipts.append(dict(receipt))
                recorder = getattr(self.subject, "record_delivery_receipt", None)
                if callable(recorder):
                    recorder(dict(receipt))
        self._save_runtime_state()

    def step(self) -> CycleTrace | None:
        if self.runtime_config.poll_embodiment_before_step:
            self.poll_embodiment()
        self._prepare_subject_elapsed()
        # Execution-stage expression needs the same selected moment that DUCK
        # already resolved. DuckOrganism includes these fields in its action
        # context below via a small compatibility enrichment in organism.py.
        trace = self.organism.step()
        if trace is None:
            if self._inject_endogenous_trigger() is None:
                return None
            self._prepare_subject_elapsed()
            trace = self.organism.step()
        if trace is not None:
            self._reconcile_execution(trace)
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

    def latest_expression(self) -> dict[str, Any] | None:
        trace = self.organism.traces[-1] if self.organism.traces else None
        if trace is None or not trace.outcome:
            return None
        execution = trace.outcome.get("execution", {})
        metadata = execution.get("metadata", {}) if isinstance(execution, dict) else {}
        expression = metadata.get("expression") if isinstance(metadata, dict) else None
        return dict(expression) if isinstance(expression, dict) else None

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
            "expression_journal_size": len(self.expression_journal.rows),
            "expression_journal_limit": self.expression_journal.max_rows,
            "expression_archive_available": self.expression_journal.archive_lookup is not None,
            "delivery_receipt_count": len(self.delivery_receipts),
            "metacognition": self.organism.metacognitive_report(),
        }
