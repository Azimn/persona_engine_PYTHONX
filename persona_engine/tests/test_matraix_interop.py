"""Wayfarer MatrAIx crosswalk and lossless interoperability tests."""

from copy import deepcopy

import pytest

from persona_engine.core.matraix_interop import (
    MatraixInteropError,
    RELATION_TYPES,
    UNMAPPED_DIMENSION_POLICY,
    audit_matraix_catalog,
    classify_matraix_dimension,
    export_matraix_dimensions,
    import_matraix_dimensions,
    import_matraix_persona,
    load_crosswalk,
    mapped_matraix_ids,
    validate_crosswalk,
)


def _sample_dimensions():
    return {
        "primary_language": "English",
        "risk_tolerance": "Moderate",
        "decision_style": "Analytical",
        "learning_style": "Hands-on",
        "media_diet": "Mixed",
        "economic_motivation": "Security",
        "values_priority": "Autonomy",
        "tone_expected": "Direct",
        "dominant_trait": "Curious",
        "age_bracket": "35-44",
        "region": "North America",
        "future_dimension_not_yet_understood": "preserve me",
    }


def _synthetic_frozen_catalog():
    mapped = sorted(mapped_matraix_ids())
    fillers = [f"synthetic_unmapped_{index:04d}" for index in range(1290 - len(mapped))]
    ids = mapped + fillers
    return {
        "schemaVersion": "1.0",
        "targetDimensions": 1290,
        "dimensions": [{"id": item} for item in ids],
    }


def test_crosswalk_freezes_exact_upstream_reference_and_unmapped_policy():
    crosswalk = load_crosswalk()
    reference = crosswalk["reference"]
    assert reference["repository"] == "MatrAIx-ai/MatrAIx-Persona-8B"
    assert reference["commit_sha"] == "39d850270917db25535dac3f7aa2561732050e82"
    assert reference["schema_blob_sha"] == "742a50ed79f106675311c09f016fff48951f841c"
    assert reference["schema_version"] == "1.0"
    assert reference["target_dimensions"] == 1290
    assert crosswalk["unmapped_dimension_policy"] == UNMAPPED_DIMENSION_POLICY
    assert {item["relation"] for item in crosswalk["mappings"]} == RELATION_TYPES


def test_unmapped_dimension_has_explicit_preserve_only_semantics():
    result = classify_matraix_dimension("future_dimension_not_yet_understood")
    assert result == {
        "dimension_id": "future_dimension_not_yet_understood",
        "relation": "unsupported",
        "direction": "preserve_only",
        "explicit": False,
        "policy": UNMAPPED_DIMENSION_POLICY,
        "mapping_ids": [],
    }
    explicit = classify_matraix_dimension("primary_language")
    assert explicit["explicit"] is True
    assert explicit["relation"] == "exact"
    assert "primary_language" in explicit["mapping_ids"]


def test_import_is_lossless_even_for_unsupported_and_future_dimensions():
    source = _sample_dimensions()
    phenotype = import_matraix_dimensions(source)
    interop = phenotype["extensions"]["matraix"]
    preserved = interop["dimensions"]
    assert preserved == source
    assert preserved is not source
    assert interop["unmapped_dimension_policy"] == UNMAPPED_DIMENSION_POLICY
    assert phenotype["communication"]["primary_language"] == "English"
    assert phenotype["personality"]["risk_tolerance"] == "Moderate"
    assert phenotype["behavioral_tendencies"]["decision_style"] == "Analytical"
    assert phenotype["communication"]["preferred_tone"] == "Direct"
    assert phenotype["personality"]["dominant_trait"] == "Curious"
    assert phenotype["behavioral_tendencies"]["dominant_trait_expression"] == "Curious"
    assert phenotype["behavioral_tendencies"]["decision_profile"] == {
        "risk_tolerance": "Moderate",
        "decision_style": "Analytical",
    }
    assert "age_bracket" not in phenotype.get("personality", {})


def test_export_preserves_unknowns_and_overlays_only_explicit_reversible_mappings():
    phenotype = import_matraix_dimensions(_sample_dimensions())
    phenotype["communication"]["primary_language"] = "Spanish"
    phenotype["communication"]["preferred_tone"] = "Warm"
    exported = export_matraix_dimensions(phenotype)
    assert exported["primary_language"] == "Spanish"
    assert exported["tone_expected"] == "Direct"  # approximate mapping is import-only
    assert exported["age_bracket"] == "35-44"
    assert exported["future_dimension_not_yet_understood"] == "preserve me"


def test_one_to_many_exports_only_when_native_views_are_consistent():
    phenotype = import_matraix_dimensions(_sample_dimensions())
    phenotype["personality"]["dominant_trait"] = "Deliberate"
    exported = export_matraix_dimensions(phenotype)
    assert exported["dominant_trait"] == "Curious"
    phenotype["behavioral_tendencies"]["dominant_trait_expression"] = "Deliberate"
    exported = export_matraix_dimensions(phenotype)
    assert exported["dominant_trait"] == "Deliberate"


def test_many_to_one_bundle_can_round_trip_explicit_component_changes():
    phenotype = import_matraix_dimensions(_sample_dimensions())
    phenotype["behavioral_tendencies"]["decision_profile"] = {
        "risk_tolerance": "High",
        "decision_style": "Intuitive",
    }
    exported = export_matraix_dimensions(phenotype)
    assert exported["risk_tolerance"] == "High"
    assert exported["decision_style"] == "Intuitive"


def test_import_accepts_matraix_style_persona_wrapper():
    phenotype = import_matraix_persona({"persona_id": "mx-1", "dimensions": _sample_dimensions()})
    assert phenotype["preferences"]["learning_style"] == "Hands-on"


def test_import_does_not_impute_missing_external_dimensions():
    phenotype = import_matraix_dimensions({"primary_language": "English"})
    preserved = phenotype["extensions"]["matraix"]["dimensions"]
    assert preserved == {"primary_language": "English"}
    assert "risk_tolerance" not in phenotype.get("personality", {})


def test_catalog_audit_verifies_frozen_count_version_and_explicit_mapping_ids():
    report = audit_matraix_catalog(_synthetic_frozen_catalog())
    assert report["valid"] is True
    assert report["catalog_actual_dimension_count"] == 1290
    assert report["expected_target_dimensions"] == 1290
    assert report["missing_mapped_ids"] == []
    assert report["explicitly_mapped_dimension_count"] == len(mapped_matraix_ids())
    assert report["implicit_preserve_only_dimension_count"] == 1290 - len(mapped_matraix_ids())
    assert report["unmapped_dimension_policy"] == UNMAPPED_DIMENSION_POLICY


def test_catalog_audit_fails_closed_on_missing_mapped_id_or_reference_mismatch():
    catalog = _synthetic_frozen_catalog()
    catalog["dimensions"] = [item for item in catalog["dimensions"] if item["id"] != "primary_language"]
    catalog["dimensions"].append({"id": "replacement_unmapped"})
    catalog["schemaVersion"] = "2.0"
    report = audit_matraix_catalog(catalog)
    assert report["valid"] is False
    assert "primary_language" in report["missing_mapped_ids"]
    assert report["schema_version_match"] is False


def test_catalog_audit_detects_duplicate_and_malformed_ids():
    catalog = _synthetic_frozen_catalog()
    catalog["dimensions"][0] = {"id": "primary_language"}
    catalog["dimensions"][1] = {"id": "primary_language"}
    catalog["dimensions"][2] = {"label": "missing id"}
    report = audit_matraix_catalog(catalog)
    assert report["valid"] is False
    assert "primary_language" in report["duplicate_ids"]
    assert 2 in report["malformed_indexes"]


def test_crosswalk_rejects_native_target_outside_stable_phenotype_namespaces():
    crosswalk = deepcopy(load_crosswalk())
    mapping = next(item for item in crosswalk["mappings"] if item["relation"] == "exact")
    mapping["wayfarer_paths"] = ["demographics.age"]
    with pytest.raises(MatraixInteropError, match="invalid native phenotype path"):
        validate_crosswalk(crosswalk)


def test_crosswalk_rejects_missing_relation_class_coverage():
    crosswalk = deepcopy(load_crosswalk())
    crosswalk["mappings"] = [item for item in crosswalk["mappings"] if item["relation"] != "unsupported"]
    with pytest.raises(MatraixInteropError, match="all relation types"):
        validate_crosswalk(crosswalk)


def test_crosswalk_rejects_ambiguous_unmapped_policy():
    crosswalk = deepcopy(load_crosswalk())
    crosswalk["unmapped_dimension_policy"] = "guess_from_labels"
    with pytest.raises(MatraixInteropError, match="unmapped_dimension_policy"):
        validate_crosswalk(crosswalk)
