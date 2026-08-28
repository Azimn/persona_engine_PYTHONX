"""Offline CLI for Wayfarer <-> MatrAIx phenotype interoperability."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from persona_engine.core.matraix_interop import (
    audit_matraix_catalog_file,
    classify_matraix_dimension,
    export_matraix_dimensions,
    import_matraix_persona,
)


def _load(path: str) -> dict:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _write(path: str, payload: dict) -> None:
    Path(path).write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Project Wayfarer MatrAIx interoperability helper")
    sub = parser.add_subparsers(dest="command", required=True)

    importer = sub.add_parser("import", help="project MatrAIx dimensions into a Wayfarer phenotype JSON object")
    importer.add_argument("--input", required=True)
    importer.add_argument("--output", required=True)

    exporter = sub.add_parser("export", help="export preserved/reversible MatrAIx dimensions from a Wayfarer phenotype JSON object")
    exporter.add_argument("--input", required=True)
    exporter.add_argument("--output", required=True)

    auditor = sub.add_parser("audit", help="audit a local MatrAIx dimensions.json against Wayfarer's frozen crosswalk reference")
    auditor.add_argument("--catalog", required=True)
    auditor.add_argument("--output")

    classifier = sub.add_parser("classify", help="show Wayfarer's mapping semantics for one MatrAIx dimension ID")
    classifier.add_argument("dimension_id")
    classifier.add_argument("--output")

    args = parser.parse_args(argv)
    if args.command == "import":
        _write(args.output, import_matraix_persona(_load(args.input)))
        return 0
    if args.command == "export":
        _write(args.output, export_matraix_dimensions(_load(args.input)))
        return 0
    if args.command == "audit":
        report = audit_matraix_catalog_file(args.catalog)
        if args.output:
            _write(args.output, report)
        else:
            print(json.dumps(report, indent=2, sort_keys=True))
        return 0 if report["valid"] else 1

    result = classify_matraix_dimension(args.dimension_id)
    if args.output:
        _write(args.output, result)
    else:
        print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
