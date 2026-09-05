"""DUCK v0.1 organism loop over a persistent Wayfarer subject."""
from __future__ import annotations
from dataclasses import dataclass
import hashlib,json
from uuid import uuid4
from .action import ActionGenerator,ActionSelector
from .attribution import AttributionBridge
from .executor import ActionExecutor,EmbodimentCapabilities,ExecutionPolicy
from .memory_bridge import SubjectMemoryActivation
from .metacognition import CalibrationMonitor
from .motivation import DriveSystem
from .persistence import DuckPersistence
from .procedures import ProcedureRegistry
from .reducer import CanonicalReducer
from .scheduler import CognitiveScheduler
from .services import NullServiceRegistry,ServiceContext,ServiceRegistry
from .simulation import RuleWorldModel,SimulationResult,effect_error
from .situation import SituationConstructor
from .subject_adapter import SubjectPort
from .types import CognitiveItem,CycleTrace,ExternalEvent,OrganismState,PredictionRecord,ProspectiveCommitment,StatePatch
from .workspace import GlobalWorkspace

@dataclass(frozen=True)
class DuckConfig:
    schema_version:str='duck-organism-v0.1'; working_memory_limit:int=8; drive_workspace_threshold:float=.10; endogenous_drive_threshold:float=.22
    max_consecutive_endogenous_cycles:int=4; max_run_until_idle_cycles:int=8; memory_retrieval_width:int=3
    enable_motivation:bool=True; enable_memory_activation:bool=True; enable_workspace:bool=True; enable_simulation:bool=True
    def fingerprint(self): return hashlib.sha256(json.dumps(self.__dict__,sort_keys=True,separators=(',',':')).encode()).hexdigest()

class DuckOrganism:
    def __init__(self,subject:SubjectPort,*,organism_id=None,config=None,drives=None,world_model=None,services=None,procedures=None,execution_policy=None,embodiment=None,persistence=None,state=None):
        self.subject=subject; self.config=config or DuckConfig(); self.persistence=persistence; self.services=services or NullServiceRegistry(); self.reducer=CanonicalReducer(); self.traces=[]
        self.drives=drives or DriveSystem(state.drive_state if state else None)
        self.world_model=world_model or RuleWorldModel(state.world_model_state if state else None)
        self.procedures=procedures or ProcedureRegistry(state=state.procedural_state if state else None)
        self.metacognition=CalibrationMonitor(state=state.metacognitive_state if state else None)
        self.scheduler=CognitiveScheduler(drive_threshold=self.config.endogenous_drive_threshold,max_consecutive_endogenous=self.config.max_consecutive_endogenous_cycles)
        self.workspace=GlobalWorkspace(); self.situation_constructor=SituationConstructor(); self.attribution=AttributionBridge(); self.memory_activation=SubjectMemoryActivation(); self.action_generator=ActionGenerator(); self.action_selector=ActionSelector(self.drives)
        self.executor=ActionExecutor(self.world_model,policy=execution_policy,embodiment=embodiment)
        if state is None:
            state=OrganismState(schema_version=self.config.schema_version,organism_id=organism_id or str(uuid4()),subject_id=subject.subject_id,drive_state=self.drives.drives,
                                world_model_state=self.world_model.snapshot(),procedural_state=self.procedures.snapshot(),metacognitive_state=self.metacognition.snapshot(),config_fingerprint=self.config.fingerprint())
        if state.subject_id!=subject.subject_id: raise ValueError('DUCK checkpoint subject_id does not match attached subject')
        self.state=state; self.drives.drives=self.state.drive_state; self.world_model.restore(self.state.world_model_state); self.procedures.restore(self.state.procedural_state); self.metacognition.restore(self.state.metacognitive_state)
    def current_state(self): return self.state
    def current_broadcast(self): return self.workspace.last_broadcast
    def set_services(self,services): self.services=services
    def ingest(self,event): self.scheduler.ingest(event)
    def add_commitment(self,commitment):
        if any(i.commitment_id==commitment.commitment_id for i in self.state.commitments): raise ValueError(f'duplicate commitment_id {commitment.commitment_id}')
        self.state.commitments.append(commitment)
    def save(self):
        if self.persistence is None: raise RuntimeError('DUCK persistence is not configured')
        return self.persistence.save(self.state)
    @classmethod
    def load(cls,subject,persistence,**kwargs): return cls(subject,persistence=persistence,state=persistence.load(),**kwargs)
    def _patch(self,domain,old_value,new_value,source,reason,evidence=()): return StatePatch(domain,domain,old_value,new_value,source,reason,evidence,self.state.tick,'duck_internal')
    def _apply(self,patch,patches): self.reducer.apply(self.state,patch); patches.append(patch)
    def _memory_query(self,t):
        p=t.payload; return str(p.get('observed_text') or p.get('description') or p.get('topic') or p.get('unresolved_question') or '').strip()
    def step(self,*,budget_ms=None):
        del budget_ms
        trigger=self.scheduler.next_trigger(self.state,self.drives,allow_drive_triggers=self.config.enable_motivation)
        if trigger is None: return None
        tick=self.state.tick; patches=[]
        situation_changes,event_item=self.situation_constructor.update(self.state.situation,trigger,tick=tick,subject_id=self.state.subject_id)
        attribution_frame=self.attribution.attribute(trigger,subject_id=self.state.subject_id,tick=tick); attribution_item=self.attribution.as_cognitive_item(attribution_frame,tick=tick,subject_id=self.state.subject_id)
        subject_result=self.subject.observe_event(trigger.payload)
        if self.config.enable_motivation:
            drive_changes=self.drives.step(); self.drives.ensure_drive_goals(self.state.active_goals,tick=tick); drive_items=self.drives.cognitive_items(tick=tick,subject_id=self.state.subject_id,threshold=self.config.drive_workspace_threshold)
        else: drive_changes={'lesion':{'motivation':1.0}}; drive_items=[]
        items=[event_item,attribution_item]+drive_items
        if self.config.enable_memory_activation: items+=self.memory_activation.retrieve(self.subject,query=self._memory_query(trigger),now=trigger.timestamp,tick=tick,subject_id=self.state.subject_id,top_k=self.config.memory_retrieval_width)
        projection={'trigger':trigger.to_dict(),'attribution':attribution_frame.to_dict(),'situation':self.state.situation.to_dict(),'broadcast_history':self.state.working_memory[-3:],
                    'active_goals':[g.to_dict() for g in self.state.active_goals if g.status=='active'],'commitments':[c.to_dict() for c in self.state.commitments if c.status=='pending'],
                    'drives':{n:d.to_dict() for n,d in sorted(self.drives.drives.items())},'subject':self.subject.snapshot()}
        service_items,service_errors=self.services.proposals(ServiceContext(tick,self.state.subject_id,'workspace_candidates',projection)); items+=service_items
        broadcast=self.workspace.compete(items,tick=tick) if self.config.enable_workspace else None
        if broadcast:
            new=(list(self.state.working_memory)+[broadcast.winner.to_dict()])[-self.config.working_memory_limit:]
            self._apply(self._patch('working_memory',list(self.state.working_memory),new,'workspace','global broadcast changes bounded working memory',(broadcast.winner.item_id,)),patches)
        actions=self.action_generator.generate(self.state,broadcast)+self.procedures.candidates(self.state,broadcast); actions=[{a.action_id:a for a in actions}[k] for k in sorted({a.action_id:a for a in actions})]
        context={'tick':tick,'situation':self.state.situation.to_dict(),'subject':self.subject.snapshot(),'confirmed':bool(trigger.payload.get('confirmed',False))}
        simulations=[self.world_model.simulate(a,context) for a in actions] if self.config.enable_simulation else [SimulationResult(a.action_id,dict(a.expected_world_effects),dict(a.expected_self_effects),.25,{'source':'simulation_lesion','action_type':a.action_type}) for a in actions]
        action,simulation,score,breakdown=self.action_selector.select(actions,simulations,self.state); intention=self.action_selector.commit(action,simulation,tick=tick,score=score,breakdown=breakdown)
        self._apply(self._patch('current_intention',self.state.current_intention,intention,'action_selector','serialized action commitment after simulation',(broadcast.winner.item_id,) if broadcast else ()),patches)
        execution=self.executor.execute(action,simulation,context); observed_world,observed_self=execution.world_effects,execution.self_effects
        applied_drives=self.drives.apply_effects(observed_self) if self.config.enable_motivation else {}
        for c in self.state.commitments:
            if execution.executed and action.action_type=='honor_commitment' and action.parameters.get('commitment_id')==c.commitment_id: c.status='completed'
        world_error=effect_error(simulation.predicted_world_effects,observed_world); self_error=effect_error(simulation.predicted_self_effects,observed_self)
        prediction=PredictionRecord(f'prediction:{tick}:{action.action_id}',intention.intention_id,dict(simulation.predicted_world_effects),dict(simulation.predicted_self_effects),dict(observed_world),dict(observed_self),world_error,self_error)
        old_world=dict(self.state.world_model_state); old_proc=dict(self.state.procedural_state); old_meta=dict(self.state.metacognitive_state)
        if self.config.enable_simulation: self.world_model.learn(action.action_type,world_error=world_error,self_error=self_error)
        self.procedures.learn(action,prediction_error=(world_error+self_error)/2); self.metacognition.observe(world_error=world_error,self_error=self_error,simulation_confidence=simulation.confidence)
        action_entry={'tick':tick,'intention':intention.to_dict(),'execution':execution.to_dict(),'outcome':{'world':observed_world,'self':observed_self,'drive_effects':applied_drives}}
        patch_specs=[('action_ledger',list(self.state.action_ledger),(list(self.state.action_ledger)+[action_entry])[-128:],'executor','record observed action outcome',(trigger.event_id,)),
                     ('prediction_ledger',list(self.state.prediction_ledger),(list(self.state.prediction_ledger)+[prediction.to_dict()])[-128:],'prediction','compare expected and observed world/self effects',(intention.intention_id,)),
                     ('world_model_state',old_world,self.world_model.snapshot(),'learning','persist learned world model',()),('procedural_state',old_proc,self.procedures.snapshot(),'learning','persist procedural confidence',()),
                     ('metacognitive_state',old_meta,self.metacognition.snapshot(),'learning','persist metacognitive calibration',())]
        for spec in patch_specs: self._apply(self._patch(*spec),patches)
        self.subject.advance_time(1.0)
        for spec in [('tick',self.state.tick,self.state.tick+1,'scheduler','complete one serialized cognitive cycle',(trigger.event_id,)),('scheduler_state',dict(self.state.scheduler_state),self.scheduler.snapshot(),'scheduler','persist bounded endogenous scheduling state',())]: self._apply(self._patch(*spec),patches)
        trace=CycleTrace(tick,trigger.to_dict(),{**situation_changes,'attribution':attribution_frame.to_dict(),'subject_observation':subject_result},drive_changes,tuple(i.to_dict() for i in items),broadcast.to_dict() if broadcast else None,
                         tuple(a.to_dict() for a in actions),tuple(s.to_dict() for s in simulations),intention.to_dict(),{'execution':execution.to_dict(),'world':observed_world,'self':observed_self,'drive_effects':applied_drives},prediction.to_dict(),tuple(p.to_dict() for p in patches),tuple(service_errors),tuple(i.to_dict() for i in service_items))
        self.traces.append(trace)
        if self.persistence: self.persistence.append_trace(trace); self.persistence.save(self.state)
        return trace
    def run_until_idle(self,*,max_cycles=None):
        out=[]; limit=self.config.max_run_until_idle_cycles if max_cycles is None else int(max_cycles)
        for _ in range(max(0,limit)):
            t=self.step()
            if t is None: break
            out.append(t)
        return out
    def metacognitive_report(self):
        return {'subject_id':self.state.subject_id,'organism_id':self.state.organism_id,'tick':self.state.tick,'workspace_priority':self.workspace.last_broadcast.priority if self.workspace.last_broadcast else 0.0,
                'drive_urgency':{n:d.urgency for n,d in sorted(self.drives.drives.items())},'latest_prediction':self.state.prediction_ledger[-1] if self.state.prediction_ledger else None,'calibration':self.metacognition.report(),
                'world_model_reliability':dict(sorted(self.world_model.reliability.items())),'service_count':len(self.services.services),'lesions':{'motivation':not self.config.enable_motivation,'memory_activation':not self.config.enable_memory_activation,'workspace':not self.config.enable_workspace,'simulation':not self.config.enable_simulation}}
