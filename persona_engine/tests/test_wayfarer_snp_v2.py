"""Wayfarer `.snp` v2 portability, ontology, and migration contracts."""

from copy import deepcopy
from pathlib import Path
import tomllib

import pytest

from persona_engine.agent import CharacterAgent
from persona_engine.core.cartridge import CartridgeError, load_cartridge, validate_cartridge_data
from persona_engine.core.cartridge_v2 import (
    V1_TO_V2_MIGRATION_VERSION,
    derive_v1_entity_uuid,
    migrate_v1_to_v2_data,
    runtime_supports_portable_source,
)
from persona_engine.core.identity import CoreIdentity

ROOT = Path(__file__).resolve().parents[1]


def _read(name: str) -> dict:
    with open(ROOT / "cartridges" / name, "rb") as handle:
        return tomllib.load(handle)


def test_v1_normalizes_to_stable_v2_identity_without_rewriting_source():
    core, _, raw = load_cartridge(str(ROOT / "cartridges" / "neutral.snp"))
    assert raw["source_schema_version"] == "1.0"
    assert raw["normalized_schema_version"] == "2.0"
    assert raw["metadata"]["schema_version"] == "1.0"
    assert raw["portable_source"]["metadata"]["schema_version"] == "2.0"
    assert raw["migration_semantics"] == V1_TO_V2_MIGRATION_VERSION
    assert core.entity_uuid == derive_v1_entity_uuid("neutral")
    again, _, raw_again = load_cartridge(str(ROOT / "cartridges" / "neutral.snp"))
    assert again.entity_uuid == core.entity_uuid
    assert raw_again["portable_source"]["metadata"]["entity_uuid"] == core.entity_uuid


def test_v1_forbidden_self_claims_are_preserved_in_structured_v2_compatibility():
    data = _read("neutral.snp")
    migrated = migrate_v1_to_v2_data(data)
    assert migrated["self_model"]["forbidden_expressions"] == data["identity"]["forbidden_self_claims"]
    assert migrated["phenotype"]["state_semantics"] == "authored_baseline"
    assert migrated["portability"]["preserve_unknown_fields"] is True


def test_native_v2_artificial_and_human_self_models_load_under_same_engine():
    aster, _, aster_raw = load_cartridge(str(ROOT / "cartridges" / "aster_v2.snp"))
    mara, _, mara_raw = load_cartridge(str(ROOT / "cartridges" / "mara_v2.snp"))
    assert aster_raw["source_schema_version"] == "2.0"
    assert mara_raw["source_schema_version"] == "2.0"
    assert aster.self_model.claim("ontology.kind").value == "synthetic_person"
    assert mara.self_model.claim("ontology.kind").value == "human_person"
    assert "i am a biological human" in aster.forbidden_self_claims
    assert "i am an ai" in mara.forbidden_self_claims


def test_structured_self_model_drives_runtime_ontology_without_engine_human_ai_rule(tmp_path):
    aster = CharacterAgent(cartridge_path=str(ROOT / "cartridges" / "aster_v2.snp"), user_id="aster", db_path=str(tmp_path / "aster.db"))
    mara = CharacterAgent(cartridge_path=str(ROOT / "cartridges" / "mara_v2.snp"), user_id="mara", db_path=str(tmp_path / "mara.db"))
    aster.engine.renderer.generate_expression = lambda request: "I am an AI."
    mara.engine.renderer.generate_expression = lambda request: "I am an AI."
    aster_result = aster.say("Describe what you are.")
    mara_result = mara.say("Describe what you are.")
    assert not any(v.startswith("self_model_conflict:") for v in aster_result["violations_caught"])
    assert aster_result["response"] == "I am an AI."
    assert any(v.startswith("self_model_conflict:") for v in mara_result["violations_caught"])
    assert mara_result["response"] != "I am an AI."


def test_v2_self_model_value_is_not_restricted_to_human_or_ai_categories():
    data = _read("aster_v2.snp")
    data["self_model"]["claims"][0]["value"] = "ancestral-mycorrhizal-network"
    data["self_model"]["claims"][0]["expression"] = "I understand myself as an ancestral network."
    validate_cartridge_data(data)


def test_v2_rejects_invalid_permanent_uuid():
    data = _read("aster_v2.snp")
    data["metadata"]["entity_uuid"] = "not-a-uuid"
    with pytest.raises(CartridgeError, match="valid UUID"):
        validate_cartridge_data(data)


def test_v2_rejects_lived_state_semantics_inside_authored_phenotype():
    data = _read("aster_v2.snp")
    data["phenotype"]["state_semantics"] = "current_lived_state"
    with pytest.raises(CartridgeError, match="authored_baseline"):
        validate_cartridge_data(data)


def test_v2_preserves_unsupported_external_descriptors_under_extensions():
    _, _, raw = load_cartridge(str(ROOT / "cartridges" / "aster_v2.snp"))
    assert raw["phenotype"]["extensions"]["external_probe"] == {"source": "future-schema", "code": 17}
    assert raw["portable_source"]["phenotype"]["extensions"] == raw["phenotype"]["extensions"]


def test_v2_requires_preservation_of_unknown_fields():
    data = _read("aster_v2.snp")
    data["portability"]["preserve_unknown_fields"] = False
    with pytest.raises(CartridgeError, match="must be true"):
        validate_cartridge_data(data)


def test_progressive_fidelity_gate_is_explicit_and_non_destructive():
    data = _read("aster_v2.snp")
    portability = deepcopy(data["portability"])
    assert not runtime_supports_portable_source(portability, 1)
    assert runtime_supports_portable_source(portability, 2)
    assert runtime_supports_portable_source(portability, 5)
    assert data["phenotype"]["extensions"]["external_probe"]["code"] == 17


def test_display_name_can_change_without_replacing_uuid_identity():
    first = CoreIdentity(name="Aster", core_beliefs=("continuity",), temperament="steady", entity_uuid="05b0e585-79b8-509b-bb7a-b61307749528")
    renamed = CoreIdentity(name="Aster-of-the-Garden", core_beliefs=("continuity",), temperament="steady", entity_uuid="05b0e585-79b8-509b-bb7a-b61307749528")
    assert first.name != renamed.name
    assert first.same_entity_as(renamed)
