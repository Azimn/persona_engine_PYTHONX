"""Character-authored response preferences for soft social triggers."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


ALLOWED_DISPOSITION_RESPONSES = frozenset({
    "none",
    "challenge",
    "deflect",
    "go_quiet",
    "shift_topic",
    "shorten",
    "decline",
})


@dataclass(frozen=True)
class BehavioralDispositionProfile:
    """Compact authored response policy with legacy-compatible defaults."""

    intimacy_too_fast: str = "deflect"
    accusation: str = "challenge"
    contradiction: str = "challenge"
    manipulation: str = "go_quiet"
    boredom: str = "shift_topic"
    disrespect: str = "shorten"
    emotional_overload: str = "go_quiet"

    @classmethod
    def from_dict(cls, raw: dict[str, Any] | None) -> "BehavioralDispositionProfile":
        data = raw if isinstance(raw, dict) else {}
        defaults = cls()
        values: dict[str, str] = {}
        for field_name in cls.__dataclass_fields__:
            value = str(data.get(field_name, getattr(defaults, field_name))).strip().lower()
            if value not in ALLOWED_DISPOSITION_RESPONSES:
                raise ValueError(f"unsupported behavioral disposition response: {field_name}={value}")
            values[field_name] = value
        return cls(**values)

    def response_for(self, trigger: str) -> str | None:
        if trigger not in self.__dataclass_fields__:
            return None
        value = str(getattr(self, trigger))
        return None if value == "none" else value

    def to_dict(self) -> dict[str, str]:
        return {key: str(value) for key, value in asdict(self).items()}
