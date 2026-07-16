"""Strict immutable character cartridge loader and validator.

A cartridge is a TOML `.snp` file that defines authored, character-specific
configuration. Engine modules must remain character-agnostic; mutable lived
state belongs in Persistence or a session snapshot.
"""

from __future__ import annotations

import tomllib
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .identity import CoreIdentity, IdentityLedger


class CartridgeError(ValueError):
    """Raised when a cartridge is missing required fields or is malformed."""


_REQUIRED = {
    "metadata": ("entity_id", "entity_name", "schema_version"),
    "identity": ("core_beliefs", "temperament", "moral_boundaries", "speech_constraints", "prohibited_mutations", "model_name"),
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
_OPTIONAL_SECTIONS = {"sensory_profile", "voice_profile", "avatar_profile", "cognitive_themes", "concealment", "arc", "intrinsic", "offline_expression"}
_ALLOWED_TOP_LEVEL = set(_REQUIRED) | {"beliefs", "belief_rules"} | _OPTIONAL_SECTIONS
_ALLOWED_SECTION_FIELDS = {k: set(v) for k, v in _REQUIRED.items()}
_ALLOWED_SECTION_FIELDS.update({
    "sensory_profile": {"audio_sensitivity", "vision_sensitivity", "interruption_sensitivity", "silence_sensitivity"},
    "voice_profile": {"default_rate", "default_volume", "hesitation_bias", "interruptible"},
    "avatar_profile": {"default_face", "guarded_face", "tired_face", "attention_style", "overloaded_face", "restless_motion"},
    "cognitive_themes": {"allowed", "retrieval_filters"},
    "concealment": {"weights"},
    "arc": {"earned_changes"},
    "intrinsic": {"selection_interval_ticks", "wants", "activities"},
    "offline_expression": {
        "identity_boundary", "sound", "ambiguous", "repair", "care", "slow",
        "memory", "greeting", "quiet", "question", "default",
    },
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
    for field in _REQUIRED.get(section, ()):  # typed dict would be overkill here
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


def _validate_intrinsic(section: dict[str, Any]) -> None:
    from .intrinsic import ACTION_TYPES

    wants = section.get("wants", [])
    activities = section.get("activities", [])
    if not isinstance(wants, list) or not isinstance(activities, list):
        raise CartridgeError("[intrinsic] wants and activities must be arrays")
    if int(section.get("selection_interval_ticks", 6)) < 1:
        raise CartridgeError("[intrinsic].selection_interval_ticks must be >= 1")
    want_fields = {"id", "description", "baseline", "neglect_gain", "satisfaction"}
    activity_fields = {
        "id", "want_id", "description", "intention", "attention_target", "action_type", "target",
        "base_utility", "energy_cost", "novelty_weight", "interruptible", "visibility",
        "performance_cue", "pressure_affinities",
    }
    want_ids: set[str] = set()
    for index, want in enumerate(wants):
        if not isinstance(want, dict):
            raise CartridgeError(f"[intrinsic].wants[{index}] must be a table")
        _unknown_keys(want, want_fields, f"[intrinsic].wants[{index}]")
        if not want_fields.issubset(want):
            raise CartridgeError(f"[intrinsic].wants[{index}] is missing a required field")
        want_id = str(want["id"])
        if not want_id or want_id in want_ids:
            raise CartridgeError(f"duplicate or empty intrinsic want id: {want_id}")
        want_ids.add(want_id)
        for field in ("baseline", "neglect_gain", "satisfaction"):
            number = float(want[field])
            if not math.isfinite(number) or not 0.0 <= number <= 1.0:
                raise CartridgeError(f"[intrinsic].wants[{index}].{field} must be within [0, 1]")
    activity_ids: set[str] = set()
    required_activity = activity_fields - {"pressure_affinities"}
    for index, activity in enumerate(activities):
        if not isinstance(activity, dict):
            raise CartridgeError(f"[intrinsic].activities[{index}] must be a table")
        _unknown_keys(activity, activity_fields, f"[intrinsic].activities[{index}]")
        if not required_activity.issubset(activity):
            raise CartridgeError(f"[intrinsic].activities[{index}] is missing a required field")
        activity_id = str(activity["id"])
        if not activity_id or activity_id in activity_ids:
            raise CartridgeError(f"duplicate or empty intrinsic activity id: {activity_id}")
        activity_ids.add(activity_id)
        if str(activity["want_id"]) not in want_ids:
            raise CartridgeError(f"intrinsic activity references unknown want: {activity['want_id']}")
        if str(activity["action_type"]) not in ACTION_TYPES:
            raise CartridgeError(f"unsupported intrinsic action_type: {activity['action_type']}")
        for field in ("energy_cost", "novelty_weight"):
            number = float(activity[field])
            if not math.isfinite(number) or not 0.0 <= number <= 1.0:
                raise CartridgeError(f"[intrinsic].activities[{index}].{field} must be within [0, 1]")
        base_utility = float(activity["base_utility"])
        if not math.isfinite(base_utility) or not -1.0 <= base_utility <= 1.0:
            raise CartridgeError(f"[intrinsic].activities[{index}].base_utility must be within [-1, 1]")
        affinities = activity.get("pressure_affinities", {})
        if not isinstance(affinities, dict) or not all(
            isinstance(key, str) and isinstance(value, (int, float))
            and math.isfinite(float(value)) and -1.0 <= float(value) <= 1.0
            for key, value in affinities.items()
        ):
            raise CartridgeError(f"[intrinsic].activities[{index}].pressure_affinities must be numeric")


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
    if "intrinsic" in data:
        _validate_intrinsic(data["intrinsic"])
    if "offline_expression" in data:
        for field in _ALLOWED_SECTION_FIELDS["offline_expression"]:
            if field in data["offline_expression"]:
                _require_string_list(data["offline_expression"], field, "[offline_expression]")
                if not data["offline_expression"][field]:
                    raise CartridgeError(f"[offline_expression].{field} must not be empty")
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


def load_cartridge(path: str) -> tuple[CoreIdentity, IdentityLedger, dict[str, Any]]:
    """Load a `.snp` TOML cartridge.

    Returns `(CoreIdentity, IdentityLedger, raw_rules)` where `raw_rules`
    contains schema-validated data for downstream components.
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
        model_name=str(identity_data["model_name"]),
    )
    ledger = IdentityLedger(immutable=core)
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
        "intrinsic": data.get("intrinsic", {}),
        "offline_expression": data.get("offline_expression", {}),
        "path": str(Path(path)),
    }
    return core, ledger, raw
