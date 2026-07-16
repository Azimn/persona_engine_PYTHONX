"""Bounded prediction, episode, and relationship-expectation records."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
from statistics import fmean
from typing import Any, Mapping, Sequence


EXPECTATION_VALUES = ("unlikely", "uncertain", "sometimes", "usually", "strongly_expected")


def stable_id(prefix: str, *parts: object) -> str:
    raw=json.dumps([str(item) for item in parts],separators=(",",":")).encode()
    return prefix+"_"+hashlib.blake2b(raw,digest_size=8).hexdigest()


@dataclass(frozen=True)
class ActionExpectation:
    schema_version:int; expectation_id:str; tick:int; decision_id:str; context_signature:str
    predicted_objective_success:float; predicted_subjective_satisfaction:float
    predicted_relationship_effect:float; predicted_identity_compatibility:float
    predicted_effort:float; predicted_social_appropriateness:float; predicted_information_gain:float
    selected_skill_id:str|None; evidence_ids:tuple[str,...]
    def to_dict(self):return asdict(self)


@dataclass(frozen=True)
class OutcomeVector:
    schema_version:int; outcome_id:str; completion_id:str|None; decision_id:str; evidence_tier:str
    objective_success:float; subjective_satisfaction:float; relationship_effect:float
    identity_compatibility:float; effort_cost:float; social_appropriateness:float
    information_gain:float; uncertainty:float; evidence_ids:tuple[str,...]
    def to_dict(self):return asdict(self)


@dataclass(frozen=True)
class PredictionError:
    schema_version:int; error_id:str; expectation_id:str; outcome_id:str; objective_error:float
    satisfaction_error:float; relationship_error:float; effort_error:float
    appropriateness_error:float; information_error:float; total_surprise:float
    def to_dict(self):return asdict(self)


@dataclass(frozen=True)
class DevelopmentEpisode:
    schema_version:int; episode_id:str; tick:int; context_signature:str; decision_id:str
    synthesis_id:str; intention_id:str|None; action_kind:str; communicative_function:str|None
    selected_skill_id:str|None; selected_habit_id:str|None; active_interpretation_ids:tuple[str,...]
    retrieved_memory_ids:tuple[str,...]; expectation_id:str; outcome_id:str; prediction_error_id:str
    world_event_ids:tuple[str,...]; subjective_experience_ids:tuple[str,...]; terminal_status:str
    def to_dict(self):return asdict(self)


@dataclass
class RelationshipExpectation:
    key:str; value:str="uncertain"; confidence:float=0.0; supporting_episode_ids:tuple[str,...]=()
    distinct_days:tuple[int,...]=(); violations:int=0
    def to_dict(self):return asdict(self)
    @classmethod
    def from_dict(cls,data):
        raw=dict(data);raw["supporting_episode_ids"]=tuple(raw.get("supporting_episode_ids",()));raw["distinct_days"]=tuple(raw.get("distinct_days",()))
        return cls(**raw)


class RelationshipExpectationStore:
    MAX_EXPECTATIONS=32
    def __init__(self,items:Sequence[RelationshipExpectation]=()):self.items={item.key:item for item in items}
    def observe(self,key:str,episode_id:str,day:int,supported:bool):
        item=self.items.get(key)
        if item is None:
            if len(self.items)>=self.MAX_EXPECTATIONS:return None
            item=RelationshipExpectation(key);self.items[key]=item
        prior_value = item.value
        if supported:
            item.supporting_episode_ids=tuple(dict.fromkeys((*item.supporting_episode_ids,episode_id)))[-32:]
            item.distinct_days=tuple(sorted(set((*item.distinct_days,int(day)))))[-32:]
            item.confidence=min(1.0,item.confidence+.12)
        else:
            item.violations+=1;item.confidence=max(0.0,item.confidence-.10)
        count=len(item.supporting_episode_ids)
        item.value="usually" if (
            count>=3 and len(item.distinct_days)>=2
            and (item.confidence>=.65 or (prior_value=="usually" and item.confidence>=.50))
        ) else "sometimes" if count>=2 else "uncertain"
        return item
    def to_list(self):return [item.to_dict() for item in self.items.values()]
    @classmethod
    def from_list(cls,data):return cls([RelationshipExpectation.from_dict(item) for item in (data or ())])


class DevelopmentEpisodeStore:
    MAX_EPISODES=512
    def __init__(self,episodes:Sequence[DevelopmentEpisode]=()):self.episodes=list(episodes)[-self.MAX_EPISODES:]
    def add(self,item:DevelopmentEpisode):
        if not any(e.episode_id==item.episode_id for e in self.episodes):self.episodes=[*self.episodes,item][-self.MAX_EPISODES:]
        return item
    def to_list(self):return [item.to_dict() for item in self.episodes]
    @classmethod
    def from_list(cls,data):
        fields=DevelopmentEpisode.__dataclass_fields__
        items=[]
        for value in data or ():
            raw={k:value[k] for k in fields if k in value}
            for key in ("active_interpretation_ids","retrieved_memory_ids","world_event_ids","subjective_experience_ids"):raw[key]=tuple(raw.get(key,()))
            items.append(DevelopmentEpisode(**raw))
        return cls(items)


def build_episode(*,tick:int,decision,synthesis,active_interpretation_ids=(),retrieved_memory_ids=(),world_event_ids=(),subjective_experience_ids=(),day:int=0):
    context=stable_id("context",decision.action_kind,decision.communicative_function,day%7)
    expectation=ActionExpectation(1,stable_id("expectation",decision.decision_id),tick,decision.decision_id,context,.55,.5,0,.9,.5,.6,.4,getattr(decision,"selected_skill_id",None),tuple(retrieved_memory_ids))
    outcome=OutcomeVector(1,stable_id("outcome",decision.decision_id,tick),None,decision.decision_id,"uncertain",.5,.5,0,.9,.5,.5,.4,.6,tuple(world_event_ids))
    errors=(outcome.objective_success-expectation.predicted_objective_success,outcome.subjective_satisfaction-expectation.predicted_subjective_satisfaction,outcome.relationship_effect-expectation.predicted_relationship_effect,outcome.effort_cost-expectation.predicted_effort,outcome.social_appropriateness-expectation.predicted_social_appropriateness,outcome.information_gain-expectation.predicted_information_gain)
    prediction=PredictionError(1,stable_id("prediction_error",expectation.expectation_id,outcome.outcome_id),expectation.expectation_id,outcome.outcome_id,*errors,round(fmean(abs(x) for x in errors),6))
    episode=DevelopmentEpisode(1,stable_id("development_episode",decision.decision_id,tick),tick,context,decision.decision_id,synthesis.synthesis_id,decision.intention_id,decision.action_kind,decision.communicative_function,getattr(decision,"selected_skill_id",None),decision.selected_habit_id,tuple(active_interpretation_ids),tuple(retrieved_memory_ids),expectation.expectation_id,outcome.outcome_id,prediction.error_id,tuple(world_event_ids),tuple(subjective_experience_ids),"pending")
    return expectation,outcome,prediction,episode
