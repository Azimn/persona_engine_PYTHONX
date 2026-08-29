"""World authority and objective fact resolution.

The world authority is the only generic module allowed to create objective
world facts from host, simulator, audio, vision, or action-proposal events.
It does not decide emotions, beliefs, or relationship state. It produces
bounded facts that downstream interpretation may read through visibility rules.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any
import time
import uuid


@dataclass
class WorldFact:
    """Objective world fact owned by the world authority."""

    id: str
    key: str
    value: Any
    source: str
    confidence: float
    visible_to_character: bool
    created_at: float
    expires_at: float | None = None
    tags: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "WorldFact":
        return cls(**{k: data[k] for k in data if k in cls.__dataclass_fields__})


@dataclass
class WorldActionProposal:
    """An intended action. The organism proposes; the world resolves."""

    actor_id: str
    action_type: str
    payload: dict[str, Any]
    created_at: float
    confidence: float = 1.0


@dataclass
class WorldResolution:
    """Outcome of resolving an action or sensor event into facts."""

    accepted: bool
    facts_created: list[WorldFact]
    reason: str


class WorldAuthority:
    """Owns objective facts and visibility filtering.

    This class is intentionally character-agnostic. Any character-specific
    sensitivity to these facts must live in cartridge data or downstream state.
    """

    def __init__(self, facts: list[WorldFact] | None = None):
        self.facts: dict[str, WorldFact] = {fact.id: fact for fact in (facts or [])}

    def to_list(self) -> list[dict[str, Any]]:
        return [fact.to_dict() for fact in self.facts.values()]

    @classmethod
    def from_list(cls, data: list[dict[str, Any]] | None) -> "WorldAuthority":
        return cls([WorldFact.from_dict(item) for item in (data or [])])

    def add_fact(
        self,
        key: str,
        value: Any,
        source: str,
        confidence: float = 1.0,
        visible_to_character: bool = True,
        tags: list[str] | None = None,
        expires_at: float | None = None,
        created_at: float | None = None,
    ) -> WorldFact:
        now = created_at or time.time()
        fact = WorldFact(
            id=f"fact_{uuid.uuid4().hex}",
            key=str(key),
            value=value,
            source=str(source),
            confidence=max(0.0, min(1.0, float(confidence))),
            visible_to_character=bool(visible_to_character),
            created_at=now,
            expires_at=expires_at,
            tags=list(tags or []),
        )
        self.facts[fact.id] = fact
        return fact

    def expire_old(self, now: float | None = None) -> None:
        now = now or time.time()
        expired = [fact_id for fact_id, fact in self.facts.items() if fact.expires_at is not None and fact.expires_at <= now]
        for fact_id in expired:
            del self.facts[fact_id]

    @staticmethod
    def _potential_winner_ids(facts: list[WorldFact], now: float) -> set[str]:
        """Return active facts that may still become latest-surviving truth.

        Facts are evaluated in insertion order because that is the existing
        WorldAuthority precedence contract. An older expiring fact matters only
        when it can outlive every newer candidate. The first older non-expiring
        fact is a permanent fallback and makes all still-older facts unreachable.
        """

        keep: set[str] = set()
        max_newer_expiry = now
        for fact in reversed(facts):
            if fact.expires_at is not None and fact.expires_at <= now:
                continue
            if fact.expires_at is None:
                keep.add(fact.id)
                break
            expiry = float(fact.expires_at)
            if expiry > max_newer_expiry:
                keep.add(fact.id)
                max_newer_expiry = expiry
        return keep

    def compact_dominated(self, now: float | None = None) -> int:
        """Discard active fact history that cannot affect present or future truth.

        Server truth and character-visible truth are separate projections, so a
        hidden newer fact cannot erase an older visible fallback. Expiring
        overrides retain any older fact that can legitimately re-emerge later.
        Canonical continuity, not this current-state authority, owns historical
        event retention. Returns the number of facts removed.
        """

        now = time.time() if now is None else float(now)
        self.expire_old(now=now)
        by_key: dict[str, list[WorldFact]] = {}
        for fact in self.facts.values():
            by_key.setdefault(fact.key, []).append(fact)

        keep: set[str] = set()
        for facts in by_key.values():
            keep.update(self._potential_winner_ids(facts, now))
            visible_facts = [fact for fact in facts if fact.visible_to_character]
            keep.update(self._potential_winner_ids(visible_facts, now))

        before = len(self.facts)
        self.facts = {
            fact_id: fact
            for fact_id, fact in self.facts.items()
            if fact_id in keep
        }
        return before - len(self.facts)

    def apply_host_event(self, payload: dict[str, Any], source: str = "host", visible: bool = True) -> WorldResolution:
        facts: list[WorldFact] = []
        for key, value in (payload or {}).items():
            if key.startswith("_"):
                continue
            facts.append(self.add_fact(key, value, source=source, confidence=1.0, visible_to_character=visible, tags=[source]))
        return WorldResolution(bool(facts), facts, "host event accepted" if facts else "no visible fact keys")

    def apply_sensor_event(self, sensor_type: str, payload: dict[str, Any], confidence: float = 1.0) -> WorldResolution:
        """Convert bounded sensor observations into objective facts.

        This method deliberately does not write to pressures or relationship.
        """
        sensor_type = str(sensor_type)
        facts: list[WorldFact] = []
        for key, value in (payload or {}).items():
            if key in {"raw_audio", "raw_frame", "image_bytes"}:
                continue
            fact_key = f"{sensor_type}_{key}"
            facts.append(self.add_fact(fact_key, value, source=f"{sensor_type}_sensor", confidence=confidence, visible_to_character=True, tags=["sensorium", sensor_type]))
        return WorldResolution(bool(facts), facts, "sensor event accepted" if facts else "sensor event had no safe facts")

    def resolve_action(self, proposal: WorldActionProposal) -> WorldResolution:
        """Resolve a character action proposal into world facts.

        The implementation is intentionally conservative. Unsupported actions
        are rejected without side effects.
        """
        action = proposal.action_type
        payload = dict(proposal.payload or {})
        if action in {"set_attention", "turn_attention", "orient"}:
            target = str(payload.get("target", "unknown"))[:80]
            fact = self.add_fact("attention_target", target, source="action_resolution", confidence=proposal.confidence, visible_to_character=True, tags=["action", "attention"])
            return WorldResolution(True, [fact], "attention proposal resolved")
        if action in {"move_to_zone", "move"}:
            zone = str(payload.get("zone", payload.get("target", "unknown")))[:80]
            if zone == "unknown":
                return WorldResolution(False, [], "movement proposal missing zone")
            fact = self.add_fact("zone", zone, source="action_resolution", confidence=proposal.confidence, visible_to_character=True, tags=["action", "movement"])
            return WorldResolution(True, [fact], "movement proposal resolved")
        return WorldResolution(False, [], f"unsupported action proposal: {action}")

    def get_server_truth(self) -> dict[str, Any]:
        self.expire_old()
        return {fact.key: fact.value for fact in self.facts.values()}

    def get_visible_context(self, actor_id: str | None = None) -> dict[str, Any]:
        self.expire_old()
        return {fact.key: fact.value for fact in self.facts.values() if fact.visible_to_character}

    def recent_facts(self, limit: int = 20) -> list[WorldFact]:
        """Return recent active fact contenders, not an authoritative history.

        ``compact_dominated`` may discard superseded facts that can never affect
        truth again. Historical world events belong to canonical continuity.
        """

        self.expire_old()
        return sorted(self.facts.values(), key=lambda f: f.created_at, reverse=True)[:limit]
