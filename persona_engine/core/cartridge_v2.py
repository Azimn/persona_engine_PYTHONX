"""Portable `.snp` v2 normalization, migration, and schema helpers.

This module contains authored-source semantics only. It does not own lived
developmental state, renderer selection, or world truth.
"""

from __future__ import annotations

import copy
import re
import uuid
from enum import IntEnum
from typing import Any

from .identity import SelfModel, SelfModelClaim
from .decision_values import validate_value_decision_rules

V1_SCHEMA_VERSION = "1.0"
V2_SCHEMA_VERSION = "2.0"
SELF_MODEL_SCHEMA_VERSION = "1.0"
PHENOTYPE_SCHEMA_VERSION = "1.0"
V1_TO_V2_MIGRATION_VERSION = "wayfarer-v1-to-v2-1"

V1_ENTITY_UUID_NAMESPACE = uuid.UUID("d47d18a4-7890-4d2a-84ab-794851a6d7a1")

SELF_MODEL_MUTABILITY = {"fixed", "developmental", "evidence_revisable", "uncertain"}
SUBSTRATE_AWARENESS_POLICIES = {"unspecified", "opaque", "contextual", "explicit"}
PHENOTYPE_NAMESPACES = {
    "personality", "social_behavior", "values", "behavioral_tendencies",
    "communication", "preferences", "capabilities", "sensory_dispositions",
    "embodiment", "lifestyle_routine", "self_model", "extensions",
}
_SELF_MODEL_FIELDS = {"schema_version", "substrate_awareness", "forbidden_expressions", "claims"}
_SELF_MODEL_CLAIM_FIELDS = {
    "id", "domain", "value", "certainty", "mutability", "expression", "forbidden_expressions",
}
_PHENOTYPE_ROOT_FIELDS = {"schema_version", "state_semantics"} | PHENOTYPE_NAMESPACES
_PORTABILITY_FIELDS = {"minimum_fidelity_level", "preserve_unknown_fields", "required_namespaces"}
_CLAIM_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:-]*$")


class FidelityLevel(IntEnum):
    DESCRIPTIVE_PHENOTYPE = 1
    IDENTITY_CONTINUITY = 2
    DEVELOPMENTAL_PLASTICITY = 3
    SOCIAL_AUTHORITY = 4
    LONGITUDINAL_CROSS_HOST = 5


FIDELITY_LEVEL_SEMANTICS = {
    1: "descriptive phenotype",
    2: "identity and continuity preservation",
    3: "developmental plasticity",
    4: "social embedding and authority",
    5: "longitudinal cross-host continuation",
}


def normalize_schema_version(value: Any) -> str:
    text = str(value).strip()
    if text == "1":
        return V1_SCHEMA_VERSION
    if text == "2":
        return V2_SCHEMA_VERSION
    return text


def derive_v1_entity_uuid(entity_id: str) -> str:
    normalized = str(entity_id).strip().lower()
    if not normalized:
        raise ValueError("legacy entity_id must be non-empty before UUID migration")
    return str(uuid.uuid5(V1_ENTITY_UUID_NAMESPACE, f"wayfarer:v1:{normalized}"))


def validate_entity_uuid(value: Any) -> str:
    try:
        parsed = uuid.UUID(str(value))
    except (ValueError, AttributeError, TypeError) as exc:
        raise ValueError("metadata.entity_uuid must be a valid UUID") from exc
    return str(parsed)


def _string_list(value: Any, label: str) -> list[str]:
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise ValueError(f"{label} must be a list of strings")
    return [str(item) for item in value]


def validate_self_model(data: Any) -> None:
    if not isinstance(data, dict):
        raise ValueError("[self_model] must be a table")
    unknown = sorted(set(data) - _SELF_MODEL_FIELDS)
    if unknown:
        raise ValueError(f"unknown field in [self_model]: {unknown[0]}")
    if normalize_schema_version(data.get("schema_version", SELF_MODEL_SCHEMA_VERSION)) != SELF_MODEL_SCHEMA_VERSION:
        raise ValueError("unsupported [self_model].schema_version")
    awareness = str(data.get("substrate_awareness", "unspecified"))
    if awareness not in SUBSTRATE_AWARENESS_POLICIES:
        raise ValueError(f"unsupported [self_model].substrate_awareness: {awareness}")
    _string_list(data.get("forbidden_expressions", []), "[self_model].forbidden_expressions")
    claims = data.get("claims", [])
    if not isinstance(claims, list):
        raise ValueError("[[self_model.claims]] must be an array of tables")
    seen: set[str] = set()
    for index, claim in enumerate(claims):
        if not isinstance(claim, dict):
            raise ValueError(f"malformed [[self_model.claims]] item at index {index}")
        unknown_claim = sorted(set(claim) - _SELF_MODEL_CLAIM_FIELDS)
        if unknown_claim:
            raise ValueError(f"unknown field in [[self_model.claims]][{index}]: {unknown_claim[0]}")
        for required in ("id", "domain", "value"):
            if required not in claim:
                raise ValueError(f"missing required [[self_model.claims]][{index}].{required}")
        claim_id = str(claim["id"]).strip()
        if not _CLAIM_ID_RE.match(claim_id):
            raise ValueError(f"invalid self-model claim id: {claim_id}")
        if claim_id in seen:
            raise ValueError(f"duplicate self-model claim id: {claim_id}")
        seen.add(claim_id)
        if not str(claim["domain"]).strip():
            raise ValueError(f"self-model claim domain must be non-empty: {claim_id}")
        certainty = float(claim.get("certainty", 1.0))
        if not 0.0 <= certainty <= 1.0:
            raise ValueError(f"self-model claim certainty must be within [0, 1]: {claim_id}")
        mutability = str(claim.get("mutability", "fixed"))
        if mutability not in SELF_MODEL_MUTABILITY:
            raise ValueError(f"unsupported self-model mutability for {claim_id}: {mutability}")
        if "expression" in claim and not isinstance(claim["expression"], str):
            raise ValueError(f"self-model claim expression must be a string: {claim_id}")
        _string_list(claim.get("forbidden_expressions", []), f"[[self_model.claims]][{index}].forbidden_expressions")


def parse_self_model(data: dict[str, Any]) -> SelfModel:
    validate_self_model(data)
    claims = tuple(
        SelfModelClaim(
            claim_id=str(item["id"]),
            domain=str(item["domain"]),
            value=copy.deepcopy(item["value"]),
            certainty=float(item.get("certainty", 1.0)),
            mutability=str(item.get("mutability", "fixed")),
            expression=str(item.get("expression", "")),
            forbidden_expressions=tuple(str(x) for x in item.get("forbidden_expressions", [])),
        )
        for item in data.get("claims", [])
    )
    return SelfModel(
        schema_version=SELF_MODEL_SCHEMA_VERSION,
        substrate_awareness=str(data.get("substrate_awareness", "unspecified")),
        claims=claims,
        forbidden_expressions=tuple(str(x) for x in data.get("forbidden_expressions", [])),
    )


def validate_phenotype(data: Any) -> None:
    if not isinstance(data, dict):
        raise ValueError("[phenotype] must be a table")
    unknown = sorted(set(data) - _PHENOTYPE_ROOT_FIELDS)
    if unknown:
        raise ValueError(f"unknown phenotype namespace: {unknown[0]}; preserve external fields under phenotype.extensions")
    if normalize_schema_version(data.get("schema_version", PHENOTYPE_SCHEMA_VERSION)) != PHENOTYPE_SCHEMA_VERSION:
        raise ValueError("unsupported [phenotype].schema_version")
    if str(data.get("state_semantics", "authored_baseline")) != "authored_baseline":
        raise ValueError("[phenotype].state_semantics must be authored_baseline")
    for namespace in PHENOTYPE_NAMESPACES:
        if namespace in data and not isinstance(data[namespace], dict):
            raise ValueError(f"[phenotype.{namespace}] must be a table")
    values = data.get("values", {})
    if "decision_rules" in values:
        try:
            validate_value_decision_rules(values["decision_rules"])
        except ValueError as exc:
            raise ValueError(f"[phenotype.values].decision_rules: {exc}") from exc


def validate_portability(data: Any) -> None:
    if not isinstance(data, dict):
        raise ValueError("[portability] must be a table")
    unknown = sorted(set(data) - _PORTABILITY_FIELDS)
    if unknown:
        raise ValueError(f"unknown field in [portability]: {unknown[0]}")
    level = int(data.get("minimum_fidelity_level", FidelityLevel.IDENTITY_CONTINUITY))
    if level not in FIDELITY_LEVEL_SEMANTICS:
        raise ValueError("[portability].minimum_fidelity_level must be within 1..5")
    if data.get("preserve_unknown_fields", True) is not True:
        raise ValueError("[portability].preserve_unknown_fields must be true")
    required = _string_list(data.get("required_namespaces", []), "[portability].required_namespaces")
    unknown_required = sorted(set(required) - PHENOTYPE_NAMESPACES)
    if unknown_required:
        raise ValueError(f"unknown required phenotype namespace: {unknown_required[0]}")


def runtime_supports_portable_source(portability: dict[str, Any], runtime_fidelity_level: int) -> bool:
    validate_portability(portability)
    return int(runtime_fidelity_level) >= int(portability.get("minimum_fidelity_level", FidelityLevel.IDENTITY_CONTINUITY))


def migrate_v1_to_v2_data(data: dict[str, Any]) -> dict[str, Any]:
    source_version = normalize_schema_version(data.get("metadata", {}).get("schema_version", ""))
    if source_version == V2_SCHEMA_VERSION:
        return copy.deepcopy(data)
    if source_version != V1_SCHEMA_VERSION:
        raise ValueError(f"cannot migrate unsupported cartridge schema_version: {source_version}")

    migrated = copy.deepcopy(data)
    metadata = migrated.setdefault("metadata", {})
    metadata["schema_version"] = V2_SCHEMA_VERSION
    metadata["entity_uuid"] = derive_v1_entity_uuid(str(metadata.get("entity_id", "")))
    metadata["migration_semantics"] = V1_TO_V2_MIGRATION_VERSION

    identity = migrated.get("identity", {})
    legacy_forbidden = [str(x) for x in identity.get("forbidden_self_claims", [])]
    migrated["self_model"] = {
        "schema_version": SELF_MODEL_SCHEMA_VERSION,
        "substrate_awareness": "unspecified",
        "forbidden_expressions": legacy_forbidden,
        "claims": [],
    }
    migrated["phenotype"] = {
        "schema_version": PHENOTYPE_SCHEMA_VERSION,
        "state_semantics": "authored_baseline",
        "personality": {"temperament": identity.get("temperament", ""), "core_beliefs": copy.deepcopy(identity.get("core_beliefs", []))},
        "social_behavior": {},
        "values": {
            "moral_boundaries": copy.deepcopy(identity.get("moral_boundaries", [])),
            "decision_rules": copy.deepcopy(migrated.get("value_profile", {})),
        },
        "behavioral_tendencies": {"prohibited_mutations": copy.deepcopy(identity.get("prohibited_mutations", []))},
        "communication": {"speech_constraints": copy.deepcopy(identity.get("speech_constraints", [])), "voice": copy.deepcopy(migrated.get("voice", {}))},
        "preferences": {},
        "capabilities": {},
        "sensory_dispositions": copy.deepcopy(migrated.get("sensory_profile", {})),
        "embodiment": {"body_profile": copy.deepcopy(migrated.get("body_profile", {})), "avatar_profile": copy.deepcopy(migrated.get("avatar_profile", {}))},
        "lifestyle_routine": {"world_profile": copy.deepcopy(migrated.get("world_profile", {}))},
        "self_model": {"legacy_forbidden_expressions": legacy_forbidden},
        "extensions": {},
    }
    migrated["portability"] = {
        "minimum_fidelity_level": int(FidelityLevel.IDENTITY_CONTINUITY),
        "preserve_unknown_fields": True,
        "required_namespaces": ["self_model"],
    }
    return migrated


def normalized_portable_source(data: dict[str, Any]) -> dict[str, Any]:
    version = normalize_schema_version(data.get("metadata", {}).get("schema_version", ""))
    if version == V1_SCHEMA_VERSION:
        return migrate_v1_to_v2_data(data)
    if version == V2_SCHEMA_VERSION:
        return copy.deepcopy(data)
    raise ValueError(f"unsupported cartridge schema_version: {version}")
