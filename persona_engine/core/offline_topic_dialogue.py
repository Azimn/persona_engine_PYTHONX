"""Cartridge-authored topic dialogue for the portable offline renderer.

This module selects bounded realization material. It does not select actions,
create memories, or decide whether the character should speak.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
import hashlib
import re
from typing import Any, Mapping, Sequence


TOPIC_FAMILIES = (
    "first_mention",
    "ordinary",
    "expanded",
    "memory_supported",
    "uncertain",
    "irritated",
    "refusal",
    "repeated",
    "relationship",
)
TOPIC_FRAGMENT_GROUPS = ("openings", *TOPIC_FAMILIES, "callbacks", "activity", "closings")
TOPIC_STATUSES = frozenset({"known", "partial", "unknown"})
MAX_TOPICS = 24
MAX_FRAGMENTS_PER_GROUP = 16

_STOP_WORDS = frozenset({
    "about", "after", "again", "also", "could", "did", "does", "ever", "for",
    "from", "have", "how", "into", "more", "much", "please", "should", "tell",
    "that", "the", "their", "them", "then", "there", "these", "they", "this",
    "those", "was", "were", "what", "when", "where", "which", "who", "why",
    "will", "with", "would", "you", "your",
})


def _tokens(value: str) -> tuple[str, ...]:
    return tuple(
        item for item in re.findall(r"[a-z0-9']+", str(value).casefold())
        if len(item) >= 3 and item not in _STOP_WORDS
    )


def _stable_index(size: int, *parts: object) -> int:
    payload = "|".join(str(item) for item in parts).encode("utf-8", errors="ignore")
    return int.from_bytes(hashlib.blake2b(payload, digest_size=4).digest(), "big") % max(1, size)


@dataclass(frozen=True)
class OfflineTopicDefinition:
    topic_id: str
    label: str
    aliases: tuple[str, ...]
    concepts: tuple[str, ...]
    memory_tags: tuple[str, ...]
    fragments: Mapping[str, tuple[str, ...]]

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "OfflineTopicDefinition":
        allowed = {"id", "label", "aliases", "concepts", "memory_tags", *TOPIC_FRAGMENT_GROUPS}
        unknown = sorted(set(value) - allowed)
        if unknown:
            raise ValueError(f"unknown offline topic field: {unknown[0]}")
        topic_id = str(value.get("id", "")).strip()
        label = str(value.get("label", "")).strip()
        aliases = tuple(str(item).strip().casefold() for item in value.get("aliases", ()))
        concepts = tuple(str(item).strip().casefold() for item in value.get("concepts", ()))
        memory_tags = tuple(str(item).strip() for item in value.get("memory_tags", ()))
        if not topic_id or len(topic_id) > 64 or not re.fullmatch(r"[a-z0-9_]+", topic_id):
            raise ValueError("offline topic id must be 1..64 lowercase identifier characters")
        if not label or len(label) > 100:
            raise ValueError("offline topic label must contain 1..100 characters")
        if not aliases or len(aliases) > 16 or any(not item or len(item) > 80 for item in aliases):
            raise ValueError("offline topic aliases must contain 1..16 bounded strings")
        if len(concepts) > 32 or len(memory_tags) > 16:
            raise ValueError("offline topic concepts or memory tags exceed their bounds")
        fragments: dict[str, tuple[str, ...]] = {}
        for group in TOPIC_FRAGMENT_GROUPS:
            raw = value.get(group, ())
            if not isinstance(raw, list) or len(raw) > MAX_FRAGMENTS_PER_GROUP:
                raise ValueError(f"offline topic {group} must be an array of at most 16 strings")
            items = tuple(str(item).strip() for item in raw)
            if any(not item or len(item) > 320 for item in items):
                raise ValueError(f"offline topic {group} contains an invalid fragment")
            fragments[group] = items
        if not fragments["ordinary"] or not fragments["uncertain"]:
            raise ValueError("offline topics require ordinary and uncertain fragments")
        return cls(topic_id, label, aliases, concepts, memory_tags, fragments)


@dataclass(frozen=True)
class OfflineTopicMatch:
    topic_id: str | None
    label: str | None
    status: str
    confidence: float
    matched_terms: tuple[str, ...]
    unresolved_terms: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class OfflineTopicThread:
    actor_id: int
    topic_id: str
    discussion_count: int = 0
    last_intent: str = ""
    recent_family_ids: list[str] = field(default_factory=list)
    recent_fragment_ids: list[str] = field(default_factory=list)
    recent_query_signatures: list[str] = field(default_factory=list)
    disclosed_memory_ids: list[str] = field(default_factory=list)
    last_turn: int = 0
    last_modality: str = "none"

    def to_dict(self) -> dict[str, Any]:
        return {
            "actor_id": self.actor_id,
            "topic_id": self.topic_id,
            "discussion_count": self.discussion_count,
            "last_intent": self.last_intent,
            "recent_family_ids": self.recent_family_ids[-12:],
            "recent_fragment_ids": self.recent_fragment_ids[-32:],
            "recent_query_signatures": self.recent_query_signatures[-12:],
            "disclosed_memory_ids": self.disclosed_memory_ids[-16:],
            "last_turn": self.last_turn,
            "last_modality": self.last_modality,
        }

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "OfflineTopicThread":
        return cls(
            actor_id=int(value["actor_id"]),
            topic_id=str(value["topic_id"]),
            discussion_count=max(0, int(value.get("discussion_count", 0))),
            last_intent=str(value.get("last_intent", "")),
            recent_family_ids=[str(item) for item in value.get("recent_family_ids", ())][-12:],
            recent_fragment_ids=[str(item) for item in value.get("recent_fragment_ids", ())][-32:],
            recent_query_signatures=[
                str(item) for item in value.get("recent_query_signatures", ())
            ][-12:],
            disclosed_memory_ids=[str(item) for item in value.get("disclosed_memory_ids", ())][-16:],
            last_turn=max(0, int(value.get("last_turn", 0))),
            last_modality=str(value.get("last_modality", "none")),
        )


class OfflineTopicThreadStore:
    MAX_THREADS = 256

    def __init__(self, threads: Sequence[OfflineTopicThread] = ()):
        self._threads = {(item.actor_id, item.topic_id): item for item in threads[-self.MAX_THREADS:]}

    def for_topic(self, actor_id: int, topic_id: str) -> OfflineTopicThread:
        key = (int(actor_id), str(topic_id))
        if key not in self._threads:
            if len(self._threads) >= self.MAX_THREADS:
                oldest = min(self._threads, key=lambda item: self._threads[item].last_turn)
                del self._threads[oldest]
            self._threads[key] = OfflineTopicThread(*key)
        return self._threads[key]

    def to_list(self) -> list[dict[str, Any]]:
        return [
            item.to_dict() for item in sorted(
                self._threads.values(), key=lambda item: (item.actor_id, item.topic_id)
            )
        ]

    @classmethod
    def from_list(cls, value: Sequence[Mapping[str, Any]] | None) -> "OfflineTopicThreadStore":
        return cls(tuple(OfflineTopicThread.from_dict(item) for item in (value or ())))


@dataclass(frozen=True)
class OfflineTopicPlan:
    topic_id: str
    topic_label: str
    match_status: str
    family: str
    fragment_ids: tuple[str, ...]
    fragments: tuple[str, ...]
    memory_id: str | None
    discussion_count_before: int
    pool_size: int
    unused_pool_size: int
    exhaustion_ratio: float
    query_signature: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class OfflineTopicLibrary:
    def __init__(self, topics: Sequence[OfflineTopicDefinition] = ()):
        if len(topics) > MAX_TOPICS:
            raise ValueError("offline topic library supports at most 24 topics")
        if len({item.topic_id for item in topics}) != len(topics):
            raise ValueError("offline topic ids must be unique")
        self.topics = tuple(topics)

    @classmethod
    def from_cartridge(cls, value: Mapping[str, Any] | None) -> "OfflineTopicLibrary":
        source = dict(value or {})
        unknown = sorted(set(source) - {"topics"})
        if unknown:
            raise ValueError(f"unknown offline topics field: {unknown[0]}")
        raw = source.get("topics", [])
        if not isinstance(raw, list):
            raise ValueError("offline topics must be an array")
        return cls(tuple(OfflineTopicDefinition.from_dict(item) for item in raw))

    def match(self, text: str) -> OfflineTopicMatch:
        query = set(_tokens(text))
        normalized = " ".join(str(text).casefold().split())
        candidates = []
        for topic in self.topics:
            alias_hits = tuple(alias for alias in topic.aliases if alias in normalized)
            vocabulary = set(_tokens(" ".join((*topic.aliases, *topic.concepts))))
            matched = tuple(sorted(query & vocabulary))
            if not alias_hits and not matched:
                continue
            coverage = len(matched) / max(1, len(query))
            confidence = min(1.0, (0.48 if alias_hits else 0.18) + 0.52 * coverage)
            candidates.append((confidence, len(alias_hits), topic.topic_id, topic, matched, vocabulary))
        if not candidates:
            return OfflineTopicMatch(None, None, "unknown", 0.0, (), tuple(sorted(query))[:12])
        confidence, _, _, topic, matched, vocabulary = max(candidates)
        unresolved = tuple(sorted(query - vocabulary))[:12]
        status = (
            "known"
            if (
                confidence >= 0.62
                or (confidence >= 0.52 and len(matched) >= 2)
            )
            and len(unresolved) <= max(2, len(matched))
            else "partial"
        )
        return OfflineTopicMatch(
            topic.topic_id, topic.label, status, round(confidence, 6), matched, unresolved,
        )

    def plan(
        self,
        *,
        match: OfflineTopicMatch,
        thread: OfflineTopicThread,
        input_act: str,
        turn: int,
        pressure: float,
        familiarity: float,
        memory_id: str | None,
        memory_text: str | None,
        activity: str,
    ) -> OfflineTopicPlan | None:
        topic = next((item for item in self.topics if item.topic_id == match.topic_id), None)
        if topic is None or match.status == "unknown":
            return None
        query_signature = "|".join((*match.matched_terms, *match.unresolved_terms)[:8])
        repeated_query = bool(
            query_signature and query_signature in thread.recent_query_signatures[-4:]
        )
        if match.status == "partial":
            family = "uncertain"
        elif pressure >= 0.72 and topic.fragments["irritated"]:
            family = "irritated"
        elif input_act == "ask_memory" and memory_id and topic.fragments["memory_supported"]:
            family = "memory_supported"
        elif thread.discussion_count == 0 and topic.fragments["first_mention"]:
            family = "first_mention"
        elif repeated_query and thread.discussion_count >= 2 and topic.fragments["repeated"]:
            family = "repeated" if topic.fragments["repeated"] else "ordinary"
        elif memory_id and memory_id not in thread.disclosed_memory_ids and topic.fragments["memory_supported"]:
            family = "memory_supported"
        elif thread.discussion_count == 1 and topic.fragments["expanded"]:
            family = "expanded"
        elif familiarity >= 0.45 and topic.fragments["relationship"]:
            family = "relationship"
        else:
            family = "ordinary"
        selected: list[tuple[str, str]] = []
        if thread.discussion_count == 0 and topic.fragments["openings"]:
            selected.append(self._select(topic, "openings", thread, turn))
        selected.append(self._select(topic, family, thread, turn))
        if family == "memory_supported" and memory_text and topic.fragments["callbacks"]:
            selected.append(self._select(topic, "callbacks", thread, turn))
        elif activity and thread.discussion_count > 0 and topic.fragments["activity"] and turn % 3 == 0:
            selected.append(self._select(topic, "activity", thread, turn))
        if thread.discussion_count >= 5 and topic.fragments["closings"] and turn % 2 == 0:
            selected.append(self._select(topic, "closings", thread, turn))
        pool_ids = {
            f"{topic.topic_id}:{group}:{index}"
            for group in TOPIC_FRAGMENT_GROUPS
            for index in range(len(topic.fragments[group]))
        }
        used = set(thread.recent_fragment_ids)
        unused = len(pool_ids - used)
        return OfflineTopicPlan(
            topic_id=topic.topic_id,
            topic_label=topic.label,
            match_status=match.status,
            family=family,
            fragment_ids=tuple(item[0] for item in selected),
            fragments=tuple(
                item[1].replace("{memory}", (memory_text or "the earlier episode")[:160])
                .replace("{activity}", (activity or "my work")[:100])
                for item in selected
            ),
            memory_id=memory_id if family == "memory_supported" and memory_text else None,
            discussion_count_before=thread.discussion_count,
            pool_size=len(pool_ids),
            unused_pool_size=unused,
            exhaustion_ratio=round(1.0 - unused / max(1, len(pool_ids)), 6),
            query_signature=query_signature,
        )

    @staticmethod
    def _select(
        topic: OfflineTopicDefinition,
        group: str,
        thread: OfflineTopicThread,
        turn: int,
    ) -> tuple[str, str]:
        fragments = topic.fragments[group]
        candidates = [
            (f"{topic.topic_id}:{group}:{index}", text)
            for index, text in enumerate(fragments)
        ]
        unused = [item for item in candidates if item[0] not in thread.recent_fragment_ids]
        if unused:
            pool = unused
        else:
            last_id = thread.recent_fragment_ids[-1] if thread.recent_fragment_ids else None
            pool = [item for item in candidates if item[0] != last_id] or candidates
        return pool[_stable_index(len(pool), topic.topic_id, group, thread.actor_id, turn)]


def record_topic_turn(
    thread: OfflineTopicThread,
    *,
    plan: OfflineTopicPlan | None,
    input_act: str,
    turn: int,
    modality: str,
) -> None:
    thread.discussion_count += 1
    thread.last_intent = str(input_act)
    thread.last_turn = int(turn)
    thread.last_modality = str(modality)
    if plan is None:
        return
    thread.recent_family_ids = [*thread.recent_family_ids, plan.family][-12:]
    thread.recent_fragment_ids = [*thread.recent_fragment_ids, *plan.fragment_ids][-32:]
    if plan.query_signature:
        thread.recent_query_signatures = [
            *thread.recent_query_signatures, plan.query_signature,
        ][-12:]
    if plan.memory_id:
        thread.disclosed_memory_ids = [*thread.disclosed_memory_ids, plan.memory_id][-16:]
