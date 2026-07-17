"""Deterministic replay of cartridge-authored pre-session life history.

Genesis is an input history, not a memory import. Every retained record passes
through the ordinary world-event, perception, consolidation, decay, and
autobiographical pathways owned by the engine.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
import math
from typing import Any, Mapping, Sequence

from .journal import JOURNAL_ENTRY_KINDS


GENESIS_AUTHORITIES = frozenset({
    "lived", "documentary", "hearsay", "expanded_continuity",
    "ontologically_disputed", "current_system_fact",
})
MAX_GENESIS_EPISODES = 64
MAX_GENESIS_ELAPSED_DAYS = 3650.0
SECONDS_PER_YEAR = 365.2425 * 86400.0


def _stable_digest(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    return hashlib.blake2b(payload, digest_size=12).hexdigest()


@dataclass(frozen=True)
class GenesisEpisode:
    episode_id: str
    historical_year: int
    authority: str
    event_type: str
    actors: tuple[str, ...]
    location: str
    action: str
    targets: tuple[str, ...]
    outcome: str
    attention: float
    confidence: float
    salience: float
    emotional_residue: str
    interpretation: str
    distortion: Mapping[str, Any]
    consolidate: bool
    elapsed_days_before: float
    tags: tuple[str, ...]
    journal_text: str | None
    journal_kind: str
    perceived_summary: str | None
    historical_span_years: float

    def __post_init__(self) -> None:
        if self.authority not in GENESIS_AUTHORITIES:
            raise ValueError(f"unsupported genesis authority: {self.authority}")
        if not self.episode_id or len(self.episode_id) > 80:
            raise ValueError("genesis episode_id must contain 1..80 characters")
        if not self.event_type or len(self.event_type) > 80:
            raise ValueError("genesis event_type must contain 1..80 characters")
        if not self.outcome.strip() or len(self.outcome) > 1200:
            raise ValueError("genesis outcome must contain 1..1200 characters")
        if not self.interpretation.strip() or len(self.interpretation) > 800:
            raise ValueError("genesis interpretation must contain 1..800 characters")
        for value in (self.attention, self.confidence, self.salience):
            if not math.isfinite(float(value)) or not 0.0 <= float(value) <= 1.0:
                raise ValueError("genesis perception values must be finite and within [0, 1]")
        if not math.isfinite(self.elapsed_days_before) or not 0.0 <= self.elapsed_days_before <= MAX_GENESIS_ELAPSED_DAYS:
            raise ValueError("genesis elapsed_days_before exceeds its bound")
        if len(self.actors) > 8 or len(self.targets) > 8 or len(self.tags) > 12:
            raise ValueError("genesis actor, target, or tag bound exceeded")
        if self.journal_text is not None and (not self.journal_text.strip() or len(self.journal_text) > 4000):
            raise ValueError("genesis journal text must contain 1..4000 characters")
        if self.journal_kind not in JOURNAL_ENTRY_KINDS:
            raise ValueError(f"unsupported genesis journal kind: {self.journal_kind}")
        if self.perceived_summary is not None and (
            not self.perceived_summary.strip() or len(self.perceived_summary) > 1200
            or not self.perceived_summary.lower().startswith(("i ", "i'", "my ", "we "))
        ):
            raise ValueError("genesis perceived summary must be bounded first-person text")
        if not math.isfinite(self.historical_span_years) or not 0.0 <= self.historical_span_years <= 200.0:
            raise ValueError("genesis historical_span_years must be within [0, 200]")

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "GenesisEpisode":
        perception = dict(value.get("perception") or {})
        return cls(
            episode_id=str(value["id"]),
            historical_year=int(value.get("year", 0)),
            authority=str(value.get("authority", "lived")),
            event_type=str(value.get("event_type", "historical_event")),
            actors=tuple(str(item) for item in value.get("actors", ())),
            location=str(value.get("location", "unknown"))[:120],
            action=str(value.get("action", "experienced"))[:200],
            targets=tuple(str(item) for item in value.get("targets", ())),
            outcome=str(value.get("outcome", "")),
            attention=float(perception.get("attention", 0.8)),
            confidence=float(perception.get("confidence", 0.75)),
            salience=float(perception.get("salience", 0.6)),
            emotional_residue=str(perception.get("emotional_residue", "neutral"))[:120],
            interpretation=str(perception.get("interpretation", "ordinary")),
            distortion=dict(perception.get("distortion") or {}),
            consolidate=bool(perception.get("consolidate", True)),
            elapsed_days_before=float(value.get("elapsed_days_before", 0.0)),
            tags=tuple(str(item)[:80] for item in value.get("tags", ())),
            journal_text=str(value["journal_text"]) if value.get("journal_text") is not None else None,
            journal_kind=str(value.get("journal_kind", "private_note")),
            perceived_summary=str(perception["summary"]) if perception.get("summary") is not None else None,
            historical_span_years=float(value.get("historical_span_years", 0.0)),
        )


@dataclass(frozen=True)
class GenesisReplayResult:
    schema_version: int
    genesis_version: str
    replay_digest: str
    episodes_processed: int
    events_created: int
    experiences_created: int
    events_missed: int
    memories_consolidated: int
    interpretation_count: int
    start_time: float
    end_time: float
    already_applied: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class GenesisReplayer:
    """Apply one bounded authored history through an InteriorEngine."""

    def parse(self, genesis: Mapping[str, Any] | None) -> tuple[str, tuple[GenesisEpisode, ...]]:
        source = dict(genesis or {})
        version = str(source.get("version", ""))
        episodes = tuple(GenesisEpisode.from_dict(item) for item in source.get("episodes", ()))
        if not version or len(version) > 80:
            raise ValueError("genesis version must contain 1..80 characters")
        if not 1 <= len(episodes) <= MAX_GENESIS_EPISODES:
            raise ValueError(f"genesis must contain 1..{MAX_GENESIS_EPISODES} episodes")
        ids = [item.episode_id for item in episodes]
        if len(ids) != len(set(ids)):
            raise ValueError("genesis episode IDs must be unique")
        return version, episodes

    def replay(self, engine, *, end_time: float) -> GenesisReplayResult:
        version, episodes = self.parse((engine.cartridge_data or {}).get("genesis"))
        source_digest = _stable_digest({"version": version, "episodes": [asdict(item) for item in episodes]})
        prior = next(
            (item for item in engine.genesis_replays if item.get("replay_digest") == source_digest),
            None,
        )
        if prior:
            values = {
                key: prior[key] for key in GenesisReplayResult.__dataclass_fields__
                if key in prior and key != "already_applied"
            }
            return GenesisReplayResult(**values, already_applied=True)

        positive_years = [item.historical_year for item in episodes if item.historical_year > 0]
        end_year = max(positive_years, default=0)
        year_counts = {
            year: sum(item.historical_year == year for item in episodes)
            for year in set(positive_years)
        }
        year_seen: dict[int, int] = {}
        fallback_seconds = sum(item.elapsed_days_before for item in episodes) * 86400.0
        cursor = float(end_time) - fallback_seconds
        timestamps: list[float] = []
        before_events = len(engine.world_events.to_list())
        before_experiences = len(engine.experiences.experiences)
        before_memories = len(engine.memory.memories)
        missed = 0

        for episode in episodes:
            if end_year and episode.historical_year > 0:
                index = year_seen.get(episode.historical_year, 0) + 1
                year_seen[episode.historical_year] = index
                fraction = index / (year_counts[episode.historical_year] + 1.0)
                cursor = float(end_time) - (
                    (end_year - episode.historical_year) + (1.0 - fraction)
                ) * SECONDS_PER_YEAR
            else:
                cursor += episode.elapsed_days_before * 86400.0
            timestamps.append(cursor)
            engine.timestep += 1
            event = engine.record_world_event(
                event_type=episode.event_type,
                actors=episode.actors,
                location=episode.location,
                action=episode.action,
                targets=episode.targets,
                outcome=episode.outcome,
                source="cartridge_genesis",
                payload={
                    "genesis_episode_id": episode.episode_id,
                    "historical_year": episode.historical_year,
                    "authority": episode.authority,
                    "authored_history": True,
                    "historical_span_years": episode.historical_span_years,
                },
                timestamp=cursor,
            )
            experience = engine.perceive_world_event(
                event.event_id,
                attention=episode.attention,
                confidence=episode.confidence,
                salience=episode.salience,
                emotional_residue=episode.emotional_residue,
                interpretation=episode.interpretation,
                distortion={
                    **dict(episode.distortion),
                    "genesis_authority": episode.authority,
                    "historical_year": episode.historical_year,
                },
                consolidate=episode.consolidate,
                perceived_summary=episode.perceived_summary,
            )
            if experience is None:
                missed += 1
            elif experience.memory_id and episode.tags:
                memory = next((item for item in engine.memory.memories if item.id == experience.memory_id), None)
                if memory is not None:
                    memory.tags.update({"genesis", *episode.tags})
                    if episode.historical_span_years >= 1.0:
                        memory.tags.update({"chapter_summary", f"span_years:{int(episode.historical_span_years)}"})
            if episode.journal_text:
                engine.write_journal_entry(
                    episode.journal_text,
                    entry_kind=episode.journal_kind,
                    source="cartridge_genesis",
                    source_event_ids=(event.event_id,),
                    historical_year=episode.historical_year,
                    timestamp=cursor,
                    persist=False,
                )
            engine.experiences.decay(cursor)
            engine.memory.compress_old(cursor)

        engine.experiences.decay(float(end_time))
        engine.memory.compress_old(float(end_time))
        engine.last_wall_time = float(end_time)
        result = GenesisReplayResult(
            schema_version=1,
            genesis_version=version,
            replay_digest=source_digest,
            episodes_processed=len(episodes),
            events_created=len(engine.world_events.to_list()) - before_events,
            experiences_created=len(engine.experiences.experiences) - before_experiences,
            events_missed=missed,
            memories_consolidated=len(engine.memory.memories) - before_memories,
            interpretation_count=len(engine.autobiographical_interpretations.interpretations),
            start_time=min(timestamps, default=float(end_time)),
            end_time=float(end_time),
        )
        engine.genesis_replays = [*engine.genesis_replays, result.to_dict()][-8:]
        engine.persistence.log_event(
            engine.identity.name, engine.user_id, engine.timestep,
            "genesis_replay_completed", result.to_dict(),
        )
        engine._persist()
        return result
