"""Strict immutable character cartridge loader and validator.

A cartridge is a TOML `.snp` file that defines authored, character-specific
configuration. Engine modules remain character-agnostic; mutable lived state
belongs in Persistence or a session snapshot.

Wayfarer v2 normalizes portable authored source around a permanent entity UUID,
structured self-model, phenotype namespaces, and progressive-fidelity metadata.
Legacy v1 cartridges remain valid and are normalized into v2 form in memory.
Renderer/model selection remains host/session configuration, never identity.
"""

from __future__ import annotations

import re
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .cartridge_v2 import (
    V1_SCHEMA_VERSION,
    V2_SCHEMA_VERSION,
    V1_TO_V2_MIGRATION_VERSION,
    normalize_schema_version,
    normalized_portable_source,
    parse_self_model,
    validate_entity_uuid,
    validate_phenotype,
    validate_portability,
    validate_self_model,
)
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
    "unanchored_sound", "quiet", "how_are_you", "who_are_you", "what_doing", "statement",
}
_DIALOGUE_SLOTS = {"address", "topic", "memory", "state", "identity"}
_DIALOGUE_STANCES = {"conflicted", "guarded", "trusted", "close"}


def _dialogue_group_allowed(group: str) -> bool:
    if group in _DIALOGUE_GROUPS:
        return True
    base, separator, stance = str(group).partition("__")
    return bool(separator and base in _DIALOGUE_GROUPS and stance in _DIALOGUE_STANCES)


def _validate_dialogue_group_keys(dialogue: dict[str, Any]) -> None:
    unknown = sorted(str(group) for group in dialogue if not _dialogue_group_allowed(str(group)))
    if unknown:
        raise CartridgeError(f"unknown field in [dialogue]: {unknown[0]}")
_OPTIONAL_SECTIONS = {
    "sensory_profile", "voice_profile", "avatar_profile", "cognitive_themes",
    "concealment", "arc", "dialogue",
}
_V2_SECTIONS = {"self_model", "phenotype", "portability"}
_ALLOWED_TOP_LEVEL = set(_REQUIRED) | {"beliefs", "belief_rules"} | _OPTIONAL_SECTIONS | _V2_SECTIONS
_ALLOWED_SECTION_FIELDS = {key: set(value) for key, value in _REQUIRED.items()}
_ALLOWED_SECTION_FIELDS["identity"].update({"model_name", "forbidden_self_claims"})
_ALLOWED_SECTION_FIELDS["metadata"].update({"entity_uuid", "migration_semantics"})
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
    "baseline_energy": (0.0, 1.0), "baseline_tension": (0.0, 1.0),
    "baseline_comfort": (0.0, 1.0), "restlessness_gain": (0.0, 1.0),
    "sensory_load_sensitivity": (0.0, 1.0), "fatigue_decay_rate": (0.0, 1.0),
    "recovery_rate": (0.0, 1.0), "movement_need_gain": (0.0, 1.0),
    "absence_sensitivity": (0.0, 1.0), "ambient_change_sensitivity": (0.0, 1.0),
    "routine_disruption_sensitivity": (0.0, 1.0), "audio_sensitivity": (0.0, 1.0),
    "vision_sensitivity": (0.0, 1.0), "interruption_sensitivity": (0.0, 1.0),
    "silence_sensitivity": (0.0, 1.0), "hesitation_bias": (0.0, 1.0),
}
_ALLOWED_STRING_ENUMS = {"default_rate": {"slow", "normal", "fluid", "fast"}, "default_volume": {"low", "medium", "high"}}


@dataclass(frozen=True)
class Cartridge:
    metadata: dict[str, Any]
    identity: CoreIdentity
    ledger: IdentityLedger
    beliefs: list[dict[str, Any]]
    belief_rules: list[dict[str, Any]]
    voice: dict[str, Any]
    portable_source: dict[str, Any] | None = None


def _unknown_keys(actual: dict[str, Any], allowed: set[str], label: str) -> None:
    unknown = sorted(set(actual) - allowed)
    if unknown:
        raise CartridgeError(f"unknown field in {label}: {unknown[0]}")


def _require_section(data: dict[str, Any], section: str) -> dict[str, Any]:
    value = data.get(section)
    if not isinstance(value, dict):
        raise CartridgeError(f"missing required section [{section}]")
    if section == "dialogue":
        _validate_dialogue_group_keys(value)
    else:
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
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise CartridgeError(f"{label}.{field} must be a list of strings")


def _validate_dialogue(dialogue: dict[str, Any]) -> None:
    _validate_dialogue_group_keys(dialogue)
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
    for index, item in enumerate(value):
        if not isinstance(item, dict):
            raise CartridgeError(f"malformed [[{key}]] item at index {index}")
    return value


def _validate_beliefs(beliefs: list[dict[str, Any]]) -> None:
    seen: set[str] = set()
    for index, belief in enumerate(beliefs):
        _unknown_keys(belief, _ALLOWED_BELIEF, f"[[beliefs]][{index}]")
        for field in _REQUIRED_BELIEF:
            if field not in belief:
                raise CartridgeError(f"missing required field [[beliefs]][{index}].{field}")
        belief_id = str(belief["id"])
        if belief_id in seen:
            raise CartridgeError(f"duplicate belief id: {belief_id}")
        seen.add(belief_id)
        minimum, maximum, initial = float(belief["min"]), float(belief["max"]), float(belief["initial"])
        if minimum > maximum:
            raise CartridgeError(f"belief {belief_id} has min greater than max")
        if not minimum <= initial <= maximum:
            raise CartridgeError(f"belief {belief_id} initial is outside min/max")
        if float(belief["decay_rate"]) < 0:
            raise CartridgeError(f"belief {belief_id} decay_rate must be >= 0")


def _validate_rules(rules: list[dict[str, Any]], beliefs: list[dict[str, Any]]) -> None:
    belief_ids = {str(item["id"]) for item in beliefs}
    for index, rule in enumerate(rules):
        _unknown_keys(rule, _ALLOWED_RULE, f"[[belief_rules]][{index}]")
        for field in _REQUIRED_RULE:
            if field not in rule:
                raise CartridgeError(f"missing required field [[belief_rules]][{index}].{field}")
        if str(rule["belief_id"]) not in belief_ids:
            raise CartridgeError(f"belief rule references unknown belief id: {rule['belief_id']}")
        if int(rule["threshold_count"]) < 1:
            raise CartridgeError(f"belief rule threshold_count must be >= 1 at index {index}")


def _validate_v2_sections(data: dict[str, Any], metadata: dict[str, Any]) -> None:
    if "entity_uuid" not in metadata:
        raise CartridgeError("missing required field [metadata].entity_uuid for schema v2")
    for section in _V2_SECTIONS:
        if section not in data:
            raise CartridgeError(f"missing required section [{section}] for schema v2")
    try:
        validate_entity_uuid(metadata["entity_uuid"])
        validate_self_model(data["self_model"])
        validate_phenotype(data["phenotype"])
        validate_portability(data["portability"])
    except ValueError as exc:
        raise CartridgeError(str(exc)) from exc
    missing = [name for name in data["portability"].get("required_namespaces", []) if name not in data["phenotype"]]
    if missing:
        raise CartridgeError(f"required phenotype namespace is missing: {missing[0]}")


def validate_cartridge_data(data: dict[str, Any]) -> None:
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
    for field in ("core_beliefs", "moral_boundaries", "speech_constraints", "prohibited_mutations"):
        _require_string_list(identity_data, field, "[identity]")
    if "forbidden_self_claims" in identity_data:
        _require_string_list(identity_data, "forbidden_self_claims", "[identity]")
    _require_string_list(voice, "forbidden_lexicon", "[voice]")
    _require_string_list(world, "default_objects", "[world_profile]")

    schema_version = normalize_schema_version(metadata["schema_version"])
    if schema_version not in {V1_SCHEMA_VERSION, V2_SCHEMA_VERSION}:
        raise CartridgeError(f"unsupported cartridge schema_version: {metadata['schema_version']}")
    if schema_version == V1_SCHEMA_VERSION:
        unexpected_v2 = sorted(_V2_SECTIONS & set(data))
        if unexpected_v2:
            raise CartridgeError(f"[{unexpected_v2[0]}] requires [metadata].schema_version = \"2.0\"")
    else:
        _validate_v2_sections(data, metadata)

    beliefs = _require_list(data, "beliefs")
    belief_rules = _require_list(data, "belief_rules")
    _validate_beliefs(beliefs)
    _validate_rules(belief_rules, beliefs)


def _migration_warnings(identity_data: dict[str, Any], source_schema_version: str) -> list[str]:
    """Return only actionable/deprecated-source warnings.

    Silent in-memory normalization of a valid v1 cartridge is ordinary
    compatibility behavior, not a warning condition. The normalized schema and
    migration semantics remain inspectable in ``raw`` metadata.
    """
    warnings: list[str] = []
    if "model_name" in identity_data:
        warnings.append("[identity].model_name is a legacy v1 field and is ignored by Wayfarer; configure the renderer through host/session RendererConfig instead.")
    if source_schema_version == V2_SCHEMA_VERSION and "forbidden_self_claims" in identity_data:
        warnings.append("[identity].forbidden_self_claims is legacy compatibility data in schema v2; prefer structured [self_model] claims and expression restrictions.")
    return warnings


def load_cartridge(path: str) -> tuple[CoreIdentity, IdentityLedger, dict[str, Any]]:
    try:
        with open(path, "rb") as handle:
            data = tomllib.load(handle)
    except tomllib.TOMLDecodeError as exc:
        raise CartridgeError(f"malformed cartridge TOML: {exc}") from exc
    except OSError as exc:
        raise CartridgeError(f"could not read cartridge {path}: {exc}") from exc

    validate_cartridge_data(data)
    metadata, identity_data = data["metadata"], data["identity"]
    source_schema_version = normalize_schema_version(metadata["schema_version"])
    try:
        portable = normalized_portable_source(data)
        self_model = parse_self_model(portable["self_model"])
    except ValueError as exc:
        raise CartridgeError(str(exc)) from exc

    portable_metadata = portable["metadata"]
    combined_forbidden = list(str(x) for x in identity_data.get("forbidden_self_claims", []))
    for phrase in self_model.all_forbidden_expressions():
        if phrase not in combined_forbidden:
            combined_forbidden.append(phrase)

    core = CoreIdentity(
        name=str(metadata["entity_name"]),
        core_beliefs=tuple(str(x) for x in identity_data["core_beliefs"]),
        temperament=str(identity_data["temperament"]),
        moral_boundaries=tuple(str(x) for x in identity_data["moral_boundaries"]),
        speech_constraints=tuple(str(x) for x in identity_data["speech_constraints"]),
        prohibited_mutations=tuple(str(x) for x in identity_data["prohibited_mutations"]),
        entity_uuid=str(portable_metadata["entity_uuid"]),
        self_model=self_model,
        forbidden_self_claims=tuple(combined_forbidden),
        model_name="missing-model-for-mock",
    )
    ledger = IdentityLedger(immutable=core)
    dialogue = data.get("dialogue", {})
    register_dialogue(core.name, dialogue)
    raw = {
        "metadata": metadata, "beliefs": data["beliefs"], "belief_rules": data["belief_rules"],
        "voice": data["voice"], "body_profile": data["body_profile"], "world_profile": data["world_profile"],
        "interpretation_bias": data["interpretation_bias"], "sensory_profile": data.get("sensory_profile", {}),
        "voice_profile": data.get("voice_profile", {}), "avatar_profile": data.get("avatar_profile", {}),
        "cognitive_themes": data.get("cognitive_themes", {}), "concealment": data.get("concealment", {}),
        "arc": data.get("arc", {}), "dialogue": dialogue, "entity_uuid": core.entity_uuid,
        "source_schema_version": source_schema_version, "normalized_schema_version": V2_SCHEMA_VERSION,
        "migration_semantics": portable_metadata.get("migration_semantics", "native-v2"),
        "self_model": portable["self_model"], "phenotype": portable["phenotype"], "portability": portable["portability"],
        "portable_source": portable, "migration_warnings": _migration_warnings(identity_data, source_schema_version),
        "path": str(Path(path)),
    }
    return core, ledger, raw
