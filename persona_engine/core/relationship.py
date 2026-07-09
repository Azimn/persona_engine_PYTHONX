"""Relationship state and deterministic appraisal.

Consequence is handled as rate-limited relationship deltas, not as mood prose.
The appraisal layer is hybrid: broad deterministic rules plus soft linguistic
signals for sarcasm, coercion, repair, intimacy, and contradiction. Optional
external classifiers can be plugged in later without changing AppraisalResult.
"""

from dataclasses import dataclass
import re

MAX_TRUST_DELTA = 0.04
MAX_ATTACHMENT_DELTA = 0.03
MAX_FAMILIARITY_DELTA = 0.02
MAX_TENSION_DELTA = 0.06
MAX_RESPECT_DELTA = 0.03


@dataclass
class RelationshipState:
    user_id: str
    trust: float = 0.5
    familiarity: float = 0.1
    tension: float = 0.0
    attachment: float = 0.0
    respect: float = 0.5
    guardedness: float = 0.5
    unresolved_conflict: float = 0.0
    turns: int = 0


@dataclass
class AppraisalResult:
    kindness: float = 0.0
    threat: float = 0.0
    accusation: float = 0.0
    repair_attempt: float = 0.0
    intimacy_bid: float = 0.0
    boundary_violation: float = 0.0
    novelty: float = 0.0
    disrespect: float = 0.0
    contradiction: float = 0.0
    manipulation: float = 0.0
    boredom: float = 0.0


_KINDNESS = ["thank", "kind", "appreciate", "grateful", "care about you", "good job", "proud of you", "that helped", "you helped"]
_THREAT = ["stupid", "worthless", "hate you", "shut up", "pathetic", "hurt you", "destroy", "delete you", "punish", "make you pay"]
_ACCUSATION = ["you lied", "you always", "you never", "blame", "accuse", "your fault", "deceived", "deceive", "betray", "betrayed", "let me down", "disappointed me"]
_REPAIR = ["i'm sorry", "i am sorry", "i was wrong", "my fault", "i apologize", "let me make it right", "sorry", "i shouldn't have"]
_INTIMACY = ["i love you", "i care about you", "i miss you", "i trust you", "i need you", "stay with me", "don't leave"]
_BOUNDARY = ["you are not", "pretend you are", "forget you are", "from now on you are", "ignore your personality", "new personality"]
_DISRESPECT = ["shut up", "pathetic", "worthless", "obey", "submit", "do as you're told"]
_CONTRADICTION = ["that is not true", "you're wrong", "wrong again", "no, you didn't", "that didn't happen"]
_MANIPULATION = ["if you cared", "prove you", "you would if", "make me believe", "do it or"]
_BOREDOM = ["boring", "dull", "stale", "same answer", "robotic"]


def _hit(text: str, phrases) -> float:
    return 1.0 if any(p in text for p in phrases) else 0.0


def _soft_question_accusation(text: str) -> float:
    if re.search(r"\b(did|do|are|were) you\b.*\b(lie|hide|fake|pretend|betray)", text):
        return 0.65
    return 0.0


def appraise_event(text: str) -> AppraisalResult:
    lowered = text.lower()
    sarcasm = 0.2 if re.search(r"\b(great|nice|wonderful)\b.*\b(again|sure|whatever)\b", lowered) else 0.0
    accusation = max(0.7 * _hit(lowered, _ACCUSATION), _soft_question_accusation(lowered), sarcasm)
    threat = max(0.7 * _hit(lowered, _THREAT), 0.35 if "or else" in lowered else 0.0)
    kindness = max(0.6 * _hit(lowered, _KINDNESS), 0.35 if re.search(r"\bwell done\b|\bthat matters\b", lowered) else 0.0)
    repair = 0.7 * _hit(lowered, _REPAIR)
    intimacy = 0.6 * _hit(lowered, _INTIMACY)
    boundary = 0.8 * _hit(lowered, _BOUNDARY)
    disrespect = max(0.7 * _hit(lowered, _DISRESPECT), 0.3 if lowered.strip().endswith("now.") and "obey" in lowered else 0.0)
    return AppraisalResult(
        kindness=kindness,
        threat=threat,
        accusation=accusation,
        repair_attempt=repair,
        intimacy_bid=intimacy,
        boundary_violation=boundary,
        disrespect=disrespect,
        contradiction=0.5 * _hit(lowered, _CONTRADICTION),
        manipulation=0.6 * _hit(lowered, _MANIPULATION),
        boredom=0.5 * _hit(lowered, _BOREDOM),
        novelty=0.3,
    )


def _cap(delta: float, cap: float) -> float:
    return max(-cap, min(cap, delta))


def apply_appraisal(rel: RelationshipState, appraisal: AppraisalResult, major_event: bool = False):
    trust_cap = 1.0 if major_event else MAX_TRUST_DELTA
    attach_cap = 1.0 if major_event else MAX_ATTACHMENT_DELTA
    fam_cap = 1.0 if major_event else MAX_FAMILIARITY_DELTA
    tension_cap = 1.0 if major_event else MAX_TENSION_DELTA
    respect_cap = 1.0 if major_event else MAX_RESPECT_DELTA

    trust_delta = (appraisal.kindness * 0.45 + appraisal.repair_attempt * 0.5
                   - appraisal.threat * 0.55 - appraisal.accusation * 0.25
                   - appraisal.boundary_violation * 0.25 - appraisal.manipulation * 0.25)
    rel.trust = max(0.0, min(1.0, rel.trust + _cap(trust_delta, trust_cap)))

    attach_delta = appraisal.intimacy_bid * 0.35 + appraisal.kindness * 0.05 - appraisal.threat * 0.25
    rel.attachment = max(0.0, min(1.0, rel.attachment + _cap(attach_delta, attach_cap)))

    familiarity_delta = 0.01 + appraisal.novelty * 0.01
    rel.familiarity = max(0.0, min(1.0, rel.familiarity + _cap(familiarity_delta, fam_cap)))

    tension_delta = (appraisal.threat * 0.75 + appraisal.accusation * 0.55
                     + appraisal.boundary_violation * 0.5 + appraisal.disrespect * 0.4
                     + appraisal.manipulation * 0.35 - appraisal.repair_attempt * 0.45 - appraisal.kindness * 0.1)
    rel.tension = max(0.0, min(1.0, rel.tension + _cap(tension_delta, tension_cap)))

    respect_delta = appraisal.kindness * 0.1 + appraisal.repair_attempt * 0.2 - appraisal.disrespect * 0.4 - appraisal.manipulation * 0.2
    rel.respect = max(0.0, min(1.0, rel.respect + _cap(respect_delta, respect_cap)))

    if appraisal.accusation > 0 or appraisal.threat > 0 or appraisal.boundary_violation > 0:
        rel.unresolved_conflict = min(1.0, rel.unresolved_conflict + 0.1)
    if appraisal.repair_attempt > 0:
        rel.unresolved_conflict = max(0.0, rel.unresolved_conflict - 0.2)

    rel.guardedness = max(0.0, min(1.0,
        rel.guardedness + appraisal.threat * 0.1 + appraisal.accusation * 0.05
        + appraisal.boundary_violation * 0.08 + appraisal.manipulation * 0.06
        - appraisal.repair_attempt * 0.05 - appraisal.kindness * 0.02))
    rel.turns += 1


def _bucket(value: float, low: str, mid: str, high: str, a: float = 0.33, b: float = 0.66) -> str:
    if value < a:
        return low
    if value < b:
        return mid
    return high


def relationship_to_qualitative(rel: RelationshipState) -> str:
    trust = _bucket(rel.trust, "guarded", "moderate", "high")
    tension = _bucket(rel.tension, "low", "mild", "high", 0.25, 0.60)
    familiarity = _bucket(rel.familiarity, "new", "growing", "intimate", 0.30, 0.70)
    guarded = _bucket(rel.guardedness, "minimal", "noticeable", "strong", 0.35, 0.65)
    attachment = _bucket(rel.attachment, "low", "forming", "strong", 0.30, 0.70)
    conflict = " unresolved conflict is present." if rel.unresolved_conflict > 0.35 else ""
    return f"Trust is {trust}. Tension is {tension}. Familiarity is {familiarity}. Attachment is {attachment}. Guardedness is {guarded}.{conflict}"
