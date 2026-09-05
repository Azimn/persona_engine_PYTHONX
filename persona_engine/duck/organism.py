"""DUCK v0.1 organism loop over a persistent Wayfarer subject.

Proposal generation may be parallel or neural. Organism-owned canonical changes
are serialized through typed StatePatch operations. Wayfarer remains the
continuing subject authority for identity, autobiography, relationships and
subject-scoped epistemics.
"""

from __future__ import annotations

from copy import deepcopy
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
    def __init__(self, subject: SubjectPort, *, organism_id: str | None = None, config: DuckConfig | None = None, drives: DriveSystem | None = None, world_model: RuleWorldModel | None = None, services: ServiceRegistry | None = None, procedures: ProcedureRegistry | None = None, execution_policy: ExecutionPolicy | None = None, embodiment: EmbodimentCapabilities | None = None, persistence: DuckPersistence | None = None, state: OrganismState | None = None):
        self.subject = subject
        self.config = config or DuckConfig()
        self.persistence = persistence
        self.services = services or NullServiceRegistry()
        self.reducer = CanonicalReducer()
        self.traces: list[CycleTrace] = []
        self.drives = drives or DriveSystem(state.drive_state if state else None)
        self.world_model = world_model or RuleWorldModel(state.world_model_state if state else None)
        self.procedures = procedures or ProcedureRegistry(state=state.procedural_state if state else None)
        self.metacognition = CalibrationMonitor(state=state.metacognitive_state if state else None)
        self.scheduler = CognitiveScheduler(drive_threshold=self.config.endogenous_drive_threshold, max_consecutive_endogenous=self.config.max_consecutive_endogenous_cycles)
        self.workspace = GlobalWorkspace()
        self.situation_constructor = SituationConstructor()
        self.attribution = AttributionBridge()
        self.memory_activation = SubjectMemoryActivation()
        self.action_generator = ActionGenerator()
        self.action_selector = ActionSelector(self.drives)
        self.executor = ActionExecutor(self.world_model, policy=execution_policy, embodiment=embodiment)
        if state is None:
            state = OrganismState(schema_version=self.config.schema_version, organism_id=organism_id or str(uuid4()), subject_id=subject.subject_id, drive_state=self.drives.drives, world_model_state=self.world_model.snapshot(), procedural_state=self.procedures.snapshot(), metacognitive_state=self.metacognition.snapshot(), config_fingerprint=self.config.fingerprint())
        if state.subject_id != subject.subject_id:
            raise ValueError("DUCK checkpoint subject_id does not match attached subject")
        self.state = state
        self.drives.drives = self.state.drive_state
        self.world_model.restore(self.state.world_model_state)
        self.procedures.restore(self.state.procedural_state)
        self.metacognition.restore(self.state.metacognitive_state)

    def current_state(self): return self.state
    def current_broadcast(self): return self.workspace.last_broadcast
    def set_services(self, services): self.services = services
    def ingest(self, event): self.scheduler.ingest(event)

    def _patch(self, domain, old_value, new_value, source, reason, evidence=()):
        return StatePatch(domain=domain,key=domain,old_value=old_value,new_value=new_value,source_module=source,reason=reason,evidence_refs=tuple(evidence),tick=self.state.tick,authorization_class="duck_internal")

    def _apply(self, patch, patches=None):
        self.reducer.apply(self.state, patch)
        if patches is not None: patches.append(patch)

    def add_commitment(self, commitment):
        if any(item.commitment_id == commitment.commitment_id for item in self.state.commitments): raise ValueError(f"duplicate commitment_id {commitment.commitment_id}")
        updated=deepcopy(self.state.commitments); updated.append(deepcopy(commitment))
        self._apply(self._patch("commitments",deepcopy(self.state.commitments),updated,"prospective_memory","adopt explicit prospective commitment",(commitment.commitment_id,)))
        if self.persistence is not None: self.persistence.save(self.state)

    def save(self):
        if self.persistence is None: raise RuntimeError("DUCK persistence is not configured")
        return self.persistence.save(self.state)

    @classmethod
    def load(cls, subject, persistence, **kwargs): return cls(subject,persistence=persistence,state=persistence.load(),**kwargs)

    def _memory_query(self, trigger):
        payload=trigger.payload
        return str(payload.get("observed_text") or payload.get("description") or payload.get("topic") or payload.get("unresolved_question") or "")

    def step(self):
        trigger=self.scheduler.next_event(self.state,self.drives.drives)
        if trigger is None: return None
        tick=self.state.tick; patches=[]
        pre_drives=deepcopy(self.state.drive_state)
        if self.config.enable_motivation:
            drive_changes=self.drives.step(); self._apply(self._patch("drive_state",pre_drives,deepcopy(self.drives.drives),"motivation","homeostatic drive update",(trigger.event_id,)),patches)
            old_goals=deepcopy(self.state.active_goals); updated_goals=self.drives.ensure_drive_goals(deepcopy(self.state.active_goals),tick=tick)
            self._apply(self._patch("active_goals",old_goals,updated_goals,"motivation","derive goals from persistent deficits",(trigger.event_id,)),patches)
            drive_items=self.drives.cognitive_items(tick=tick,subject_id=self.state.subject_id,threshold=self.config.drive_workspace_threshold)
        else: drive_changes={}; drive_items=[]

        old_situation=deepcopy(self.state.situation); situation_changes=self.situation_constructor.update(self.state.situation,trigger)
        self._apply(self._patch("situation",old_situation,deepcopy(self.state.situation),"situation","integrate event into current situation",(trigger.event_id,)),patches)
        attribution_frame, attribution_item=self.attribution.build(trigger,self.state,tick=tick)
        subject_payload=dict(trigger.payload); subject_payload["duck_attribution"]=attribution_frame.to_dict(); subject_payload["duck_event_id"]=trigger.event_id
        subject_result=self.subject.observe_event(subject_payload)
        event_item=CognitiveItem(item_id=f"event:{trigger.event_id}",tick=tick,kind="perception",source_module="perception",subject_id=self.state.subject_id,payload=dict(trigger.payload),confidence=trigger.confidence,salience=float(trigger.payload.get("salience",0.45)),self_relevance=max(float(trigger.payload.get("self_relevance",0.0)),attribution_frame.self_relevance),novelty=float(trigger.payload.get("novelty",0.25)),threat=float(trigger.payload.get("threat",0.0)),valence=float(trigger.payload.get("valence",0.0)),arousal=float(trigger.payload.get("arousal",0.0)),attribution_id=attribution_frame.attribution_id,provenance={"source":trigger.source,"event_id":trigger.event_id},canonical=False)

        items=[event_item,attribution_item]; items.extend(drive_items)
        if self.config.enable_memory_activation:
            items.extend(self.memory_activation.retrieve(self.subject,query=self._memory_query(trigger),now=trigger.timestamp,tick=tick,subject_id=self.state.subject_id,top_k=self.config.memory_retrieval_width))
        projection={"trigger":trigger.to_dict(),"attribution":attribution_frame.to_dict(),"situation":self.state.situation.to_dict(),"broadcast_history":self.state.working_memory[-3:],"active_goals":[goal.to_dict() for goal in self.state.active_goals if goal.status=="active"],"commitments":[item.to_dict() for item in self.state.commitments if item.status=="pending"],"drives":{name:drive.to_dict() for name,drive in sorted(self.drives.drives.items())},"subject":self.subject.snapshot()}
        service_items,service_errors=self.services.proposals(ServiceContext(tick=tick,subject_id=self.state.subject_id,purpose="workspace_candidates",projection=projection)); items.extend(service_items)
        broadcast=self.workspace.compete(items,tick=tick) if self.config.enable_workspace else None
        if broadcast is not None:
            updated_working=(list(self.state.working_memory)+[broadcast.winner.to_dict()])[-self.config.working_memory_limit:]
            self._apply(self._patch("working_memory",list(self.state.working_memory),updated_working,"workspace","global broadcast changes bounded working memory",(broadcast.winner.item_id,)),patches)

        actions=self.action_generator.generate(self.state,broadcast); actions.extend(self.procedures.candidates(self.state,broadcast)); by_id={a.action_id:a for a in actions}; actions=[by_id[k] for k in sorted(by_id)]
        context={"tick":tick,"subject_id":self.state.subject_id,"trigger":trigger.to_dict(),"broadcast":broadcast.to_dict() if broadcast else None,"situation":self.state.situation.to_dict(),"subject":self.subject.snapshot(),"confirmed":bool(trigger.payload.get("confirmed",False))}
        if self.config.enable_simulation: simulations=[self.world_model.simulate(action,context) for action in actions]
        else: simulations=[SimulationResult(action_id=a.action_id,predicted_world_effects=dict(a.expected_world_effects),predicted_self_effects=dict(a.expected_self_effects),confidence=0.25,provenance={"source":"simulation_lesion","action_type":a.action_type}) for a in actions]
        action,simulation,score,breakdown=self.action_selector.select(actions,simulations,self.state); intention=self.action_selector.commit(action,simulation,tick=tick,score=score,breakdown=breakdown)
        self._apply(self._patch("current_intention",self.state.current_intention,intention,"action_selector","serialized action commitment after simulation",(broadcast.winner.item_id,) if broadcast else ()),patches)
        execution=self.executor.execute(action,simulation,context); observed_world=execution.world_effects; observed_self=execution.self_effects
        if self.config.enable_motivation:
            post_drives=DriveSystem(deepcopy(self.state.drive_state)); applied_drives=post_drives.apply_effects(observed_self)
            if applied_drives:
                self._apply(self._patch("drive_state",deepcopy(self.state.drive_state),post_drives.drives,"executor","apply observed action consequences to regulatory drives",(intention.intention_id,)),patches); self.drives.drives=self.state.drive_state; self.action_selector=ActionSelector(self.drives)
        else: applied_drives={}
        updated_commitments=deepcopy(self.state.commitments); commitment_changed=False
        for item in updated_commitments:
            if execution.executed and action.action_type=="honor_commitment" and action.parameters.get("commitment_id")==item.commitment_id: item.status="completed"; commitment_changed=True
        if commitment_changed: self._apply(self._patch("commitments",deepcopy(self.state.commitments),updated_commitments,"executor","complete prospective commitment after observed execution",(intention.intention_id,)),patches)
        world_error=effect_error(simulation.predicted_world_effects,observed_world); self_error=effect_error(simulation.predicted_self_effects,observed_self)
        prediction=PredictionRecord(prediction_id=f"prediction:{tick}:{action.action_id}",intention_id=intention.intention_id,predicted_world_effects=dict(simulation.predicted_world_effects),predicted_self_effects=dict(simulation.predicted_self_effects),observed_world_effects=dict(observed_world),observed_self_effects=dict(observed_self),world_error=world_error,self_error=self_error)
        old_world=deepcopy(self.state.world_model_state); old_procedural=deepcopy(self.state.procedural_state); old_metacognitive=deepcopy(self.state.metacognitive_state)
        if self.config.enable_simulation: self.world_model.learn(action.action_type,world_error=world_error,self_error=self_error)
        self.procedures.learn(action,prediction_error=(world_error+self_error)/2.0); self.metacognition.observe(world_error=world_error,self_error=self_error,simulation_confidence=simulation.confidence)
        action_entry={"tick":tick,"intention":intention.to_dict(),"execution":execution.to_dict(),"outcome":{"world":observed_world,"self":observed_self,"drive_effects":applied_drives}}
        patch_specs=[("action_ledger",list(self.state.action_ledger),(list(self.state.action_ledger)+[action_entry])[-128:],"executor","record observed action outcome",(trigger.event_id,)),("prediction_ledger",list(self.state.prediction_ledger),(list(self.state.prediction_ledger)+[prediction.to_dict()])[-128:],"prediction","compare expected and observed world/self effects",(intention.intention_id,)),("world_model_state",old_world,self.world_model.snapshot(),"learning","persist learned world model",(prediction.prediction_id,)),("procedural_state",old_procedural,self.procedures.snapshot(),"learning","persist procedural confidence",(prediction.prediction_id,)),("metacognitive_state",old_metacognitive,self.metacognition.snapshot(),"learning","persist metacognitive calibration",(prediction.prediction_id,))]
        for spec in patch_specs: self._apply(self._patch(*spec),patches)
        self.subject.advance_time(1.0)
        for spec in [("tick",self.state.tick,self.state.tick+1,"scheduler","complete one serialized cognitive cycle",(trigger.event_id,)),("scheduler_state",dict(self.state.scheduler_state),self.scheduler.snapshot(),"scheduler","persist bounded endogenous scheduling state",())]: self._apply(self._patch(*spec),patches)
        trace=CycleTrace(tick=tick,trigger=trigger.to_dict(),situation_changes={**situation_changes,"attribution":attribution_frame.to_dict(),"subject_observation":subject_result},drive_changes=drive_changes,cognitive_items=tuple(item.to_dict() for item in items),broadcast=broadcast.to_dict() if broadcast else None,action_candidates=tuple(item.to_dict() for item in actions),simulations=tuple(item.to_dict() for item in simulations),selected_intention=intention.to_dict(),outcome={"execution":execution.to_dict(),"world":observed_world,"self":observed_self,"drive_effects":applied_drives},prediction=prediction.to_dict(),patches=tuple(item.to_dict() for item in patches),service_errors=tuple(service_errors),service_proposals=tuple(item.to_dict() for item in service_items))
        self.traces.append(trace)
        if self.persistence is not None: self.persistence.append_trace(trace); self.persistence.save(self.state)
        return trace

    def run_until_idle(self,*,max_cycles=None):
        limit=self.config.max_run_until_idle_cycles if max_cycles is None else int(max_cycles); traces=[]
        for _ in range(max(0,limit)):
            trace=self.step()
            if trace is None: break
            traces.append(trace)
        return traces

    def metacognitive_report(self):
        return {"subject_id":self.state.subject_id,"organism_id":self.state.organism_id,"tick":self.state.tick,"workspace_priority":self.workspace.last_broadcast.priority if self.workspace.last_broadcast else 0.0,"drive_urgency":{name:drive.urgency for name,drive in sorted(self.drives.drives.items())},"latest_prediction":self.state.prediction_ledger[-1] if self.state.prediction_ledger else None,"calibration":self.metacognition.report(),"world_model_reliability":dict(sorted(self.world_model.reliability.items())),"service_count":len(self.services.services),"lesions":{"motivation":not self.config.enable_motivation,"memory_activation":not self.config.enable_memory_activation,"workspace":not self.config.enable_workspace,"simulation":not self.config.enable_simulation}}
