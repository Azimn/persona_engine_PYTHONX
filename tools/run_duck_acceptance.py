#!/usr/bin/env python3
"""Production-boundary acceptance probe for the DUCK future runtime.

This probe exercises the real local composition root with the deterministic
offline renderer. It is intentionally broader than the cognitive mock probe:
one persistent subject must survive conversation, checkpointing, backup/restore,
process restart, bounded hot state, and historical expression recovery.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import tempfile

from persona_engine.duck.backup import DuckBackupManager
from persona_engine.duck.host import FutureDuckHost


CARTRIDGE = Path(__file__).resolve().parents[1] / "persona_engine" / "cartridges" / "neutral.snp"


def _assert_bounds(host: FutureDuckHost) -> dict[str, int]:
    state = host.runtime.organism.current_state()
    action_count = len(state.action_ledger)
    prediction_count = len(state.prediction_ledger)
    working_count = len(state.working_memory)
    expression_count = len(host.runtime.expression_journal.rows)
    expression_limit = int(host.runtime.expression_journal.max_rows)

    if action_count > 128:
        raise RuntimeError(f"action ledger exceeded hot bound: {action_count}")
    if prediction_count > 128:
        raise RuntimeError(f"prediction ledger exceeded hot bound: {prediction_count}")
    if working_count > host.runtime.organism.config.working_memory_limit:
        raise RuntimeError(f"working memory exceeded configured bound: {working_count}")
    if expression_count > expression_limit:
        raise RuntimeError(
            f"expression hot cache exceeded configured bound: {expression_count}>{expression_limit}"
        )
    return {
        "actions": action_count,
        "predictions": prediction_count,
        "working_memory": working_count,
        "expressions": expression_count,
        "expression_limit": expression_limit,
    }


def run_acceptance(cycles: int, *, expression_cache_limit: int = 256) -> dict:
    cycles = max(12, int(cycles))
    expression_cache_limit = max(2, int(expression_cache_limit))

    with tempfile.TemporaryDirectory(prefix="duck-production-acceptance-") as temp_name:
        base = Path(temp_name)
        active_root = base / "subject"
        host = FutureDuckHost.open(
            active_root,
            cartridge_path=CARTRIDGE,
            user_id="duck-production-acceptance",
        )
        subject_id = host.subject.subject_id
        initial_tick = host.runtime.tick
        host.runtime.expression_journal.max_rows = expression_cache_limit

        first_speech_id: str | None = None
        first_expression_text: str | None = None
        responses = 0
        backup_restores = 0
        process_restarts = 0
        max_observed = {
            "actions": 0,
            "predictions": 0,
            "working_memory": 0,
            "expressions": 0,
        }

        backup_at = max(1, cycles // 3)
        restart_at = max(backup_at + 1, (cycles * 2) // 3)

        for index in range(cycles):
            result = host.send(f"production acceptance message {index}")
            if result.get("subject_id") != subject_id:
                raise RuntimeError("subject identity changed during conversation")
            if result.get("selected_action") != "communicate":
                raise RuntimeError(
                    f"expected communicate action at cycle {index}, got {result.get('selected_action')!r}"
                )
            if not str(result.get("response") or "").strip():
                raise RuntimeError(f"no delivered response at cycle {index}")
            responses += 1

            trace = host.runtime.organism.traces[-1]
            execution = (trace.outcome or {}).get("execution", {})
            metadata = execution.get("metadata", {}) if isinstance(execution, dict) else {}
            if first_speech_id is None:
                first_speech_id = str(metadata.get("speech_id") or "")
                expression = metadata.get("expression", {})
                first_expression_text = str(expression.get("text") or "") if isinstance(expression, dict) else ""
                if not first_speech_id or not first_expression_text:
                    raise RuntimeError("first delivered expression was not durably identified")

            bounds = _assert_bounds(host)
            for key in max_observed:
                max_observed[key] = max(max_observed[key], int(bounds[key]))

            if index == backup_at:
                host.save()
                archive = base / "midlife-backup.zip"
                backup_info = DuckBackupManager.create(active_root, archive)
                if backup_info.get("subject_id") != subject_id:
                    raise RuntimeError("backup manifest changed subject identity")
                restored_root = base / "restored-subject"
                DuckBackupManager.restore(
                    archive,
                    restored_root,
                    expected_subject_id=subject_id,
                )
                active_root = restored_root
                host = FutureDuckHost.open(active_root)
                if host.subject.subject_id != subject_id:
                    raise RuntimeError("restored host opened as a different subject")
                backup_restores += 1

            if index == restart_at:
                before_restart_tick = host.runtime.tick
                host.save()
                host = FutureDuckHost.open(active_root)
                if host.subject.subject_id != subject_id:
                    raise RuntimeError("process restart opened as a different subject")
                if host.runtime.tick != before_restart_tick:
                    raise RuntimeError(
                        f"process restart changed cognitive tick {before_restart_tick}->{host.runtime.tick}"
                    )
                process_restarts += 1

        if first_speech_id is None or first_expression_text is None:
            raise RuntimeError("acceptance run produced no expression evidence")

        final_bounds = _assert_bounds(host)
        final_status = host.runtime.status()
        final_save = host.save()

        archived = host.duck_persistence.find_expression(first_speech_id)
        if not archived:
            raise RuntimeError("first realized expression was not recoverable from durable trace")
        if str(archived.get("text") or "") != first_expression_text:
            raise RuntimeError("historical expression text changed in durable trace")

        eviction_expected = cycles > expression_cache_limit
        first_still_hot = first_speech_id in host.runtime.expression_journal.rows
        if eviction_expected and first_still_hot:
            raise RuntimeError("old expression remained in hot cache after eviction threshold")

        if host.runtime.tick < initial_tick + cycles:
            raise RuntimeError("cognitive clock did not advance across the acceptance history")
        if backup_restores != 1 or process_restarts != 1:
            raise RuntimeError("acceptance lifecycle did not exercise both restore and restart")
        if not final_status.get("expression_archive_available"):
            raise RuntimeError("production runtime lost expression archive lookup after restart")

        return {
            "result": "PASS",
            "subject_id": subject_id,
            "cycles_requested": cycles,
            "responses_delivered": responses,
            "initial_tick": initial_tick,
            "final_tick": host.runtime.tick,
            "backup_restores": backup_restores,
            "process_restarts": process_restarts,
            "expression_cache_limit": expression_cache_limit,
            "expression_cache_size": len(host.runtime.expression_journal.rows),
            "expression_eviction_expected": eviction_expected,
            "first_expression_still_hot": first_still_hot,
            "first_expression_archive_recovered": True,
            "max_hot_state": max_observed,
            "final_hot_state": final_bounds,
            "canonical_digest": final_save["duck_state_sha256"],
        }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Run the production-boundary DUCK future-build acceptance probe"
    )
    parser.add_argument("--cycles", type=int, default=360)
    parser.add_argument("--expression-cache-limit", type=int, default=256)
    parser.add_argument("--output", default="")
    args = parser.parse_args(argv)

    result = run_acceptance(
        args.cycles,
        expression_cache_limit=args.expression_cache_limit,
    )
    text = json.dumps(result, indent=2, sort_keys=True)
    if args.output:
        path = Path(args.output)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text + "\n", encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
