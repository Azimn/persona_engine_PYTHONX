"""Relationship-specific structured interaction rituals."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
from typing import Sequence


@dataclass
class DyadicRitual:
    schema_version: int
    ritual_id: str
    relationship_id: str
    trigger_pattern: str
    response_action_kind: str
    communicative_function: str | None
    performance_tendency_id: str | None
    strength: float
    repetitions: int
    successful_repetitions: int
    last_used_tick: int
    context_tags: tuple[str, ...]
    evidence_ids: tuple[str, ...]
    state: str

    def to_dict(self): return asdict(self)
    @classmethod
    def from_dict(cls, data):
        raw=dict(data); raw["context_tags"]=tuple(raw.get("context_tags",())); raw["evidence_ids"]=tuple(raw.get("evidence_ids",()))
        return cls(**raw)


class DyadicRitualStore:
    MAX_RITUALS = 32

    def __init__(self, rituals: Sequence[DyadicRitual] = ()):
        self.rituals = list(rituals)[:self.MAX_RITUALS]

    def observe(self, relationship_id: str, trigger_pattern: str, action_kind: str,
                communicative_function: str | None, tick: int, evidence_id: str, success: bool = True):
        key=f"{relationship_id}|{trigger_pattern}|{action_kind}|{communicative_function}".encode()
        rid="ritual_"+hashlib.blake2b(key,digest_size=8).hexdigest()
        item=next((r for r in self.rituals if r.ritual_id==rid),None)
        if item is None:
            if len(self.rituals)>=self.MAX_RITUALS:return None
            item=DyadicRitual(1,rid,relationship_id,trigger_pattern,action_kind,communicative_function,None,.1,0,0,tick,(trigger_pattern,),(),"candidate")
            self.rituals.append(item)
        item.repetitions+=1; item.successful_repetitions+=int(success); item.last_used_tick=tick
        item.strength=min(1.0,item.strength+(.04 if success else .01)); item.evidence_ids=tuple(dict.fromkeys((*item.evidence_ids,evidence_id)))[-24:]
        item.state="supported" if item.repetitions>=3 else "candidate"
        return item

    def to_list(self):return [item.to_dict() for item in self.rituals]
    @classmethod
    def from_list(cls,data):return cls([DyadicRitual.from_dict(item) for item in (data or ())])
