"""Layer 3: memory as computed activation plus hybrid semantic retrieval.

Activation is computed fresh at retrieval time from recency, frequency, and
salience. Retrieval combines ACT-R-style activation with lexical, synonym, and
character n-gram similarity. Optional external vector stores can be added later
without changing the public MemoryStore API.
"""

import math
import re
import uuid
from dataclasses import dataclass, field
from typing import List, Set, Dict
from enum import Enum


class KnowledgeSource(Enum):
    OBSERVED = "observed"
    USER_TOLD = "user_told"
    INFERRED = "inferred"
    REFLECTION = "reflection"
    CORE_IDENTITY = "core_identity"


@dataclass
class MemoryUnit:
    content: str
    created_at: float
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:8])
    recall_times: List[float] = field(default_factory=list)
    emotional_valence: float = 0.0
    emotional_intensity: float = 0.0
    relationship_relevance: float = 0.0
    identity_relevance: float = 0.0
    unresolved: bool = False
    source: KnowledgeSource = KnowledgeSource.OBSERVED
    tags: Set[str] = field(default_factory=set)
    compressed: bool = False

    def __post_init__(self):
        # V1 stored every recall timestamp forever. Long-horizon tests showed
        # that seven resident memories could therefore occupy hundreds of KB.
        # Keep only the recent rehearsal trace required by activation. This is
        # an engineering saturation bound, not a claim about human memory span.
        cleaned = []
        for value in self.recall_times[-REHEARSAL_TRACE_WIDTH:]:
            try:
                cleaned.append(float(value))
            except (TypeError, ValueError):
                continue
        self.recall_times = cleaned

    def record_recall(self, now: float) -> None:
        self.recall_times.append(float(now))
        if len(self.recall_times) > REHEARSAL_TRACE_WIDTH:
            del self.recall_times[:-REHEARSAL_TRACE_WIDTH]


def first_person_memory_content(content: str) -> str:
    """Return memory text in the character's first-person record style."""

    text = str(content or "").strip()
    if not text:
        return "I noticed something, but the detail is unavailable."
    lowered = text.lower()
    if lowered.startswith(("i ", "i'", "i.", "i:", "my ", "we ")):
        return text
    if lowered.startswith("user stated:"):
        return "I heard you say:" + text.split(":", 1)[1]
    if lowered.startswith("user mentioned "):
        return "I heard you mention " + text[len("User mentioned "):]
    if lowered.startswith("user accused "):
        return "I heard an accusation: " + text[len("User accused "):]
    if lowered.startswith("user made "):
        return "I noticed you made " + text[len("User made "):]
    if lowered.startswith("[sensorium]"):
        detail = text.split("]", 1)[1].strip()
        if ":" in detail:
            kind, value = [part.strip() for part in detail.split(":", 1)]
            if kind == "body_state":
                return f"I noticed my body state: {value}"
            if kind == "movement_need":
                return f"I felt a need to move: {value}"
            if kind == "sensory_load":
                return f"I felt sensory load: {value}"
            if kind == "user_absence":
                return f"I noticed your absence: {value}"
            if kind == "ambient_event":
                return f"I noticed an ambient event: {value}"
            return f"I noticed {kind}: {value}"
        return f"I noticed {detail}"
    if lowered.startswith("[reflection]"):
        return "I formed a reflection:" + text.split("]", 1)[1]
    return text


_SYNONYM_GROUPS = [
    {"sad", "upset", "hurt", "down", "depressed", "miserable", "unhappy", "low"},
    {"angry", "mad", "furious", "irritated", "annoyed", "resentful"},
    {"lie", "lied", "deceive", "deceived", "betray", "betrayed", "dishonest"},
    {"sorry", "apologize", "apology", "regret", "wrong", "repair"},
    {"care", "love", "miss", "need", "trust", "attached", "stay"},
    {"afraid", "fear", "scared", "worried", "threat", "unsafe"},
]
_SYNONYM_MAP: Dict[str, Set[str]] = {}
for group in _SYNONYM_GROUPS:
    for word in group:
        _SYNONYM_MAP[word] = group


def _tokens(text: str) -> Set[str]:
    return {t for t in re.findall(r"[a-z0-9']+", text.lower()) if len(t) > 1}


def _expanded_tokens(text: str) -> Set[str]:
    base = _tokens(text)
    expanded = set(base)
    for token in base:
        expanded.update(_SYNONYM_MAP.get(token, set()))
    return expanded


def _char_ngrams(text: str, n: int = 4) -> Set[str]:
    clean = re.sub(r"\s+", " ", text.lower()).strip()
    if len(clean) < n:
        return {clean} if clean else set()
    return {clean[i:i+n] for i in range(len(clean) - n + 1)}


def activation(mem: MemoryUnit, now: float, query_similarity: float = 0.0,
               emotional_state_match: float = 0.0, decay: float = 0.5) -> float:
    times = [max(now - mem.created_at, 0.001)] + [max(now - t, 0.001) for t in mem.recall_times]
    base = math.log(sum(t ** -decay for t in times))
    salience = (
        mem.emotional_intensity * 1.5
        + mem.relationship_relevance * 1.0
        + mem.identity_relevance * 1.2
        + (1.0 if mem.unresolved else 0.0)
    )
    return base + query_similarity + emotional_state_match + salience


def lexical_similarity(query: str, content: str) -> float:
    q = _tokens(query)
    c = _tokens(content)
    if not q or not c:
        return 0.0
    return len(q & c) / math.sqrt(len(q) * len(c))


def semantic_similarity(query: str, content: str) -> float:
    """Dependency-free semantic-ish similarity.

    This is not a substitute for MiniLM or ChromaDB, but it catches common
    paraphrases through synonym expansion and character n-grams while keeping the
    engine runnable on a clean Python install.
    """
    q_exp = _expanded_tokens(query)
    c_exp = _expanded_tokens(content)
    synonym_score = 0.0
    if q_exp and c_exp:
        synonym_score = len(q_exp & c_exp) / math.sqrt(len(q_exp) * len(c_exp))
    q_ng = _char_ngrams(query)
    c_ng = _char_ngrams(content)
    ngram_score = (len(q_ng & c_ng) / len(q_ng | c_ng)) if q_ng and c_ng else 0.0
    return max(lexical_similarity(query, content), synonym_score * 0.85, ngram_score * 0.55)


# Backward-compatible name used by older tests or callers.
def simple_similarity(query: str, content: str) -> float:
    return semantic_similarity(query, content)


TURN_RETRIEVAL_WIDTH = 4
REFLECTION_RETRIEVAL_WIDTH = 3
# Rehearsal is a bounded working-state trace, not a second autobiography.
# Use one ordinary retrieval-workspace width so repeated recall can strengthen
# a memory but cannot make its resident representation grow with lifetime.
REHEARSAL_TRACE_WIDTH = TURN_RETRIEVAL_WIDTH


class MemoryStore:
    def __init__(self):
        self.memories: List[MemoryUnit] = []

    def compact_user_told_working_set(self, relationship) -> dict:
        """Bound only canonically recoverable user-statement autobiography.

        Non-USER_TOLD memories remain pinned until their first-person/causal
        reconstruction contracts are demonstrated. User statements retain
        two current roles: active unresolved evidence for the widest consumer
        (reflection, top 3) and recent conversational context for ordinary
        retrieval (top 4). Cold canonical biography owns older wording.
        """
        user_memories = [m for m in self.memories if m.source == KnowledgeSource.USER_TOLD]
        if not user_memories:
            return {"before": len(self.memories), "after": len(self.memories), "evicted_user_told": 0}

        keep_ids: set[str] = set()
        cutoff = float(getattr(relationship, "last_conflict_resolved_at", 0.0) or 0.0)
        relationship_unresolved = float(getattr(relationship, "unresolved_conflict", 0.0) or 0.0) > 0.0
        if relationship_unresolved:
            active_unresolved = [
                m for m in user_memories
                if m.unresolved and float(m.created_at) > cutoff
            ]
            active_unresolved.sort(
                key=lambda m: (
                    float(m.relationship_relevance),
                    float(m.emotional_intensity),
                    float(m.identity_relevance),
                    float(m.created_at),
                    str(m.id),
                ),
                reverse=True,
            )
            keep_ids.update(m.id for m in active_unresolved[:REFLECTION_RETRIEVAL_WIDTH])

        recent = sorted(user_memories, key=lambda m: (float(m.created_at), str(m.id)), reverse=True)
        recent_added = 0
        for memory in recent:
            if memory.id in keep_ids:
                continue
            keep_ids.add(memory.id)
            recent_added += 1
            if recent_added >= TURN_RETRIEVAL_WIDTH:
                break

        before = len(self.memories)
        user_before = len(user_memories)
        self.memories = [
            memory for memory in self.memories
            if memory.source != KnowledgeSource.USER_TOLD or memory.id in keep_ids
        ]
        user_after = sum(1 for memory in self.memories if memory.source == KnowledgeSource.USER_TOLD)
        return {
            "before": before,
            "after": len(self.memories),
            "user_told_before": user_before,
            "user_told_after": user_after,
            "evicted_user_told": user_before - user_after,
            "active_unresolved_slots": REFLECTION_RETRIEVAL_WIDTH,
            "recent_context_slots": TURN_RETRIEVAL_WIDTH,
        }

    def add(self, mem: MemoryUnit):
        mem.content = first_person_memory_content(mem.content)
        if any(existing.id == mem.id for existing in self.memories):
            return
        self.memories.append(mem)

    def retrieve(self, query: str, now: float, top_k: int = 5,
                 emotional_state_match: float = 0.0) -> List[MemoryUnit]:
        scored = []
        for mem in self.memories:
            sem = semantic_similarity(query, mem.content)
            score = activation(mem, now, sem, emotional_state_match)
            scored.append((score, sem, mem))
        scored.sort(key=lambda x: x[0], reverse=True)
        top = [(sem, mem) for _, sem, mem in scored[:top_k]]
        # Being ranked into the workspace is not itself evidence that a memory
        # was meaningfully recalled. Zero-relevance candidates may remain useful
        # as background context, but they must not gain rehearsal strength merely
        # because they were resident and happened to occupy a top-k slot.
        for sem, mem in top:
            if sem > 0.0:
                mem.record_recall(now)
        return [mem for _, mem in top]

    def compress_old(self, now: float, age_threshold: float = 86400 * 30):
        for mem in self.memories:
            if not mem.compressed and (now - mem.created_at) > age_threshold and mem.emotional_intensity < 0.3:
                mem.content = f"[impression] {mem.content[:60]}"
                mem.compressed = True
