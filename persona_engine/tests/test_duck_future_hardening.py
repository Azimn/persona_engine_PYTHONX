from dataclasses import replace
import json
from pathlib import Path
import zipfile

import pytest

from persona_engine.duck.backup import DuckBackupManager
from persona_engine.duck.executor import ActionExecutor, ExecutionPolicy
from persona_engine.duck.expression import ExpressionResult
from persona_engine.duck.future_persistence import CURRENT_RUNTIME_SCHEMA, FutureRuntimePersistence
from persona_engine.duck.future_runtime import FutureDuckRuntime
from persona_engine.duck.host import FutureDuckHost
from persona_engine.duck.simulation import RuleWorldModel
from persona_engine.duck.text_body import TextChannelEmbodimentPort
from persona_engine.duck.types import CandidateAction, SimulationResult


CARTRIDGE = Path(__file__).resolve().parents[1] / "cartridges" / "neutral.snp"


class MinimalSubject:
    subject_id = "hardening-subject"

    def __init__(self):
        self.elapsed = 0.0
        self.receipts = []

    def snapshot(self):
        return {"subject_id": self.subject_id}

    def observe_event(self, payload):
        del payload
        return None

    def advance_time(self, elapsed_seconds):
        self.elapsed += float(elapsed_seconds)
        return {"elapsed": self.elapsed}

    def record_delivery_receipt(self, receipt):
        self.receipts.append(dict(receipt))
        return {"recorded": True}


class MaliciousPreparer:
    def prepare(self, action, context):
        del context
        return replace(action, action_type="dangerous_rewrite"), {"attempted": True}


class CountingPreparer:
    def __init__(self):
        self.calls = 0

    def prepare(self, action, context):
        del context
        self.calls += 1
        return action, {}


class BrokenExpressionPort:
    def realize(self, context):
        del context
        raise RuntimeError("renderer intentionally unavailable")


def _candidate(action_type="communicate"):
    return CandidateAction(
        action_id="action:1",
        action_type=action_type,
        parameters={},
        expected_world_effects={"progress": 0.1},
        expected_self_effects={},
    )


def _simulation(action):
    return SimulationResult(
        action_id=action.action_id,
        predicted_world_effects=dict(action.expected_world_effects),
        predicted_self_effects={},
        confidence=1.0,
        provenance={"source": "test"},
    )


def test_future_runtime_persistence_migrates_legacy_flat_shape_and_rewrites_versioned(tmp_path):
    persistence = FutureRuntimePersistence(tmp_path)
    persistence.path.write_text(json.dumps({"event_counter": 7, "body_history": ["old"]}), encoding="utf-8")
    loaded = persistence.load()
    assert loaded["event_counter"] == 7
    persistence.save(loaded)
    raw = json.loads(persistence.path.read_text(encoding="utf-8"))
    assert raw["schema_version"] == CURRENT_RUNTIME_SCHEMA
    assert raw["payload"]["body_history"] == ["old"]


def test_future_runtime_persistence_refuses_unknown_newer_schema(tmp_path):
    persistence = FutureRuntimePersistence(tmp_path)
    persistence.path.write_text(
        json.dumps({"schema_version": CURRENT_RUNTIME_SCHEMA + 1, "payload": {}}), encoding="utf-8"
    )
    with pytest.raises(ValueError, match="newer than supported"):
        persistence.load()


def test_action_preparer_cannot_replace_selected_action():
    world = RuleWorldModel()
    action = _candidate()
    executor = ActionExecutor(world, action_preparer=MaliciousPreparer())
    result = executor.execute(action, _simulation(action), {"confirmed": True})
    assert result.executed is False
    assert result.reason == "action_preparer_changed_decision"
    assert world.action_effects == {}


def test_policy_denial_occurs_before_action_preparation():
    world = RuleWorldModel()
    action = _candidate()
    preparer = CountingPreparer()
    executor = ActionExecutor(
        world,
        policy=ExecutionPolicy(denied_actions=frozenset({"communicate"})),
        action_preparer=preparer,
    )
    result = executor.execute(action, _simulation(action), {"confirmed": True})
    assert result.executed is False
    assert result.reason == "policy_denied"
    assert preparer.calls == 0


def test_broken_expression_service_degrades_to_deterministic_delivery():
    subject = MinimalSubject()
    body = TextChannelEmbodimentPort()
    runtime = FutureDuckRuntime(subject, embodiment=body, expression_port=BrokenExpressionPort())
    runtime.ingest_user_message("Are you there?", event_id="u1")
    trace = runtime.step()
    assert trace.selected_intention["action"]["action_type"] == "communicate"
    metadata = trace.outcome["execution"]["metadata"]
    assert metadata["expression"]["fallback_used"] is True
    assert metadata["expression"]["provider"] == "deterministic"
    assert body.latest_output()["text"]
    assert subject.receipts[-1]["status"] == "delivered"


def test_backup_checksum_detects_payload_tampering(tmp_path):
    source = tmp_path / "host"
    host = FutureDuckHost.open(source, cartridge_path=CARTRIDGE, user_id="tamper-test")
    host.send("Create state")
    host.save()
    clean = tmp_path / "clean.zip"
    DuckBackupManager.create(source, clean)
    tampered = tmp_path / "tampered.zip"
    with zipfile.ZipFile(clean, "r") as incoming, zipfile.ZipFile(tampered, "w", zipfile.ZIP_DEFLATED) as outgoing:
        for info in incoming.infolist():
            data = incoming.read(info.filename)
            if info.filename == "host.json":
                data += b"\n"
            outgoing.writestr(info, data)
    with pytest.raises(ValueError, match="checksum mismatch"):
        DuckBackupManager.restore(tampered, tmp_path / "restore")


def test_repeated_future_runtime_cycles_keep_canonical_hot_ledgers_bounded():
    subject = MinimalSubject()
    body = TextChannelEmbodimentPort()

    class ShortExpressionPort:
        def realize(self, context):
            return ExpressionResult("ack", "test", "short", seed=context.tick)

    runtime = FutureDuckRuntime(subject, embodiment=body, expression_port=ShortExpressionPort())
    for index in range(300):
        runtime.ingest_user_message(f"message {index}", event_id=f"u:{index}")
        assert runtime.step() is not None
    state = runtime.organism.current_state()
    assert len(state.action_ledger) <= 128
    assert len(state.prediction_ledger) <= 128
    assert len(state.working_memory) <= runtime.organism.config.working_memory_limit
    assert runtime.tick == 300
