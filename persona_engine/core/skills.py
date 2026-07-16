"""Small persistent procedural competence store, distinct from habits."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
from typing import Sequence


@dataclass
class SkillTrace:
    schema_version: int
    skill_id: str
    name: str
    action_kind: str
    communicative_function: str | None
    context_tags: tuple[str, ...]
    attempts: int = 0
    supported_successes: int = 0
    inferred_successes: int = 0
    failures: int = 0
    competence: float = .10
    automaticity: float = 0.0
    generalizability: float = .10
    expected_effort: float = .80
    identity_compatibility: float = 1.0
    maturity: float = 0.0
    state: str = "candidate"
    last_attempt_tick: int = 0
    source_episode_ids: tuple[str, ...] = ()

    def to_dict(self): return asdict(self)
    @classmethod
    def from_dict(cls, data):
        raw = dict(data); raw["context_tags"] = tuple(raw.get("context_tags", ())); raw["source_episode_ids"] = tuple(raw.get("source_episode_ids", ()))
        return cls(**raw)


@dataclass(frozen=True)
class SkillForecast:
    skill_id: str
    effective_competence: float
    context_match: float
    expected_effort: float
    misapplication_risk: float


class SkillStore:
    MAX_SKILLS = 128

    def __init__(self, skills: Sequence[SkillTrace] = ()):
        self.skills = {item.skill_id: item for item in skills}

    def get_or_create(self, name: str, action_kind: str, communicative_function: str | None,
                      context_tags: Sequence[str], tick: int) -> SkillTrace | None:
        key = f"{name}|{action_kind}|{communicative_function}|{'|'.join(sorted(context_tags))}".encode()
        sid = "skill_" + hashlib.blake2b(key, digest_size=8).hexdigest()
        if sid in self.skills: return self.skills[sid]
        if len(self.skills) >= self.MAX_SKILLS: return None
        self.skills[sid] = SkillTrace(1, sid, name, action_kind, communicative_function,
                                      tuple(sorted(set(context_tags))), last_attempt_tick=tick)
        return self.skills[sid]

    def forecast(self, skill: SkillTrace, context_tags: Sequence[str], fatigue: float = 0.0) -> SkillForecast:
        expected = set(skill.context_tags); actual = set(context_tags)
        match = len(expected & actual) / max(1, len(expected | actual))
        quality = max(0.0, min(1.0, skill.competence + .18 * skill.automaticity * match
                               - .12 * skill.automaticity * (1.0 - match) - .15 * fatigue))
        return SkillForecast(skill.skill_id, quality, match, skill.expected_effort, skill.automaticity * (1.0 - match))

    def update(self, skill_id: str, *, evidence_tier: str, succeeded: bool, tick: int, episode_id: str):
        skill = self.skills.get(skill_id)
        if not skill: return None
        skill.attempts += 1; skill.last_attempt_tick = tick
        delta = .04 if evidence_tier == "objective" else .015
        if succeeded:
            if evidence_tier == "objective": skill.supported_successes += 1
            else: skill.inferred_successes += 1
            skill.competence = min(1.0, skill.competence + delta)
            skill.automaticity = min(1.0, skill.automaticity + delta * .5)
            skill.expected_effort = max(0.05, skill.expected_effort - delta * .5)
        else:
            skill.failures += 1; skill.competence = max(0.0, skill.competence - delta * .5)
        skill.maturity = min(1.0, skill.attempts / 20.0)
        skill.state = "mature" if skill.maturity >= .8 and skill.competence >= .75 else "reliable" if skill.competence >= .6 else "practicing" if skill.attempts >= 3 else "candidate"
        skill.source_episode_ids = tuple(dict.fromkeys((*skill.source_episode_ids, episode_id)))[-32:]
        return skill

    def to_list(self): return [item.to_dict() for item in self.skills.values()]
    @classmethod
    def from_list(cls, data): return cls([SkillTrace.from_dict(item) for item in (data or ())])
