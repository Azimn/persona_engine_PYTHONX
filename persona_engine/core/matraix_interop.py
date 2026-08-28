"""Lossless MatrAIx <-> Wayfarer phenotype interoperability.

The crosswalk is deliberately conservative. Complete external dimension maps are
preserved under ``phenotype.extensions.matraix.dimensions``. Native projection
occurs only through a frozen, versioned crosswalk, so adding interoperability
never grants an external taxonomy authority over Wayfarer's internal semantics.
"""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

from .cartridge_v2 import PHENOTYPE_NAMESPACES, PHENOTYPE_SCHEMA_VERSION, validate_phenotype

DEFAULT_CROSSWALK_PATH = Path(__file__).resolve().parents[1] / "schema" / "matraix_crosswalk_v1.json"
RELATION_TYPES = {"exact", "approximate", "one_to_many", "many_to_one", "unsupported"}
DIRECTIONS = {"bidirectional", "import_only", "bidirectional_if_consistent", "bidirectional_bundle", "preserve_only"}


class MatraixInteropError(ValueError):
    """Raised when a crosswalk or interoperability payload is malformed."""


def _read_json(path: str | Path) -> dict[str, Any]:
    try:
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise MatraixInteropError(f"could not read MatrAIx crosswalk {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise MatraixInteropError("MatrAIx crosswalk root must be an object")
    return payload


def validate_crosswalk(data: dict[str, Any]) -> None:
    reference = data.get("reference")
    mappings = data.get("mappings")
    if str(data.get("crosswalk_version", "")) != "1.0":
        raise MatraixInteropError("unsupported MatrAIx crosswalk_version")
    if not isinstance(reference, dict):
        raise MatraixInteropError("crosswalk reference must be an object")
    for field in ("repository", "commit_sha", "schema_path", "schema_blob_sha", "schema_version", "target_dimensions"):
        if field not in reference:
            raise MatraixInteropError(f"crosswalk reference missing {field}")
    if not isinstance(mappings, list):
        raise MatraixInteropError("crosswalk mappings must be an array")

    seen: set[str] = set()
    represented_relations: set[str] = set()
    for index, mapping in enumerate(mappings):
        if not isinstance(mapping, dict):
            raise MatraixInteropError(f"mapping {index} must be an object")
        mapping_id = str(mapping.get("id", "")).strip()
        if not mapping_id or mapping_id in seen:
            raise MatraixInteropError(f"invalid or duplicate mapping id: {mapping_id!r}")
        seen.add(mapping_id)
        relation = str(mapping.get("relation", ""))
        direction = str(mapping.get("direction", ""))
        if relation not in RELATION_TYPES:
            raise MatraixInteropError(f"unsupported relation type for {mapping_id}: {relation}")
        if direction not in DIRECTIONS:
            raise MatraixInteropError(f"unsupported direction for {mapping_id}: {direction}")
        represented_relations.add(relation)
        source_ids = mapping.get("matraix_ids")
        target_paths = mapping.get("wayfarer_paths")
        if not isinstance(source_ids, list) or not source_ids or not all(isinstance(item, str) and item for item in source_ids):
            raise MatraixInteropError(f"mapping {mapping_id} needs non-empty matraix_ids")
        if not isinstance(target_paths, list) or not all(isinstance(item, str) and item for item in target_paths):
            raise MatraixInteropError(f"mapping {mapping_id} has malformed wayfarer_paths")
        if relation == "unsupported":
            if target_paths or direction != "preserve_only":
                raise MatraixInteropError(f"unsupported mapping {mapping_id} must be preserve_only with no target paths")
        elif not target_paths:
            raise MatraixInteropError(f"mapping {mapping_id} needs at least one Wayfarer target")
        for path in target_paths:
            root = path.split(".", 1)[0]
            if root not in PHENOTYPE_NAMESPACES or root == "extensions":
                raise MatraixInteropError(f"mapping {mapping_id} targets invalid native phenotype path: {path}")

        if relation in {"exact", "approximate"} and (len(source_ids) != 1 or len(target_paths) != 1):
            raise MatraixInteropError(f"{relation} mapping {mapping_id} must be one-to-one")
        if relation == "one_to_many" and (len(source_ids) != 1 or len(target_paths) < 2):
            raise MatraixInteropError(f"one_to_many mapping {mapping_id} has invalid cardinality")
        if relation == "many_to_one" and (len(source_ids) < 2 or len(target_paths) != 1):
            raise MatraixInteropError(f"many_to_one mapping {mapping_id} has invalid cardinality")

    declared = data.get("relation_types")
    if declared is not None and set(declared) != RELATION_TYPES:
        raise MatraixInteropError("relation_types declaration does not match supported relation types")
    if represented_relations != RELATION_TYPES:
        missing = sorted(RELATION_TYPES - represented_relations)
        raise MatraixInteropError(f"crosswalk does not demonstrate all relation types: {missing}")


def load_crosswalk(path: str | Path | None = None) -> dict[str, Any]:
    payload = _read_json(path or DEFAULT_CROSSWALK_PATH)
    validate_crosswalk(payload)
    return payload


def _get_path(data: dict[str, Any], dotted: str) -> Any:
    current: Any = data
    for part in dotted.split("."):
        if not isinstance(current, dict) or part not in current:
            return None
        current = current[part]
    return current


def _set_path(data: dict[str, Any], dotted: str, value: Any) -> None:
    parts = dotted.split(".")
    current = data
    for part in parts[:-1]:
        child = current.get(part)
        if child is None:
            child = {}
            current[part] = child
        if not isinstance(child, dict):
            raise MatraixInteropError(f"cannot project into non-object phenotype path: {dotted}")
        current = child
    current[parts[-1]] = copy.deepcopy(value)


def _empty_phenotype() -> dict[str, Any]:
    return {
        "schema_version": PHENOTYPE_SCHEMA_VERSION,
        "state_semantics": "authored_baseline",
        "extensions": {},
    }


def import_matraix_dimensions(
    dimensions: dict[str, Any],
    *,
    base_phenotype: dict[str, Any] | None = None,
    crosswalk: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Project a MatrAIx dimension dictionary without losing any source fields.

    Every source field is copied to the MatrAIx extension bag first. Explicit
    native mappings are then applied. Missing dimensions simply remain missing,
    matching MatrAIx's own no-imputation convention.
    """

    if not isinstance(dimensions, dict):
        raise MatraixInteropError("MatrAIx dimensions must be an object")
    mapping_data = copy.deepcopy(crosswalk) if crosswalk is not None else load_crosswalk()
    validate_crosswalk(mapping_data)
    phenotype = copy.deepcopy(base_phenotype) if base_phenotype is not None else _empty_phenotype()
    validate_phenotype(phenotype)

    extensions = phenotype.setdefault("extensions", {})
    if not isinstance(extensions, dict):
        raise MatraixInteropError("phenotype.extensions must be an object")
    extensions["matraix"] = {
        "crosswalk_version": mapping_data["crosswalk_version"],
        "reference": copy.deepcopy(mapping_data["reference"]),
        "dimensions": copy.deepcopy(dimensions),
        "applied_mappings": [],
    }

    applied = extensions["matraix"]["applied_mappings"]
    for mapping in mapping_data["mappings"]:
        relation = mapping["relation"]
        direction = mapping["direction"]
        source_ids = mapping["matraix_ids"]
        targets = mapping["wayfarer_paths"]
        if direction == "preserve_only" or relation == "unsupported":
            continue
        present = {source_id: dimensions[source_id] for source_id in source_ids if source_id in dimensions}
        if not present:
            continue
        if relation in {"exact", "approximate"}:
            _set_path(phenotype, targets[0], present[source_ids[0]])
        elif relation == "one_to_many":
            if source_ids[0] not in present:
                continue
            for target in targets:
                _set_path(phenotype, target, present[source_ids[0]])
        elif relation == "many_to_one":
            if len(present) != len(source_ids):
                continue
            _set_path(phenotype, targets[0], present)
        applied.append(mapping["id"])

    validate_phenotype(phenotype)
    return phenotype


def export_matraix_dimensions(
    phenotype: dict[str, Any],
    *,
    crosswalk: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Export MatrAIx dimensions conservatively from a Wayfarer phenotype.

    Preserved source dimensions are the base. Only mappings with explicitly
    reversible semantics may overwrite them. Approximate import-only mappings
    never synthesize or overwrite an external value.
    """

    validate_phenotype(phenotype)
    mapping_data = copy.deepcopy(crosswalk) if crosswalk is not None else load_crosswalk()
    validate_crosswalk(mapping_data)
    preserved = _get_path(phenotype, "extensions.matraix.dimensions")
    dimensions: dict[str, Any] = copy.deepcopy(preserved) if isinstance(preserved, dict) else {}

    for mapping in mapping_data["mappings"]:
        relation = mapping["relation"]
        direction = mapping["direction"]
        source_ids = mapping["matraix_ids"]
        targets = mapping["wayfarer_paths"]
        if direction in {"import_only", "preserve_only"} or relation in {"approximate", "unsupported"}:
            continue
        if relation == "exact" and direction == "bidirectional":
            value = _get_path(phenotype, targets[0])
            if value is not None:
                dimensions[source_ids[0]] = copy.deepcopy(value)
        elif relation == "one_to_many" and direction == "bidirectional_if_consistent":
            values = [_get_path(phenotype, target) for target in targets]
            present = [value for value in values if value is not None]
            if present and len(present) == len(values) and all(value == present[0] for value in present):
                dimensions[source_ids[0]] = copy.deepcopy(present[0])
        elif relation == "many_to_one" and direction == "bidirectional_bundle":
            bundle = _get_path(phenotype, targets[0])
            if isinstance(bundle, dict):
                for source_id in source_ids:
                    if source_id in bundle:
                        dimensions[source_id] = copy.deepcopy(bundle[source_id])
    return dimensions


def import_matraix_persona(payload: dict[str, Any], **kwargs: Any) -> dict[str, Any]:
    """Accept either a raw dimension map or a MatrAIx-style persona object."""

    if not isinstance(payload, dict):
        raise MatraixInteropError("MatrAIx persona payload must be an object")
    dimensions = payload.get("dimensions") if isinstance(payload.get("dimensions"), dict) else payload
    return import_matraix_dimensions(dimensions, **kwargs)
