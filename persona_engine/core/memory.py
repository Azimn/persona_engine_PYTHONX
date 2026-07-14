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
from typing import Any, List, Set, Dict
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
    confidence: float = 1.0
    salience: float = 0.5
    provenance: dict[str, Any] = field(default_factory=dict)
    source_tier: int = 0


@dataclass(frozen=True)
class MemoryRetrieval:
    memory: MemoryUnit
    score: float
    reasons: dict[str, float | str]


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


class MemoryStore:
    def __init__(self, embedding_provider=None):
        self.memories: List[MemoryUnit] = []
        self.embedding_provider = embedding_provider

    def add(self, mem: MemoryUnit):
        mem.content = first_person_memory_content(mem.content)
        if any(existing.id == mem.id for existing in self.memories):
            return
        self.memories.append(mem)

    def retrieve(self, query: str, now: float, top_k: int = 5,
                 emotional_state_match: float = 0.0) -> List[MemoryUnit]:
        return [item.memory for item in self.retrieve_explained(query, now, top_k, emotional_state_match)]

    def retrieve_explained(self, query: str, now: float, top_k: int = 5,
                           emotional_state_match: float = 0.0,
                           goal_tags: Set[str] | None = None,
                           relationship_tags: Set[str] | None = None) -> List[MemoryRetrieval]:
        """Return bounded hybrid retrievals with inspectable selection reasons."""

        provider = self.embedding_provider
        query_vector: list[float] = []
        try:
            embeddings_available = bool(provider and provider.available())
        except Exception:
            embeddings_available = False
        if embeddings_available:
            try:
                query_vector = provider.embed_text(query)
            except Exception:
                embeddings_available = False
                query_vector = []
        goal_tags = set(goal_tags or ())
        relationship_tags = set(relationship_tags or ())
        scored: list[MemoryRetrieval] = []
        for mem in self.memories:
            lexical = lexical_similarity(query, mem.content)
            symbolic = semantic_similarity(query, mem.content)
            vector_score = 0.0
            if embeddings_available:
                try:
                    vector_score = max(0.0, provider.similarity(query_vector, provider.embed_text(mem.content)))
                except Exception:
                    vector_score = 0.0
            age = max(0.0, now - mem.created_at)
            recency = 1.0 / (1.0 + age / 86400.0)
            emotional = max(0.0, min(1.0, mem.emotional_intensity + emotional_state_match))
            goal = 0.15 if goal_tags & mem.tags else 0.0
            relationship = 0.15 if relationship_tags & mem.tags else min(0.15, mem.relationship_relevance * 0.15)
            direct_link = 0.12 if any(tag.startswith("world_event:") for tag in mem.tags) else 0.0
            score = (
                activation(mem, now, symbolic * 0.65, emotional_state_match)
                + lexical * 0.45 + vector_score * 0.55 + recency * 0.18
                + goal + relationship + direct_link + mem.salience * 0.2
            )
            scored.append(MemoryRetrieval(mem, score, {
                "lexical_match": round(lexical, 4),
                "symbolic_similarity": round(symbolic, 4),
                "semantic_similarity": round(vector_score, 4),
                "recency_boost": round(recency * 0.18, 4),
                "salience": round(mem.salience, 4),
                "emotional_relevance": round(emotional, 4),
                "goal_relevance": round(goal, 4),
                "relationship_relevance": round(relationship, 4),
                "direct_link": round(direct_link, 4),
                "embedding_provider": "available" if embeddings_available else "fallback",
            }))
        scored.sort(key=lambda item: (-item.score, item.memory.id))
        selected = scored[:max(0, int(top_k))]
        for item in selected:
            item.memory.recall_times.append(now)
        return selected

    def compress_old(self, now: float, age_threshold: float = 86400 * 30):
        for mem in self.memories:
            if not mem.compressed and (now - mem.created_at) > age_threshold and mem.emotional_intensity < 0.3:
                mem.content = f"[impression] {mem.content[:60]}"
                mem.compressed = True
                mem.confidence = max(0.1, mem.confidence - 0.2)
