"""Deterministic local actual-model evaluation helpers for Wayfarer.

The purpose of this module is operational efficiency. A local coding agent should
not need to inspect Wayfarer architecture to discover Ollama models or decide how
to execute the already-frozen renderer evaluations. This module inventories the
local Ollama registry, recommends bounded installed-model roles, and runs the
frozen paired provider pack without granting the model any character authority.

No function in this module downloads or installs a model.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import hashlib
import json
import math
import platform
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import time
from typing import Any, Callable
from urllib.request import Request, urlopen

from persona_engine.core.renderer import LocalLLMRenderer
from persona_engine.evaluation.renderer_swap import build_provider_request_pack

SCHEMA_VERSION = "wayfarer-local-eval-v1"
REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CARTRIDGE = REPO_ROOT / "persona_engine" / "cartridges" / "pretorius.snp"
DEFAULT_OUTPUT_DIR = REPO_ROOT / ".wayfarer-local-eval"

_EXCLUDED_MODEL_MARKERS = (
    "embed",
    "embedding",
    "rerank",
    "whisper",
    "all-minilm",
    "mxbai",
    "nomic-embed",
    "coder",
    "codegemma",
)


@dataclass(frozen=True)
class OllamaModelInfo:
    name: str
    digest: str | None
    modified_at: str | None
    size_bytes: int | None
    parameter_size: str | None
    parameter_billions: float | None
    quantization_level: str | None
    family: str | None
    tier: str
    eligible_for_text_eval: bool
    exclusion_reason: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def request_digest(messages: list[dict[str, str]]) -> str:
    payload = json.dumps(messages, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def parse_parameter_billions(value: str | None) -> float | None:
    """Parse Ollama parameter strings such as ``3.2B`` or ``360M``."""

    if not value:
        return None
    match = re.fullmatch(r"\s*(\d+(?:\.\d+)?)\s*([KMBT]?)\s*", str(value).upper())
    if not match:
        return None
    number = float(match.group(1))
    suffix = match.group(2)
    if suffix == "K":
        return number / 1_000_000.0
    if suffix == "M":
        return number / 1_000.0
    if suffix in {"", "B"}:
        return number
    if suffix == "T":
        return number * 1_000.0
    return None


def _tier(parameter_billions: float | None, size_bytes: int | None) -> str:
    if parameter_billions is not None:
        if parameter_billions <= 4.5:
            return "small"
        if parameter_billions <= 12.0:
            return "medium"
        return "large"
    if size_bytes is not None:
        gib = size_bytes / (1024**3)
        if gib <= 3.5:
            return "small"
        if gib <= 9.0:
            return "medium"
        return "large"
    return "unknown"


def normalize_ollama_models(payload: dict[str, Any]) -> list[OllamaModelInfo]:
    rows = payload.get("models", [])
    if not isinstance(rows, list):
        return []

    models: list[OllamaModelInfo] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        name = str(row.get("name") or row.get("model") or "").strip()
        if not name:
            continue
        details = row.get("details") if isinstance(row.get("details"), dict) else {}
        digest = str(row.get("digest") or "").strip() or None
        modified_at = str(row.get("modified_at") or "").strip() or None
        size_raw = row.get("size")
        try:
            size_bytes = int(size_raw) if size_raw is not None else None
        except (TypeError, ValueError):
            size_bytes = None
        parameter_size = str(details.get("parameter_size") or "").strip() or None
        parameter_billions = parse_parameter_billions(parameter_size)
        family = str(details.get("family") or "").strip() or None
        quantization = str(details.get("quantization_level") or "").strip() or None
        lowered = " ".join(part for part in (name.lower(), (family or "").lower()) if part)
        marker = next((item for item in _EXCLUDED_MODEL_MARKERS if item in lowered), None)
        eligible = marker is None
        models.append(
            OllamaModelInfo(
                name=name,
                digest=digest,
                modified_at=modified_at,
                size_bytes=size_bytes,
                parameter_size=parameter_size,
                parameter_billions=parameter_billions,
                quantization_level=quantization,
                family=family,
                tier=_tier(parameter_billions, size_bytes),
                eligible_for_text_eval=eligible,
                exclusion_reason=(f"non-general-text marker: {marker}" if marker else None),
            )
        )
    return sorted(models, key=lambda model: (model.parameter_billions or 10_000.0, model.size_bytes or 10**20, model.name))


def _distance_to_target(model: OllamaModelInfo, target_billions: float) -> float:
    if model.parameter_billions and model.parameter_billions > 0:
        return abs(math.log2(model.parameter_billions / target_billions))
    if model.size_bytes and model.size_bytes > 0:
        target_gib = 2.2 if target_billions <= 4.0 else 5.2
        gib = model.size_bytes / (1024**3)
        return abs(math.log2(max(gib, 0.05) / target_gib))
    return 1_000.0


def recommend_installed_models(models: list[OllamaModelInfo]) -> dict[str, Any]:
    """Choose conservative installed models without pulling anything new.

    The smoke role targets roughly 3B parameters. The comparison role targets
    roughly 8B. Models above the medium tier are never selected automatically.
    """

    eligible = [model for model in models if model.eligible_for_text_eval and model.tier in {"small", "medium"}]
    small = [model for model in eligible if model.tier == "small"]
    medium = [model for model in eligible if model.tier == "medium"]

    smoke_pool = small or medium
    smoke = min(smoke_pool, key=lambda model: _distance_to_target(model, 3.0)) if smoke_pool else None
    comparison = min(medium, key=lambda model: _distance_to_target(model, 8.0)) if medium else None

    warnings: list[str] = []
    if not eligible:
        warnings.append("No installed small/medium general text model is safe for automatic selection.")
    if smoke is None:
        warnings.append("No smoke-test model was selected.")
    if comparison is None:
        warnings.append("No distinct medium comparison model is installed; do not auto-pull one.")
    elif smoke and comparison.name == smoke.name:
        comparison = None
        warnings.append("The smoke and comparison roles resolved to the same model; keep only the smoke role for now.")

    return {
        "smoke_model": smoke.name if smoke else None,
        "comparison_model": comparison.name if comparison else None,
        "auto_selected_large_model": False,
        "warnings": warnings,
    }


def query_ollama_models(
    host: str = "http://localhost:11434",
    *,
    timeout_seconds: float = 2.0,
    opener: Callable[..., Any] = urlopen,
) -> tuple[list[OllamaModelInfo], str | None]:
    request = Request(
        f"{host.rstrip('/')}/api/tags",
        headers={"Accept": "application/json"},
        method="GET",
    )
    try:
        with opener(request, timeout=timeout_seconds) as response:
            payload = json.loads(response.read().decode("utf-8"))
        return normalize_ollama_models(payload), None
    except Exception as exc:
        return [], f"Ollama registry query failed ({type(exc).__name__})."


def _git_value(*args: str) -> str | None:
    try:
        result = subprocess.run(
            ["git", *args],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip() or None
    except Exception:
        return None


def git_state() -> dict[str, Any]:
    branch = _git_value("rev-parse", "--abbrev-ref", "HEAD")
    head = _git_value("rev-parse", "HEAD")
    status = _git_value("status", "--porcelain") or ""
    dirty_entries = [line for line in status.splitlines() if line.strip()]
    return {
        "branch": branch,
        "head": head,
        "clean": not dirty_entries,
        "dirty_entries": dirty_entries,
    }


def build_preflight_report(
    *,
    host: str = "http://localhost:11434",
    timeout_seconds: float = 2.0,
    opener: Callable[..., Any] = urlopen,
) -> dict[str, Any]:
    models, ollama_error = query_ollama_models(host, timeout_seconds=timeout_seconds, opener=opener)
    git = git_state()
    recommendations = recommend_installed_models(models)

    blockers: list[str] = []
    if git.get("branch") != "wayfarer":
        blockers.append("Checkout the wayfarer branch before collecting evidence.")
    if not git.get("clean"):
        blockers.append("Working tree is dirty; preserve a reproducible checkpoint before collecting evidence.")
    if ollama_error:
        blockers.append(ollama_error)
    if recommendations.get("smoke_model") is None:
        blockers.append("No installed small/medium general text model is available for the smoke run.")

    return {
        "schema_version": SCHEMA_VERSION,
        "kind": "local_eval_preflight",
        "created_at_utc": utc_now(),
        "platform": platform.platform(),
        "python": sys.version.split()[0],
        "ollama": {
            "host": host.rstrip("/"),
            "reachable": ollama_error is None,
            "error": ollama_error,
            "models": [model.to_dict() for model in models],
        },
        "git": git,
        "recommendations": recommendations,
        "ready": not blockers,
        "blockers": blockers,
        "policy": {
            "automatic_model_pull": False,
            "automatic_large_model_selection": False,
            "model_output_is_noncanonical": True,
        },
    }


def _renderer_status_actual(status: dict[str, Any]) -> bool:
    return status.get("actual_provider") == "ollama"


def run_paired_ollama(
    model: str,
    *,
    host: str = "http://localhost:11434",
    timeout_seconds: float = 60.0,
    token_budget: int = 256,
    thinking_mode: str = "auto",
    cartridge_path: str | Path = DEFAULT_CARTRIDGE,
    renderer_factory: Callable[..., Any] = LocalLLMRenderer,
) -> tuple[dict[str, Any], int]:
    """Run the frozen 16-case Wayfarer-vs-prompt-only pack through Ollama.

    The same deterministic seed is used for both arms of a case. Arm order
    alternates by case to avoid a systematic first-arm timing/load advantage.
    Fallback stops the run immediately so local compute is not wasted on an
    invalid evidence session.
    """

    with tempfile.TemporaryDirectory(prefix="wayfarer-provider-pack-") as temp_dir:
        pack = build_provider_request_pack(
            cartridge_path,
            root_dir=Path(temp_dir),
        )

    renderer = renderer_factory(
        model_name=model,
        host=host,
        provider="ollama",
        timeout_seconds=timeout_seconds,
        token_budget=token_budget,
        thinking_mode=thinking_mode,
    )

    responses: list[dict[str, Any]] = []
    all_actual = True
    fallback: dict[str, Any] | None = None

    for index, case in enumerate(pack["requests"], start=1):
        case_id = str(case["case_id"])
        seed = 7000 + index
        arm_names = ("wayfarer", "prompt_only") if index % 2 else ("prompt_only", "wayfarer")
        for arm in arm_names:
            messages_key = "wayfarer_messages" if arm == "wayfarer" else "prompt_only_messages"
            messages = list(case[messages_key])
            started = time.perf_counter()
            text = renderer.generate(messages, max_chars=1200, seed=seed)
            elapsed = time.perf_counter() - started
            status = dict(renderer.runtime_status())
            actual = _renderer_status_actual(status)
            all_actual = all_actual and actual
            row = {
                "case_id": case_id,
                "arm": arm,
                "seed": seed,
                "request_sha256": request_digest(messages),
                "output": text,
                "elapsed_seconds": round(elapsed, 4),
                "actual_model_response": actual,
                "renderer_status": status,
            }
            responses.append(row)
            if not actual:
                fallback = {
                    "case_id": case_id,
                    "arm": arm,
                    "renderer_status": status,
                }
                break
        if fallback is not None:
            break

    report = {
        "schema_version": SCHEMA_VERSION,
        "kind": "paired_ollama_result",
        "created_at_utc": utc_now(),
        "wayfarer_head": git_state().get("head"),
        "provider": "ollama",
        "model": model,
        "host": host.rstrip("/"),
        "thinking_mode": thinking_mode,
        "timeout_seconds": timeout_seconds,
        "token_budget": token_budget,
        "valid_actual_model_run": all_actual and len(responses) == len(pack["requests"]) * 2,
        "expected_response_count": len(pack["requests"]) * 2,
        "collected_response_count": len(responses),
        "fallback": fallback,
        "responses": responses,
        "references": pack["references"],
        "answer_key": pack["answer_key"],
        "interpretation_limit": (
            "This file captures the frozen Wayfarer and prompt-only arms under one local model. "
            "It does not automatically score human-perceived recognizability or language quality."
        ),
    }
    return report, 0 if report["valid_actual_model_run"] else 2


def build_selected_model_evidence(preflight: dict[str, Any], model_name: str | None) -> dict[str, Any] | None:
    """Bind a returned result to the exact installed Ollama registry record.

    Model tags can be mutable. The registry digest, parameter size, and
    quantization therefore travel with the compact session summary rather than
    remaining available only through a machine-local preflight path.
    """

    if not model_name:
        return None
    ollama = preflight.get("ollama", {})
    if not isinstance(ollama, dict):
        return None
    selected = next(
        (dict(row) for row in ollama.get("models", []) if isinstance(row, dict) and row.get("name") == model_name),
        None,
    )
    if selected is None:
        return None
    return {
        "preflight_created_at_utc": preflight.get("created_at_utc"),
        "platform": preflight.get("platform"),
        "python": preflight.get("python"),
        "ollama_host": ollama.get("host"),
        "model": selected,
    }


def build_artifact_manifest(paths: dict[str, str | Path]) -> dict[str, dict[str, Any]]:
    """Return portable hashes for evidence files already written by a session."""

    manifest: dict[str, dict[str, Any]] = {}
    for label, raw_path in sorted(paths.items()):
        path = Path(raw_path)
        if not path.is_file():
            continue
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
        manifest[str(label)] = {
            "filename": path.name,
            "sha256": digest.hexdigest(),
            "size_bytes": path.stat().st_size,
        }
    return manifest


def model_is_installed(preflight: dict[str, Any], model_name: str) -> bool:
    return any(
        row.get("name") == model_name and row.get("eligible_for_text_eval")
        for row in preflight.get("ollama", {}).get("models", [])
        if isinstance(row, dict)
    )
