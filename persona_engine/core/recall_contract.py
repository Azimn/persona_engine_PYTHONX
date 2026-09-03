"""Noncanonical realization duties derived from already-selected recall evidence.

This projection cannot retrieve, create memory, or establish a world fact. An
available topic record need not answer every attribute question. The duty is to
use/acknowledge the supplied evidence instead of silently denying its existence.
"""
from dataclasses import dataclass
import re

from .cold_biography import explicit_recall_request, grounded_recall_match


@dataclass(frozen=True)
class RecallContract:
    active: bool = False
    evidence_status: str = 'not_requested'
    evidence_ids: tuple[str, ...] = ()
    authority: str = 'selected_evidence_not_world_truth'
    reported_speaker: str = 'source_typed'


def memory_field(memory, key, default=None):
    return memory.get(key, default) if isinstance(memory, dict) else getattr(memory, key, default)


def recall_contract(query, memories):
    if not explicit_recall_request(query):
        return RecallContract()
    selected = [m for m in memories if grounded_recall_match(query, memory_field(m, 'content', ''))]
    user_statements = selected and all(getattr(memory_field(m,'source'), 'value', memory_field(m,'source')) == 'user_told' for m in selected)
    return RecallContract(True, 'available' if selected else 'unavailable',
                          tuple(str(memory_field(m, 'id', '')) for m in selected),
                          reported_speaker='current_interlocutor' if user_statements else 'source_typed')


_DENIAL = re.compile(
    r"\b(?:i (?:do not|don't|cannot|can't) (?:recall|remember)|"
    r"i have no (?:record|memory)|you (?:did not|didn't|never|haven't|have not) "
    r"(?:say|tell|mention|specify|said|told|mentioned|specified))\b", re.I)
_ACKNOWLEDGMENT = re.compile(
    r"(?:^|[.!?;]\s*|\bbut\s+)(?:you (?:said|told me|mentioned|described)|i (?:recall|remember|heard)|"
    r"(?:my|the) (?:record|note) (?:says|shows|contains))\b", re.I)


def recall_violations(text, contract, *, query='', memories=()):
    """Reject an unqualified denial when grounded topic records were selected.

    Acknowledging a record while saying its requested attribute is unknown is
    allowed. This is an evidence-omission check, not a claim that the attribute
    value is known or that arbitrary factual contradictions can be understood.
    """
    if not contract or not contract.get('active'):
        return []
    normalized = text.replace('\u2019', "'")
    if contract.get('evidence_status') == 'unavailable':
        conditional = re.search(r'\b(?:if|maybe|perhaps|might)\b', normalized, re.I)
        prior_mention = re.search(r'\byou (?:mentioned|said|told me|described)\b', normalized, re.I)
        if not conditional and (_ACKNOWLEDGMENT.search(normalized) or prior_mention):
            return ['unavailable_recall_evidence_invented']
        return []
    if contract.get('reported_speaker') == 'current_interlocutor' and re.search(
        r'(?:^|[.!?]\s*)i (?:said|stated|told you)\b', normalized, re.I):
        return ['recall_speaker_reversal']
    if _DENIAL.search(normalized) and not _ACKNOWLEDGMENT.search(normalized):
        return ['available_recall_evidence_omitted']
    if query.lstrip().lower().startswith('what') and re.search(
        r'\b(?:you asked|your question|you want to know)\b', normalized, re.I):
        # A reference to the recall question is not itself recall evidence.
        # Scope this lexical check to question-echo responses: ordinary answers
        # may paraphrase the record without repeating its exact vocabulary.
        tokens = lambda value: set(re.findall(r"[a-z0-9']+", value.lower()))
        scaffolding = {'i','you','we','a','an','the','is','was','are','were','to','of','in','and','this','that',
                       'heard','say','said','told','remember','please','neutral','detail','me','my','your'}
        selected = [m for m in memories if str(memory_field(m,'id','')) in contract.get('evidence_ids',())]
        information = set().union(*(tokens(str(memory_field(m,'content',''))) for m in selected)) - tokens(query) - scaffolding
        if information and not information.intersection(tokens(text)):
            return ['recall_information_omitted']
    return []
