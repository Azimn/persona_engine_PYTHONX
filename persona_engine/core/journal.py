"""Bounded character-owned notebook with a plain-text materialization."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
import math
from pathlib import Path
from typing import Any, Mapping, Sequence


JOURNAL_ENTRY_KINDS = frozenset({"private_note", "reflection", "research_note", "field_note"})


def _entry_id(*parts: object) -> str:
    payload = json.dumps([str(item) for item in parts], separators=(",", ":")).encode("utf-8")
    return "journal_" + hashlib.blake2b(payload, digest_size=8).hexdigest()


@dataclass(frozen=True)
class JournalEntry:
    schema_version: int
    entry_id: str
    tick: int
    timestamp: float
    text: str
    entry_kind: str
    source: str
    source_event_ids: tuple[str, ...]
    historical_year: int | None = None

    def __post_init__(self) -> None:
        if self.entry_kind not in JOURNAL_ENTRY_KINDS:
            raise ValueError(f"unsupported journal entry kind: {self.entry_kind}")
        if not math.isfinite(float(self.timestamp)):
            raise ValueError("journal timestamp must be finite")
        if not self.text.strip() or len(self.text) > 4000:
            raise ValueError("journal text must contain 1..4000 characters")
        if len(self.source_event_ids) > 12:
            raise ValueError("journal source-event bound exceeded")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "JournalEntry":
        raw = {key: value[key] for key in cls.__dataclass_fields__ if key in value}
        raw["source_event_ids"] = tuple(raw.get("source_event_ids", ()))
        raw.setdefault("historical_year", None)
        return cls(**raw)


class PersonalJournal:
    MAX_ENTRIES = 256

    def __init__(self, object_name: str = "personal notebook", entries: Sequence[JournalEntry] = ()):
        self.object_name = str(object_name)[:120] or "personal notebook"
        if len(entries) > self.MAX_ENTRIES:
            raise ValueError("journal entry bound exceeded")
        self.entries = list(entries)

    def write(
        self, *, tick: int, timestamp: float, text: str, entry_kind: str,
        source: str, source_event_ids: Sequence[str] = (), historical_year: int | None = None,
    ) -> JournalEntry:
        entry = JournalEntry(
            schema_version=1,
            entry_id=_entry_id(tick, timestamp, text, len(self.entries)),
            tick=int(tick),
            timestamp=float(timestamp),
            text=str(text).strip(),
            entry_kind=str(entry_kind),
            source=str(source)[:120],
            source_event_ids=tuple(dict.fromkeys(str(item) for item in source_event_ids))[-12:],
            historical_year=int(historical_year) if historical_year is not None else None,
        )
        if any(item.entry_id == entry.entry_id for item in self.entries):
            return next(item for item in self.entries if item.entry_id == entry.entry_id)
        if len(self.entries) >= self.MAX_ENTRIES:
            raise ValueError("journal is full; archive before writing another entry")
        self.entries.append(entry)
        return entry

    def search(self, query: str = "", limit: int = 8) -> tuple[JournalEntry, ...]:
        words = {word for word in str(query).lower().split() if len(word) > 2}
        candidates = self.entries
        if words:
            candidates = [item for item in candidates if words & set(item.text.lower().split())]
        return tuple(sorted(candidates, key=lambda item: (item.timestamp, item.entry_id), reverse=True)[:max(0, min(16, int(limit)))])

    def render_text(self) -> str:
        lines = [self.object_name, "=" * len(self.object_name), ""]
        for item in sorted(self.entries, key=lambda entry: (entry.timestamp, entry.entry_id)):
            date = str(item.historical_year) if item.historical_year is not None else f"tick {item.tick}"
            lines.extend((f"[{date}]", item.text, ""))
        return "\n".join(lines).rstrip() + "\n"

    def materialize(self, path: str | Path) -> Path:
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(self.render_text(), encoding="utf-8")
        return target

    def to_dict(self) -> dict[str, Any]:
        return {"object_name": self.object_name, "entries": [item.to_dict() for item in self.entries]}

    @classmethod
    def from_dict(cls, value: Mapping[str, Any] | None, object_name: str = "personal notebook") -> "PersonalJournal":
        source = dict(value or {})
        return cls(
            object_name=str(source.get("object_name", object_name)),
            entries=tuple(JournalEntry.from_dict(item) for item in source.get("entries", ())),
        )
