#!/usr/bin/env python3
"""Test a minimum-sufficient root-only canonical continuity projection.

This changes no runtime policy. A normal Wayfarer session is recorded first.
The probe then constructs an experimental continuity bundle containing only
causal roots, with input payloads reduced to user text plus the exogenous host
context actually supplied to the public API. Derived state-transition and
routine sensorium records are omitted and the stream is renumbered.

Acceptance requires deterministic semantic replay, cold-biography recovery,
commitment replay, elapsed-time replay, and bounded sensor-observation replay.
"""

from __future__ import annotations

import argparse
import json
import os
import tempfile
from collections import Counter, defaultdict
from copy import deepcopy
from pathlib import Path

from persona_engine.agent import CharacterAgent
from persona_engine.core.audio_sensor import AudioObservation
from persona_engine.core.cold_biography import retrieve_cold_biography
from persona_engine.core.persistence import Persistence
from persona_engine.core.replay import replay_from_continuity_bundle, semantic_digest

ROOT = Path(__file__).resolve().parents[1]
CART = ROOT / "persona_engine" / "cartridges" / "pretorius.snp"

DERIVED = {"state_transition", "sensorium", "dream_consolidation"}


def _json_bytes(value) -> int:
    return len(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8"))


def _event_bytes(events: list[dict]) -> int:
    return sum(_json_bytes(event) for event in events)


def _payload_bytes_by_type(events: list[dict]) -> dict[str, int]:
    values: dict[str, int] = defaultdict(int)
    for event in events:
        values[str(event.get("event_type", ""))] += _json_bytes(event.get("payload") or {})
    return dict(sorted(values.items(), key=lambda item: (-item[1], item[0])))


def _project_root_only(bundle: dict, submitted_context: dict[str, tuple[dict, dict]]) -> dict:
    projected = deepcopy(bundle)
    kept: list[dict] = []
    for event in bundle.get("events", []):
        event_type = str(event.get("event_type", ""))
        if event_type in DERIVED:
            continue
        clone = deepcopy(event)
        if event_type in {"input", "user_statement"}:
            payload = event.get("payload") or {}
            user_text = str(payload.get("user_text") or payload.get("text") or "")
            host_truth, host_visible = submitted_context.get(user_text, ({}, {}))
            root_payload = {"user_text": user_text}
            if host_truth:
                root_payload["server_truth"] = deepcopy(host_truth)
            if host_visible:
                root_payload["visible_context"] = deepcopy(host_visible)
            clone["payload"] = root_payload
            clone["payload_schema"] = "input-root-v2-experiment"
        # Stream sequence represents stored canonical order, so removing derived
        # verification records requires a new contiguous sequence. Event UUIDs
        # are preserved because the underlying root experiences are unchanged.
        clone["sequence"] = len(kept) + 1
        kept.append(clone)
    projected["events"] = kept
    projected["after_sequence"] = 0
    checkpoint = projected.get("checkpoint")
    if isinstance(checkpoint, dict):
        # The existing checkpoint belongs to the source sequence namespace. This
        # projection is not an import replacement yet, so do not mislabel it.
        projected["checkpoint"] = None
    return projected


def run() -> dict:
    with tempfile.TemporaryDirectory() as directory:
        source_db = os.path.join(directory, "source.db")
        source = CharacterAgent(cartridge_path=str(CART), user_id="root_projection", db_path=source_db)

        submitted: dict[str, tuple[dict, dict]] = {}

        def say(text: str, server_truth=None, visible_context=None):
            host_truth = dict(server_truth or {})
            host_visible = dict(visible_context or {})
            submitted[text] = (host_truth, host_visible)
            return source.say(text, server_truth=host_truth, visible_context=host_visible)

        say("Please remember this neutral detail: the observatory key is violet.")
        say("The workshop door is saffron today.")
        say(
            "I am standing in the north gallery while the bell is ringing.",
            server_truth={"zone": "north_gallery", "bell_state": "ringing"},
            visible_context={"notice_board": "restoration scheduled"},
        )
        say("You lied to me. This is your fault.")
        say("You lied to me again. This is your fault too.")
        source.adopt_commitment("non_disclosure", "project orchid")
        source.observe_audio(AudioObservation(
            sound_level="high",
            sudden_onset=True,
            speech_activity=False,
            speaker_present=False,
            confidence=0.9,
            created_at=1234.0,
        ))
        source.advance_time(15.0, source="root_projection_probe", record_event=True)
        say("What about the workshop door now?")

        source_digest = semantic_digest(source)
        original = source.engine.persistence.export_continuity_tail(source.engine.identity.name, source.engine.user_id)
        projected = _project_root_only(original, submitted)
        replay = replay_from_continuity_bundle(str(CART), projected, user_id="root_projection")

        # Import the experimental projection into a fresh store to prove cold
        # biography depends only on the retained input root, not derived records.
        cold_db = os.path.join(directory, "cold.db")
        cold_store = Persistence(cold_db)
        cold_store.bind_subject(original["character_id"], original["user_id"], original["subject_uuid"])
        imported = cold_store.import_continuity_tail(original["character_id"], original["user_id"], projected)
        cold = retrieve_cold_biography(
            cold_store,
            original["character_id"],
            original["user_id"],
            "Do you remember the observatory key violet?",
            top_k=4,
        )
        cold_hit = any("violet" in memory.content.lower() for memory in cold)

        original_types = Counter(str(event.get("event_type", "")) for event in original["events"])
        projected_types = Counter(str(event.get("event_type", "")) for event in projected["events"])
        original_event_bytes = _event_bytes(original["events"])
        projected_event_bytes = _event_bytes(projected["events"])
        original_payload_bytes = sum(_json_bytes(event.get("payload") or {}) for event in original["events"])
        projected_payload_bytes = sum(_json_bytes(event.get("payload") or {}) for event in projected["events"])

        context_root = next(
            event for event in projected["events"]
            if event.get("event_type") == "input"
            and "north gallery" in str((event.get("payload") or {}).get("user_text", "")).lower()
        )
        context_payload = context_root["payload"]
        context_preserved = (
            context_payload.get("server_truth") == {"zone": "north_gallery", "bell_state": "ringing"}
            and context_payload.get("visible_context") == {"notice_board": "restoration scheduled"}
        )

        passed = all([
            replay.complete,
            replay.semantic_digest == source_digest,
            cold_hit,
            imported == len(projected["events"]),
            context_preserved,
            projected_types.get("state_transition", 0) == 0,
            projected_types.get("sensorium", 0) == 0,
            projected_types.get("input", 0) == original_types.get("input", 0),
            projected_types.get("commitment_adopted", 0) == 1,
            projected_types.get("sensor_observation", 0) == 1,
            projected_types.get("time_advance", 0) >= 1,
        ])

        return {
            "probe": "canonical-root-projection-v1",
            "production_policy_changed": False,
            "passed": passed,
            "source_semantic_digest": source_digest,
            "projected_replay_semantic_digest": replay.semantic_digest,
            "semantic_replay_equal": replay.semantic_digest == source_digest,
            "cold_biography_hit": cold_hit,
            "submitted_host_context_preserved": context_preserved,
            "original": {
                "events": len(original["events"]),
                "event_type_counts": dict(sorted(original_types.items())),
                "event_bytes": original_event_bytes,
                "payload_bytes": original_payload_bytes,
                "payload_bytes_by_type": _payload_bytes_by_type(original["events"]),
            },
            "root_only_projection": {
                "events": len(projected["events"]),
                "event_type_counts": dict(sorted(projected_types.items())),
                "event_bytes": projected_event_bytes,
                "payload_bytes": projected_payload_bytes,
                "payload_bytes_by_type": _payload_bytes_by_type(projected["events"]),
                "imported_events": imported,
            },
            "reduction": {
                "event_count": len(original["events"]) - len(projected["events"]),
                "event_bytes": original_event_bytes - projected_event_bytes,
                "event_percent": round((1 - projected_event_bytes / original_event_bytes) * 100.0, 2) if original_event_bytes else 0.0,
                "payload_bytes": original_payload_bytes - projected_payload_bytes,
                "payload_percent": round((1 - projected_payload_bytes / original_payload_bytes) * 100.0, 2) if original_payload_bytes else 0.0,
            },
            "interpretation": (
                "This is an experimental projection, not a new ledger schema. Passing means current replay, cold biography, "
                "host-context replay, commitment continuity, subject time, and bounded sensory roots do not require routine "
                "derived state_transition/sensorium rows or derived metadata embedded in input roots for this mixed scenario."
            ),
        }


def markdown(result: dict) -> str:
    original = result["original"]
    projected = result["root_only_projection"]
    reduction = result["reduction"]
    return "\n".join([
        "# Canonical Root Projection Probe",
        "",
        f"Passed: `{result['passed']}`.  ",
        f"Production policy changed: `{result['production_policy_changed']}`.  ",
        f"Semantic replay equal: `{result['semantic_replay_equal']}`.  ",
        f"Cold biography retained: `{result['cold_biography_hit']}`.  ",
        f"Submitted host context preserved: `{result['submitted_host_context_preserved']}`.",
        "",
        "| Representation | Events | Event bytes | Payload bytes |",
        "| --- | ---: | ---: | ---: |",
        f"| Current canonical | {original['events']} | {original['event_bytes']:,} | {original['payload_bytes']:,} |",
        f"| Root-only projection | {projected['events']} | {projected['event_bytes']:,} | {projected['payload_bytes']:,} |",
        "",
        f"Event-byte reduction: `{reduction['event_bytes']:,} B` (`{reduction['event_percent']}%`).  ",
        f"Payload-byte reduction: `{reduction['payload_bytes']:,} B` (`{reduction['payload_percent']}%`).",
        "",
        f"Current event types: `{original['event_type_counts']}`.  ",
        f"Projected event types: `{projected['event_type_counts']}`.",
        "",
        result["interpretation"],
    ]) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json")
    parser.add_argument("--markdown")
    args = parser.parse_args()
    result = run()
    rendered = json.dumps(result, indent=2, sort_keys=True)
    print(rendered)
    if args.json:
        path = Path(args.json)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(rendered + "\n", encoding="utf-8")
    if args.markdown:
        path = Path(args.markdown)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(markdown(result), encoding="utf-8")
    if not result["passed"]:
        raise SystemExit("canonical root projection contract failed")


if __name__ == "__main__":
    main()
