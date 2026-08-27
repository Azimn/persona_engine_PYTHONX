"""Strict immutable character cartridge loader and validator.

A cartridge is a TOML `.snp` file that defines authored, character-specific
configuration. Engine modules must remain character-agnostic; mutable lived
state belongs in Persistence or a session snapshot.

Wayfarer renderer rule: renderer/model selection is host/session configuration,
not character identity. Schema v1 cartridges may still contain the historical
``[identity].model_name`` field for backward compatibility, but the loader does
not grant that field renderer-selection authority.
"""

from __future__ import annotations

import re
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .identity import CoreIdentity, IdentityLedger
from .offline_dialogue import register_dialogue


class CartridgeError(ValueError):
    """Raised when a cartridge is missing required fields or is malformed."""


_REQUIRED = {
    "metadata": ("entity_id", "entity_name", "schema_version"),
    "identity": ("core_beliefs", "temperament", "moral_boundaries", "speech_constraints", "prohibited_mutations"),
    "voice": ("forbidden_lexicon", "speaking_style", "address_user_as"),
    "body_profile": (
        "baseline_energy", "baseline_tension", "baseline_comfort", "restlessness_gain",
        "stillness_discomfort_threshold_seconds", "sensory_load_sensitivity",
        "fatigue_decay_rate", "recovery_rate", "movement_need_gain",
        "preferred_posture", "preferred_orientation",
    ),
    "world_profile": (
        "preferred_light", "preferred_noise", "absence_sensitivity", "ambient_change_sensitivity",
        "routine_disruption_sensitivity", "default_zone", "default_objects", "ambient_change_bias",
    ),
    "interpretation_bias": ("silence_low_trust", "silence_high_trust", "ambiguous_sound", "identity_attack"),
}
_DIALOGUE_GROUPS = {
    "identity_boundary", "greeting", "repair", "care", "thanks", "agreement",
    "disagreement", "uncertain", "question", "memory", "memory_missing", "sound",
    "unanchored_sound", "quiet", "how_are_you", "who_are_you", "what_doing",
    "statement",
}
_DIALOGUE_SLOTS = {"address", "topic", "memory", "state", "identity"}
_OPTIONAL_SECTIONS = {
    "sensory_profile", "voice_profile", "avatar_profile", "cognitive_themes",
    "concealment", "arc", "dialogue",
}
_ALLOWED_TOP_LEVEL = set(_REQUIRED) | {"beliefs", "belief_rules"} | _OPTIONAL_SECTIONS
_ALLOWED_SECTION_FIELDS = {k: set(v) for k, v in _REQUIRED.items()}
# v1 compatibility only. The field is accepted so existing cartridges continue
# to load, but it is not part of the Wayfarer identity contract and is ignored
# for renderer selection.
_ALLOWED_SECTION_FIELDS["identity"].add("model_name")
_ALLOWED_SECTION_FIELDS.update({
    "sensory_profile": {"audio_sensitivity", "vision_sensitivity", "interruption_sensitivity", "silence_sensitivity"},
    "voice_profile": {"default_rate", "default_volume", "hesitation_bias", "interruptible"},
    "avatar_profile": {"default_face", "guarded_face", "tired_face", "attention_style", "overloaded_face", "restless_motion"},
    "cognitive_themes": {"allowed", "retrieval_filters"},
    "concealment": {"weights"},
    "arc": {"earned_changes"},
    "dialogue": _DIALOGUE_GROUPS,
})
_REQUIRED_BELIEF = ("id", "initial", "min", "max", "decay_rate", "description")
_ALLOWED_BELIEF = set(_REQUIRED_BELIEF) | {"fixed", "disclosure"}
_REQUIRED_RULE = ("belief_id", "trigger_memory_type", "threshold_count", "delta")
_ALLOWED_RULE = set(_REQUIRED_RULE)

_NUMERIC_RANGES = {
    "baseline_energy": (0.0, 1.0),
    "baseline_tension": (0.0, 1.0),
    "baseline_comfort": (0.0, 1.0),
    "restlessness_gain": (0.0, 1.0),
    "sensory_load_sensitivity": (0.0, 1.0),
    "fatigue_decay_rate": (0.0, 1.0),
    "recovery_rate": (0.0, 1.0),
    "movement_need_gain": (0.0, 1.0),
    "absence_sensitivity": (0.0, 1.0),
    "ambient_change_sensitivity": (0.0, 1.0),
    "routine_disruption_sensitivity": (0.0, 1.0),
    "audio_sensitivity": (0.0, 1.0),
    "vision_sensitivity": (0.0, 1.0),
    "interruption_sensitivity": (0.0, 1.0),
    "silence_sensitivity": (0.0, 1.0),
    "hesitation_bias": (0.0, 1.0),
}

_ALLOWED_STRING_ENUMS = {
    "default_rate": {"slow", "normal", "fluid", "fast"},
    "default_volume": {"low", "medium", "high"},
}


@dataclass(frozen=True)
class Cartridge:
    metadata: dict[str, Any]
    identity: CoreIdentity
    ledger: IdentityLedger
    beliefs: list[dict[str, Any]]
    belief_rules: list[dict[str, Any]]
    voice: dict[str, Any]


def _unknown_keys(actual: dict[str, Any], allowed: set[str], label: str) -> None:
    unknown = sorted(set(actual) - allowed)
    if unknown:
        raise CartridgeError(f"unknown field in {label}: {unknown[0]}")


def _require_section(data: dict[str, Any], section: str) -> dict[str, Any]:
    value = data.get(section)
    if not isinstance(value, dict):
        raise CartridgeError(f"missing required section [{section}]")
    _unknown_keys(value, _ALLOWED_SECTION_FIELDS[section], f"[{section}]")
    for field in _REQUIRED.get(section, ()):
        if field not in value:
            raise CartridgeError(f"missing required field [{section}].{field}")
    for field, (lo, hi) in _NUMERIC_RANGES.items():
        if field in value:
            try:
                number = float(value[field])
            except (TypeError, ValueError) as exc:
                raise CartridgeError(f"[{section}].{field} must be numeric") from exc
            if not lo <= number <= hi:
                raise CartridgeError(f"[{section}].{field} must be within [{lo}, {hi}]")
    if "stillness_discomfort_threshold_seconds" in value and float(value["stillness_discomfort_threshold_seconds"]) < 0:
        raise CartridgeError(f"[{section}].stillness_discomfort_threshold_seconds must be >= 0")
    for field, allowed_values in _ALLOWED_STRING_ENUMS.items():
        if field in value and str(value[field]) not in allowed_values:
            raise CartridgeError(f"[{section}].{field} has unsupported value: {value[field]}")
    return value


def _require_string_list(section: dict[str, Any], field: str, label: str) -> None:
    value = section.get(field)
    if not isinstance(value, list) or not all(isinstance(x, str) for x in value):
        raise CartridgeError(f"{label}.{field} must be a list of strings")


def _validate_dialogue(dialogue: dict[str, Any]) -> None:
    _unknown_keys(dialogue, _DIALOGUE_GROUPS, "[dialogue]")
    slot_pattern = re.compile(r"\{([a-zA-Z_][a-zA-Z0-9_]*)\}")
    for group, entries in dialogue.items():
        if not isinstance(entries, list) or not entries or not all(isinstance(entry, str) and entry.strip() for entry in entries):
            raise CartridgeError(f"[dialogue].{group} must be a non-empty list of strings")
        for entry in entries:
            unknown_slots = sorted(set(slot_pattern.findall(entry)) - _DIALOGUE_SLOTS)
            if unknown_slots:
                raise CartridgeError(f"unsupported dialogue slot in [dialogue].{group}: {unknown_slots[0]}")


def _require_list(data: dict[str, Any], key: str) -> list[dict[str, Any]]:
    value = data.get(key)
    if not isinstance(value, list):
        raise CartridgeError(f"missing or malformed required array [[{key}]]")
    for idx, item in enumerate(value):
        if not isinstance(item, dict):
            raise CartridgeError(f"malformed [[{key}]] item at index {idx}")
    return value


def _validate_beliefs(beliefs: list[dict[str, Any]]) -> None:
    seen: set[str] = set()
    for idx, belief in enumerate(beliefs):
        _unknown_keys(belief, _ALLOWED_BELIEF, f"[[beliefs]][{idx}]")
        for field in _REQUIRED_BELIEF:
            if field not in belief:
                raise CartridgeError(f"missing required field [[beliefs]][{idx}].{field}")
        bid = str(belief["id"])
        if bid in seen:
            raise CartridgeError(f"duplicate belief id: {bid}")
        seen.add(bid)
        min_v = float(belief["min"])
        max_v = float(belief["max"])
        if min_v > max_v:
            raise CartridgeError(f"belief {bid} has min greater than max")
        initial = float(belief["initial"])
        if not (min_v <= initial <= max_v):
            raise CartridgeError(f"belief {bid} initial is outside min/max")
        if float(belief["decay_rate"]) < 0:
            raise CartridgeError(f"belief {bid} decay_rate must be >= 0")


def _validate_rules(rules: list[dict[str, Any]], beliefs: list[dict[str, Any]]) -> None:
    belief_ids = {str(b["id"]) for b in beliefs}
    for idx, rule in enumerate(rules):
        _unknown_keys(rule, _ALLOWED_RULE, f"[[belief_rules]][{idx}]")
        for field in _REQUIRED_RULE:
            if field not in rule:
                raise CartridgeError(f"missing required field [[belief_rules]][{idx}].{field}")
        if str(rule["belief_id"]) not in belief_ids:
            raise CartridgeError(f"belief rule references unknown belief id: {rule['belief_id']}")
        if int(rule["threshold_count"]) < 1:
            raise CartridgeError(f"belief rule threshold_count must be >= 1 at index {idx}")


def validate_cartridge_data(data: dict[str, Any]) -> None:
    """Validate raw TOML data before constructing runtime objects."""

    _unknown_keys(data, _ALLOWED_TOP_LEVEL, "top level")
    metadata = _require_section(data, "metadata")
    identity_data = _require_section(data, "identity")
    voice = _require_section(data, "voice")
    _require_section(data, "body_profile")
    world = _require_section(data, "world_profile")
    _require_section(data, "interpretation_bias")
    for optional_section in _OPTIONAL_SECTIONS:
        if optional_section in data:
            _require_section(data, optional_section)
    if "cognitive_themes" in data:
        _require_string_list(data["cognitive_themes"], "allowed", "[cognitive_themes]")
    if "dialogue" in data:
        _validate_dialogue(data["dialogue"])
    _require_string_list(identity_data, "core_beliefs", "[identity]")
    _require_string_list(identity_data, "moral_boundaries", "[identity]")
    _require_string_list(identity_data, "speech_constraints", "[identity]")
    _require_string_list(identity_data, "prohibited_mutations", "[identity]")
    _require_string_list(voice, "forbidden_lexicon", "[voice]")
    _require_string_list(world, "default_objects", "[world_profile]")
    if str(metadata["schema_version"]) != "1.0":
        raise CartridgeError(f"unsupported cartridge schema_version: {metadata['schema_version']}")
    beliefs = _require_list(data, "beliefs")
    belief_rules = _require_list(data, "belief_rules")
    _validate_beliefs(beliefs)
    _validate_rules(belief_rules, beliefs)


def _migration_warnings(identity_data: dict[str, Any]) -> list[str]:
    warnings: list[str] = []
    if "model_name" in identity_data:
        warnings.append(
            "[identity].model_name is a legacy v1 field and is ignored by Wayfarer; "
            "configure the renderer through host/session RendererConfig instead."
        )
    return warnings


def load_cartridge(path: str) -> tuple[CoreIdentity, IdentityLedger, dict[str, Any]]:
    """Load a `.snp` TOML cartridge.

    Returns ``(CoreIdentity, IdentityLedger, raw_rules)`` where ``raw_rules``
    contains schema-validated data for downstream components.

    Legacy v1 ``[identity].model_name`` is accepted but deliberately ignored.
    Cartridge loading always selects the deterministic offline compatibility
    renderer hint; host/session code may replace the renderer through the
    approved renderer-control path.
    """

    try:
        with open(path, "rb") as handle:
            data = tomllib.load(handle)
    except tomllib.TOMLDecodeError as exc:
        raise CartridgeError(f"malformed cartridge TOML: {exc}") from exc
    except OSError as exc:
        raise CartridgeError(f"could not read cartridge {path}: {exc}") from exc

    validate_cartridge_data(data)
    metadata = data["metadata"]
    identity_data = data["identity"]
    core = CoreIdentity(
        name=str(metadata["entity_name"]),
        core_beliefs=tuple(str(x) for x in identity_data["core_beliefs"]),
        temperament=str(identity_data["temperament"]),
        moral_boundaries=tuple(str(x) for x in identity_data["moral_boundaries"]),
        speech_constraints=tuple(str(x) for x in identity_data["speech_constraints"]),
        prohibited_mutations=tuple(str(x) for x in identity_data["prohibited_mutations"]),
        # Compatibility only. The authored cartridge is not allowed to choose
        # its execution substrate. UI/host RendererConfig owns that decision.
        model_name="missing-model-for-mock",
    )
    ledger = IdentityLedger(immutable=core)
    dialogue = data.get("dialogue", {})
    register_dialogue(core.name, dialogue)
    raw = {
        "metadata": metadata,
        "beliefs": data["beliefs"],
        "belief_rules": data["belief_rules"],
        "voice": data["voice"],
        "body_profile": data["body_profile"],
        "world_profile": data["world_profile"],
        "interpretation_bias": data["interpretation_bias"],
        "sensory_profile": data.get("sensory_profile", {}),
        "voice_profile": data.get("voice_profile", {}),
        "avatar_profile": data.get("avatar_profile", {}),
        "cognitive_themes": data.get("cognitive_themes", {}),
        "concealment": data.get("concealment", {}),
        "arc": data.get("arc", {}),
        "dialogue": dialogue,
        "migration_warnings": _migration_warnings(identity_data),
        "path": str(Path(path)),
    }
    return core, ledger, raw
