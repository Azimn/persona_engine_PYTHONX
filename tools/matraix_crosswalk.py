"""Small offline CLI for Wayfarer <-> MatrAIx phenotype projection."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from persona_engine.core.matraix_interop import export_matraix_dimensions, import_matraix_persona


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

    args = parser.parse_args(argv)
    payload = _load(args.input)
    if args.command == "import":
        _write(args.output, import_matraix_persona(payload))
    else:
        _write(args.output, export_matraix_dimensions(payload))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
