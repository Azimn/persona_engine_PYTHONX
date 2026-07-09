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


class MemoryStore:
    def __init__(self):
        self.memories: List[MemoryUnit] = []

    def add(self, mem: MemoryUnit):
        if any(existing.id == mem.id for existing in self.memories):
            return
        self.memories.append(mem)

    def retrieve(self, query: str, now: float, top_k: int = 5,
                 emotional_state_match: float = 0.0) -> List[MemoryUnit]:
        scored = []
        for mem in self.memories:
            sem = semantic_similarity(query, mem.content)
            score = activation(mem, now, sem, emotional_state_match)
            scored.append((score, mem))
        scored.sort(key=lambda x: x[0], reverse=True)
        top = [m for _, m in scored[:top_k]]
        for m in top:
            m.recall_times.append(now)
        return top

    def compress_old(self, now: float, age_threshold: float = 86400 * 30):
        for mem in self.memories:
            if not mem.compressed and (now - mem.created_at) > age_threshold and mem.emotional_intensity < 0.3:
                mem.content = f"[impression] {mem.content[:60]}"
                mem.compressed = True
