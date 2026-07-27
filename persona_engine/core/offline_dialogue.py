"""Runtime registry for cartridge-owned offline dialogue.

The registry is process-local infrastructure. Cartridges own all authored wording;
the generic renderer asks for the bank belonging to the active identity. Keeping
this small mapping outside the engine avoids character phrasing in core modules
and remains straightforward to reproduce in a C99 host.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any


_DIALOGUE_BY_IDENTITY: dict[str, dict[str, list[str]]] = {}


def register_dialogue(identity_name: str, dialogue: dict[str, Any] | None) -> None:
    """Register a validated cartridge dialogue bank for one identity."""

    name = str(identity_name or "").strip()
    if not name:
        return
    bank: dict[str, list[str]] = {}
    for group, entries in dict(dialogue or {}).items():
        if isinstance(entries, list):
            bank[str(group)] = [str(entry) for entry in entries]
    _DIALOGUE_BY_IDENTITY[name.casefold()] = bank


def dialogue_for(identity_name: str) -> dict[str, list[str]]:
    """Return an isolated copy so renderers cannot mutate cartridge content."""

    return deepcopy(_DIALOGUE_BY_IDENTITY.get(str(identity_name or "").casefold(), {}))


def clear_dialogue_registry() -> None:
    """Test helper. Runtime code normally never clears authored cartridge data."""

    _DIALOGUE_BY_IDENTITY.clear()
