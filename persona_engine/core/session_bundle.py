"""Checksum-verified human-test export bundles and replay validation."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Any

from .replay import export_event_log, state_digest


BUNDLE_SCHEMA_VERSION = "1.1"
REPLAYABLE_EVENT_TYPES = {"input", "sensor_observation", "world_action_resolution"}
MAX_EVENTS = 10000
MAX_TRANSCRIPT_ITEMS = 10000
MAX_BUNDLE_BYTES = 10 * 1024 * 1024
MAX_REPORT_CHARS = 2_000_000
MAX_TRANSCRIPT_TEXT_CHARS = 200_000


class SessionBundleError(ValueError):
    """Raised when an exported session bundle is invalid or unsafe to replay."""


@dataclass
class SessionBundle:
    schema_version: str
    cartridge: str
    cartridge_sha256: str
    source_user_id: str
    renderer_config: dict[str, Any]
    transcript: list[dict[str, Any]]
    report_markdown: str
    canonical_events: list[dict[str, Any]]
    turn_records: list[dict[str, Any]]
    final_digest: dict[str, Any]
    exported_at: str
    checksum: str = ""

    def unsigned_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload.pop("checksum", None)
        return payload

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["checksum"] = self.checksum or bundle_checksum(self)
        return payload


def _canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def bundle_checksum(bundle: SessionBundle) -> str:
    return hashlib.sha256(_canonical_json(bundle.unsigned_dict()).encode("utf-8")).hexdigest()


def cartridge_checksum(path: str | Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _canonical_event(event: dict[str, Any]) -> dict[str, Any] | None:
    event_type = str(event.get("event_type", ""))
    if event_type not in REPLAYABLE_EVENT_TYPES:
        return None
    return {
        "sequence": int(event.get("id", 0)),
        "timestep": int(event.get("timestep", 0)),
        "event_type": event_type,
        "payload": dict(event.get("payload") or {}),
    }


def _turn_record(event: dict[str, Any]) -> dict[str, Any] | None:
    if event.get("event_type") != "turn":
        return None
    payload = event.get("payload") or {}
    return {
        "timestep": int(event.get("timestep", 0)),
        "decision_payload": payload.get("decision_payload", {}),
        "cognitive_application_report": payload.get("cognitive_application_report", {}),
        "retrieved_memory_trace": payload.get("retrieved_memory_trace", []),
        "validator_findings": payload.get("violations", []),
        "turn_seeds": payload.get("turn_seeds", {}),
        "self_monitor": payload.get("self_monitor"),
        "selected_regulation_id": (payload.get("action_decision") or {}).get("selected_regulation_id"),
    }


def build_session_bundle(
    agent,
    cartridge_path: str | Path,
    renderer_config: dict[str, Any],
    transcript: list[dict[str, Any]] | None = None,
    report_markdown: str = "",
) -> SessionBundle:
    events = export_event_log(agent.engine.persistence, agent.engine.identity.name, agent.engine.user_id)
    canonical_events = [item for event in events if (item := _canonical_event(event)) is not None]
    turn_records = [item for event in events if (item := _turn_record(event)) is not None]
    bundle = SessionBundle(
        schema_version=BUNDLE_SCHEMA_VERSION,
        cartridge=Path(cartridge_path).name,
        cartridge_sha256=cartridge_checksum(cartridge_path),
        source_user_id=str(agent.engine.user_id),
        renderer_config=dict(renderer_config),
        transcript=[dict(item) for item in (transcript or [])],
        report_markdown=str(report_markdown),
        canonical_events=canonical_events,
        turn_records=turn_records,
        final_digest=state_digest(agent),
        exported_at=datetime.now(timezone.utc).isoformat(),
    )
    bundle.checksum = bundle_checksum(bundle)
    return bundle


def load_session_bundle(raw: dict[str, Any]) -> SessionBundle:
    if not isinstance(raw, dict):
        raise SessionBundleError("session bundle must be a JSON object")
    if len(_canonical_json(raw).encode("utf-8")) > MAX_BUNDLE_BYTES:
        raise SessionBundleError("session bundle exceeds the 10 MB limit")
    try:
        bundle = SessionBundle(**raw)
    except (TypeError, ValueError) as exc:
        raise SessionBundleError(f"invalid session bundle shape: {exc}") from exc
    if bundle.schema_version not in {"1.0", BUNDLE_SCHEMA_VERSION}:
        raise SessionBundleError(f"unsupported session bundle schema: {bundle.schema_version}")
    if Path(bundle.cartridge).name != bundle.cartridge or not bundle.cartridge.endswith(".snp"):
        raise SessionBundleError("session bundle cartridge name is invalid")
    if not isinstance(bundle.source_user_id, str) or not bundle.source_user_id:
        raise SessionBundleError("session bundle source_user_id is invalid")
    if not isinstance(bundle.renderer_config, dict) or not isinstance(bundle.final_digest, dict):
        raise SessionBundleError("session bundle metadata is invalid")
    if not isinstance(bundle.report_markdown, str) or len(bundle.report_markdown) > MAX_REPORT_CHARS:
        raise SessionBundleError("session bundle report is too large")
    if not isinstance(bundle.canonical_events, list) or not isinstance(bundle.turn_records, list):
        raise SessionBundleError("session bundle event records must be lists")
    if not isinstance(bundle.transcript, list):
        raise SessionBundleError("session bundle transcript must be a list")
    if len(bundle.canonical_events) > MAX_EVENTS:
        raise SessionBundleError("session bundle contains too many replay events")
    if len(bundle.transcript) > MAX_TRANSCRIPT_ITEMS:
        raise SessionBundleError("session bundle transcript is too large")
    if bundle.checksum != bundle_checksum(bundle):
        raise SessionBundleError("session bundle checksum mismatch")
    for event in bundle.canonical_events:
        if not isinstance(event, dict) or event.get("event_type") not in REPLAYABLE_EVENT_TYPES:
            raise SessionBundleError("session bundle contains a non-replayable event")
        if not isinstance(event.get("payload"), dict):
            raise SessionBundleError("replay event payload must be an object")
    for item in bundle.transcript:
        if not isinstance(item, dict) or item.get("role") not in {"User", "Character"}:
            raise SessionBundleError("session bundle transcript item is invalid")
        if not isinstance(item.get("text", ""), str) or len(item.get("text", "")) > MAX_TRANSCRIPT_TEXT_CHARS:
            raise SessionBundleError("session bundle transcript item is too large")
    return bundle


def validate_bundle_cartridge(bundle: SessionBundle, cartridge_path: str | Path) -> None:
    if Path(cartridge_path).name != bundle.cartridge:
        raise SessionBundleError("session bundle cartridge does not match the selected cartridge")
    if cartridge_checksum(cartridge_path) != bundle.cartridge_sha256:
        raise SessionBundleError("session bundle cartridge checksum mismatch")
