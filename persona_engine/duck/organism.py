"""DUCK v0.1 organism loop over a persistent Wayfarer subject."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from uuid import uuid4

from .action import ActionGenerator, ActionSelector
from .attribution import AttributionBridge
from .executor import ActionExecutor, EmbodimentCapabilities, ExecutionPolicy
from .memory_bridge import SubjectMemoryActivation
from .metacognition import CalibrationMonitor
from .motivation import DriveSystem
from .persistence import DuckPersistence
from .procedures import ProcedureRegistry
from .reducer import CanonicalReducer
from .scheduler import CognitiveScheduler
from .services import NullServiceRegistry, ServiceContext, ServiceRegistry
from .simulation import RuleWorldModel, SimulationResult, effect_error
from .situation import SituationConstructor
from .subject_adapter import SubjectPort
from .types import CognitiveItem, CycleTrace, ExternalEvent, OrganismState, PredictionRecord, ProspectiveCommitment, StatePatch
from .workspace import GlobalWorkspace


@dataclass(frozen=True)
class DuckConfig:
    schema_version: str = "duck-organism-v0.1"
    working_memory_limit: int = 8
    drive_workspace_threshold: float = 0.10
    endogenous_drive_threshold: float = 0.22
    max_consecutive_endogenous_cycles: int = 4
    max_run_until_idle_cycles: int = 8
    memory_retrieval_width: int = 3
    enable_motivation: bool = True
    enable_memory_activation: bool = True
    enable_workspace: bool = True
    enable_simulation: bool = True

    def fingerprint(self) -> str:
        raw = json.dumps(self.__dict__, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()


class DuckOrganism:
    def __init__(
        self,
        subject: SubjectPort,
        *,
        organism_id: str | None = None,
        config: DuckConfig | None = None,
        drives: DriveSystem | None = None,
        world_model: RuleWorldModel | None = None,
        services: ServiceRegistry | None = None,
        procedures: ProcedureRegistry | None = None,
        execution_policy: ExecutionPolicy | None = None,
        embodiment: EmbodimentCapabilities | None = None,
        persistence: DuckPersistence | None = None,
        state: OrganismState | None = None,
    ):
        self.subject = subject
        self.config = config or DuckConfig()
        self.drives = drives or DriveSystem(state.drive_state if state else None)
        self.world_model = world_model or RuleWorldModel()
        self.services = services or NullServiceRegistry()
        self.procedures = procedures or ProcedureRegistry()
        self.persistence = persistence
        self.scheduler = CognitiveScheduler(
            drive_threshold=self.config.endogenous_drive_threshold,
            max_consecutive_endogenous=self.config.max_consecutive_endogenous_cycles,
        )
        self.workspace = GlobalWorkspace()
        self.situation_constructor = SituationConstructor()
        self.attribution = AttributionBridge()
        self.memory_activation = SubjectMemoryActivation()
        self.action_generator = ActionGenerator()
        self.action_selector = ActionSelector(self.drives)
        self.executor = ActionExecutor(self.world_model, policy=execution_policy, embodiment=embodiment)
        self.metacognition = CalibrationMonitor()
        self.reducer = CanonicalReducer()
        self.traces: list[CycleTrace] = []
        if state is None:
            state = OrganismState(
                schema_version=self.config.schema_version,
                organism_id=organism_id or str(uuid4()),
                subject_id=subject.subject_id,
                drive_state=self.drives.drives,
                config_fingerprint=self.config.fingerprint(),
            )
        if state.subject_id != subject.subject_id:
            raise ValueError("DUCK checkpoint subject_id does not match attached subject")
        self.state = state
        self.drives.drives = self.state.drive_state

    def current_state(self) -> OrganismState:
        return self.state

    def current_broadcast(self):
        return self.workspace.last_broadcast

    def set_services(self, services: ServiceRegistry) -> None:
        """Swap cognitive services without resetting the subject or organism state."""
        self.services = services

    def ingest(self, event: ExternalEvent) -> None:
        self.scheduler.ingest(event)

    def add_commitment(self, commitment: ProspectiveCommitment) -> None:
        if any(item.commitment_id == commitment.commitment_id for item in self.state.commitments):
            raise ValueError(f"duplicate commitment_id {commitment.commitment_id}")
        self.state.commitments.append(commitment)

    def save(self) -> str:
        if self.persistence is None:
            raise RuntimeError("DUCK persistence is not configured")
        return self.persistence.save(self.state)

    @classmethod
    def load(cls, subject: SubjectPort, persistence: DuckPersistence, **kwargs) -> "DuckOrganism":
        return cls(subject, persistence=persistence, state=persistence.load(), **kwargs)

    def _patch(self, *, domain: str, old_value, new_value, source: str, reason: str, evidence: tuple[str, ...] = ()) -> StatePatch:
        return StatePatch(
            domain=domain,
            key=domain,
            old_value=old_value,
            new_value=new_value,
            source_module=source,
            reason=reason,
            evidence_refs=evidence,
            tick=self.state.tick,
            authorization_class="duck_internal",
        )

    def _memory_query(self, trigger: ExternalEvent) -> str:
        payload = trigger.payload
        return str(
            payload.get("observed_text")
            or payload.get("description")
            or payload.get("topic")
            or payload.get("unresolved_question")
            or ""
        ).strip()

    def step(self, *, budget_ms: int | None = None) -> CycleTrace | None:
        del budget_ms
        trigger = self.scheduler.next_trigger(
            self.state,
            self.drives,
            allow_drive_triggers=self.config.enable_motivation,
        )
        if trigger is None:
            return None

        tick = self.state.tick
        patches: list[StatePatch] = []
        situation_changes, event_item = self.situation_constructor.update(
            self.state.situation,
            trigger,
            tick=tick,
            subject_id=self.state.subject_id,
        )
        attribution_frame = self.attribution.attribute(trigger, subject_id=self.state.subject_id, tick=tick)
        attribution_item = self.attribution.as_cognitive_item(attribution_frame, tick=tick, subject_id=self.state.subject_id)
        subject_result = self.subject.observe_event(trigger.payload)

        if self.config.enable_motivation:
            drive_changes = self.drives.step()
            self.drives.ensure_drive_goals(self.state.active_goals, tick=tick)
            drive_items = self.drives.cognitive_items(
                tick=tick,
                subject_id=self.state.subject_id,
                threshold=self.config.drive_workspace_threshold,
            )
        else:
            drive_changes = {"lesion": {"motivation": 1.0}}
            drive_items = []

        items: list[CognitiveItem] = [event_item, attribution_item]
        items.extend(drive_items)
        if self.config.enable_memory_activation:
            items.extend(self.memory_activation.retrieve(
                self.subject,
                query=self._memory_query(trigger),
                now=trigger.timestamp,
                tick=tick,
                subject_id=self.state.subject_id,
                top_k=self.config.memory_retrieval_width,
            ))

        service_projection = {
            "trigger": trigger.to_dict(),
            "attribution": attribution_frame.to_dict(),
            "situation": self.state.situation.to_dict(),
            "broadcast_history": self.state.working_memory[-3:],
            "active_goals": [goal.to_dict() for goal in self.state.active_goals if goal.status == "active"],
            "commitments": [item.to_dict() for item in self.state.commitments if item.status == "pending"],
            "drives": {name: drive.to_dict() for name, drive in sorted(self.drives.drives.items())},
            "subject": self.subject.snapshot(),
        }
        service_items, service_errors = self.services.proposals(ServiceContext(
            tick=tick,
            subject_id=self.state.subject_id,
            purpose="workspace_candidates",
            projection=service_projection,
        ))
        items.extend(service_items)

        broadcast = self.workspace.compete(items, tick=tick) if self.config.enable_workspace else None
        if broadcast is not None:
            next_working = (list(self.state.working_memory) + [broadcast.winner.to_dict()])[-self.config.working_memory_limit:]
            patch = self._patch(
                domain="working_memory",
                old_value=list(self.state.working_memory),
                new_value=next_working,
                source="workspace",
                reason="global broadcast changes bounded working memory",
                evidence=(broadcast.winner.item_id,),
            )
            self.reducer.apply(self.state, patch)
            patches.append(patch)

        actions = self.action_generator.generate(self.state, broadcast)
        actions.extend(self.procedures.candidates(self.state, broadcast))
        deduped = {action.action_id: action for action in actions}
        actions = [deduped[key] for key in sorted(deduped)]
        context = {
            "tick": tick,
            "situation": self.state.situation.to_dict(),
            "subject": self.subject.snapshot(),
            "confirmed": bool(trigger.payload.get("confirmed", False)),
        }
        if self.config.enable_simulation:
            simulations = [self.world_model.simulate(action, context) for action in actions]
        else:
            simulations = [SimulationResult(
                action_id=action.action_id,
                predicted_world_effects=dict(action.expected_world_effects),
                predicted_self_effects=dict(action.expected_self_effects),
                confidence=0.25,
                provenance={"source": "simulation_lesion", "action_type": action.action_type},
            ) for action in actions]

        action, simulation, score, breakdown = self.action_selector.select(actions, simulations, self.state)
        intention = self.action_selector.commit(action, simulation, tick=tick, score=score, breakdown=breakdown)
        intention_patch = self._patch(
            domain="current_intention",
            old_value=self.state.current_intention,
            new_value=intention,
            source="action_selector",
            reason="serialized action commitment after simulation",
            evidence=(broadcast.winner.item_id,) if broadcast else (),
        )
        self.reducer.apply(self.state, intention_patch)
        patches.append(intention_patch)

        execution = self.executor.execute(action, simulation, context)
        observed_world = execution.world_effects
        observed_self = execution.self_effects
        applied_drives = self.drives.apply_effects(observed_self) if self.config.enable_motivation else {}
        for commitment in self.state.commitments:
            if execution.executed and action.action_type == "honor_commitment" and action.parameters.get("commitment_id") == commitment.commitment_id:
                commitment.status = "completed"
        world_error = effect_error(simulation.predicted_world_effects, observed_world)
        self_error = effect_error(simulation.predicted_self_effects, observed_self)
        prediction = PredictionRecord(
            prediction_id=f"prediction:{tick}:{action.action_id}",
            intention_id=intention.intention_id,
            predicted_world_effects=dict(simulation.predicted_world_effects),
            predicted_self_effects=dict(simulation.predicted_self_effects),
            observed_world_effects=dict(observed_world),
            observed_self_effects=dict(observed_self),
            world_error=world_error,
            self_error=self_error,
        )
        if self.config.enable_simulation:
            self.world_model.learn(action.action_type, world_error=world_error, self_error=self_error)
        self.procedures.learn(action, prediction_error=(world_error + self_error) / 2.0)
        self.metacognition.observe(
            world_error=world_error,
            self_error=self_error,
            simulation_confidence=simulation.confidence,
        )

        action_entry = {
            "tick": tick,
            "intention": intention.to_dict(),
            "execution": execution.to_dict(),
            "outcome": {"world": observed_world, "self": observed_self, "drive_effects": applied_drives},
        }
        action_patch = self._patch(
            domain="action_ledger",
            old_value=list(self.state.action_ledger),
            new_value=(list(self.state.action_ledger) + [action_entry])[-128:],
            source="executor",
            reason="record observed action outcome",
            evidence=(trigger.event_id,),
        )
        self.reducer.apply(self.state, action_patch)
        patches.append(action_patch)
        prediction_patch = self._patch(
            domain="prediction_ledger",
            old_value=list(self.state.prediction_ledger),
            new_value=(list(self.state.prediction_ledger) + [prediction.to_dict()])[-128:],
            source="prediction",
            reason="compare expected and observed world/self effects",
            evidence=(intention.intention_id,),
        )
        self.reducer.apply(self.state, prediction_patch)
        patches.append(prediction_patch)

        self.subject.advance_time(1.0)
        tick_patch = self._patch(
            domain="tick",
            old_value=self.state.tick,
            new_value=self.state.tick + 1,
            source="scheduler",
            reason="complete one serialized cognitive cycle",
            evidence=(trigger.event_id,),
        )
        self.reducer.apply(self.state, tick_patch)
        patches.append(tick_patch)
        scheduler_patch = self._patch(
            domain="scheduler_state",
            old_value=dict(self.state.scheduler_state),
            new_value=self.scheduler.snapshot(),
            source="scheduler",
            reason="persist bounded endogenous scheduling state",
        )
        self.reducer.apply(self.state, scheduler_patch)
        patches.append(scheduler_patch)

        trace = CycleTrace(
            tick=tick,
            trigger=trigger.to_dict(),
            situation_changes={**situation_changes, "attribution": attribution_frame.to_dict(), "subject_observation": subject_result},
            drive_changes=drive_changes,
            cognitive_items=tuple(item.to_dict() for item in items),
            broadcast=broadcast.to_dict() if broadcast else None,
            action_candidates=tuple(item.to_dict() for item in actions),
            simulations=tuple(item.to_dict() for item in simulations),
            selected_intention=intention.to_dict(),
            outcome={"execution": execution.to_dict(), "world": observed_world, "self": observed_self, "drive_effects": applied_drives},
            prediction=prediction.to_dict(),
            patches=tuple(item.to_dict() for item in patches),
            service_errors=tuple(service_errors),
        )
        self.traces.append(trace)
        if self.persistence is not None:
            self.persistence.append_trace(trace)
            self.persistence.save(self.state)
        return trace

    def run_until_idle(self, *, max_cycles: int | None = None) -> list[CycleTrace]:
        limit = self.config.max_run_until_idle_cycles if max_cycles is None else int(max_cycles)
        traces: list[CycleTrace] = []
        for _ in range(max(0, limit)):
            trace = self.step()
            if trace is None:
                break
            traces.append(trace)
        return traces

    def metacognitive_report(self) -> dict:
        latest = self.state.prediction_ledger[-1] if self.state.prediction_ledger else None
        return {
            "subject_id": self.state.subject_id,
            "organism_id": self.state.organism_id,
            "tick": self.state.tick,
            "workspace_priority": self.workspace.last_broadcast.priority if self.workspace.last_broadcast else 0.0,
            "drive_urgency": {name: drive.urgency for name, drive in sorted(self.drives.drives.items())},
            "latest_prediction": latest,
            "calibration": self.metacognition.report(),
            "world_model_reliability": dict(sorted(self.world_model.reliability.items())),
            "service_count": len(self.services.services),
            "lesions": {
                "motivation": not self.config.enable_motivation,
                "memory_activation": not self.config.enable_memory_activation,
                "workspace": not self.config.enable_workspace,
                "simulation": not self.config.enable_simulation,
            },
        }
