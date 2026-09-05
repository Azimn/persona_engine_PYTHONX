from pathlib import Path

from fastapi.testclient import TestClient
import pytest

from persona_engine.duck.api import create_app
from persona_engine.duck.backup import DuckBackupManager
from persona_engine.duck.host import FutureDuckHost


CARTRIDGE = Path(__file__).resolve().parents[1] / "cartridges" / "neutral.snp"


def test_production_host_message_restart_and_subject_continuity(tmp_path):
    root = tmp_path / "host"
    host = FutureDuckHost.open(root, cartridge_path=CARTRIDGE, user_id="host-test")
    subject_id = host.subject.subject_id
    result = host.send("Hello from the host test.", utc_epoch=1_800_000_000.0)
    assert result["subject_id"] == subject_id
    assert result["selected_action"] == "communicate"
    assert isinstance(result["response"], str) and result["response"]
    first_tick = host.runtime.tick
    host.save()

    restarted = FutureDuckHost.open(root)
    assert restarted.subject.subject_id == subject_id
    assert restarted.runtime.tick == first_tick
    second = restarted.send("Do you remember this is the same runtime?", utc_epoch=1_800_000_086.4)
    assert second["subject_id"] == subject_id
    assert restarted.runtime.tick == first_tick + 1


def test_local_api_routes_through_future_host_and_hides_debug_by_default(tmp_path):
    host = FutureDuckHost.open(tmp_path / "api-host", cartridge_path=CARTRIDGE, user_id="api-test")
    client = TestClient(create_app(host))
    health = client.get("/health")
    assert health.status_code == 200
    assert health.json()["subject_id"] == host.subject.subject_id

    reply = client.post("/v1/messages", json={"text": "Hello API"})
    assert reply.status_code == 200
    assert reply.json()["selected_action"] == "communicate"
    assert reply.json()["response"]

    status = client.get("/v1/status")
    assert status.status_code == 200
    assert status.json()["subject_id"] == host.subject.subject_id
    assert client.get("/v1/trace/latest").status_code == 403
    assert client.get("/v1/debug/status").status_code == 403


def test_backup_restore_is_checksum_verified_and_reopens_same_subject(tmp_path):
    source = tmp_path / "source"
    host = FutureDuckHost.open(source, cartridge_path=CARTRIDGE, user_id="backup-test")
    subject_id = host.subject.subject_id
    host.send("Write some state before backup.")
    host.save()
    archive = tmp_path / "duck-backup.zip"
    created = DuckBackupManager.create(source, archive)
    assert created["subject_id"] == subject_id

    destination = tmp_path / "restored"
    restored = DuckBackupManager.restore(archive, destination)
    assert restored["subject_id"] == subject_id
    reopened = FutureDuckHost.open(destination)
    assert reopened.subject.subject_id == subject_id
    assert reopened.runtime.tick == host.runtime.tick


def test_restore_rejects_nonempty_destination_without_explicit_overwrite(tmp_path):
    source = tmp_path / "source"
    host = FutureDuckHost.open(source, cartridge_path=CARTRIDGE, user_id="backup-test-2")
    host.save()
    archive = tmp_path / "duck-backup.zip"
    DuckBackupManager.create(source, archive)
    destination = tmp_path / "occupied"
    destination.mkdir()
    (destination / "keep.txt").write_text("do not destroy", encoding="utf-8")
    with pytest.raises(FileExistsError):
        DuckBackupManager.restore(archive, destination)
    assert (destination / "keep.txt").read_text(encoding="utf-8") == "do not destroy"
