"""Portable human-test bundle and replay contracts."""

from pathlib import Path

import pytest

from persona_engine.agent import CharacterAgent
from persona_engine.core.renderer_control import RendererConfig
from persona_engine.core.session_bundle import (
    SessionBundleError,
    build_session_bundle,
    load_session_bundle,
    validate_bundle_cartridge,
)


ROOT = Path(__file__).resolve().parents[1]
NEUTRAL = ROOT / "cartridges" / "neutral.snp"
FRIENDLY = ROOT / "cartridges" / "friendly.snp"


def _bundle(tmp_path):
    agent = CharacterAgent(cartridge_path=str(NEUTRAL), user_id="bundle_user", db_path=str(tmp_path / "source.db"))
    agent.observe_audio({"sound_level": "high", "sudden_onset": True, "confidence": 0.8, "created_at": 100.0})
    agent.say("Lantern is the word for this replay.")
    agent.say("What word did I give you?")
    return build_session_bundle(
        agent,
        NEUTRAL,
        RendererConfig().to_dict(),
        transcript=[{"role": "User", "text": "Lantern is the word for this replay.", "time": "test"}],
        report_markdown="# Reviewed report",
    )


def test_bundle_round_trip_preserves_human_and_trace_data(tmp_path):
    bundle = _bundle(tmp_path)
    loaded = load_session_bundle(bundle.to_dict())
    assert loaded.transcript[0]["role"] == "User"
    assert loaded.report_markdown == "# Reviewed report"
    assert loaded.turn_records
    assert loaded.turn_records[-1]["turn_seeds"]["expression"]
    assert loaded.turn_records[-1]["turn_seeds"]["private_cognition"]
    assert {event["event_type"] for event in loaded.canonical_events} == {"input", "sensor_observation"}
    assert all(event["event_type"] != "speech" for event in loaded.canonical_events)


def test_bundle_checksum_rejects_tampering(tmp_path):
    payload = _bundle(tmp_path).to_dict()
    payload["canonical_events"][0]["payload"]["sensor_type"] = "tampered"
    with pytest.raises(SessionBundleError, match="checksum mismatch"):
        load_session_bundle(payload)


def test_bundle_rejects_different_cartridge_even_when_bundle_is_valid(tmp_path):
    bundle = load_session_bundle(_bundle(tmp_path).to_dict())
    with pytest.raises(SessionBundleError, match="does not match"):
        validate_bundle_cartridge(bundle, FRIENDLY)


def test_ui_export_and_replay_use_isolated_database(tmp_path):
    TestClient = pytest.importorskip("fastapi.testclient").TestClient
    from persona_engine.ui import create_app

    app = create_app(
        cartridge_path=str(NEUTRAL),
        cartridges_dir=str(ROOT / "cartridges"),
        db_path=str(tmp_path),
        user_id="bundle_ui",
        debug=True,
    )
    client = TestClient(app)
    client.post("/api/sensor/audio", json={"sound_level": "high", "sudden_onset": True, "confidence": 0.9, "created_at": 200.0})
    client.post("/api/chat", json={"text": "Lantern is the word for this replay."})
    client.post("/api/chat", json={"text": "What word did I give you?"})
    source_path = Path(client.get("/health").json()["session"]["db_path"])

    exported = client.post("/api/session/export", json={
        "transcript": [{"role": "User", "text": "Lantern is the word for this replay.", "time": "test"}],
        "report_markdown": "# Session report",
    })
    assert exported.status_code == 200
    payload = exported.json()
    assert payload["checksum"]
    assert all(event["event_type"] != "speech" for event in payload["canonical_events"])

    first = client.post("/api/session/replay", json=payload)
    assert first.status_code == 200
    first_data = first.json()
    replay_path = Path(first_data["session"]["db_path"])
    assert first_data["session"]["mode"] == "replay"
    assert first_data["events_replayed"] == 3
    assert first_data["turns_replayed"] == 2
    assert first_data["digest_matches"] is True
    assert first_data["transcript"] == payload["transcript"]
    assert source_path.exists()
    assert replay_path.exists()
    assert replay_path != source_path

    second = client.post("/api/session/replay", json=payload)
    assert second.status_code == 200
    assert second.json()["final_digest"] == first_data["final_digest"]


def test_ui_replay_rejects_tampered_bundle(tmp_path):
    TestClient = pytest.importorskip("fastapi.testclient").TestClient
    from persona_engine.ui import create_app

    app = create_app(cartridge_path=str(NEUTRAL), cartridges_dir=str(ROOT / "cartridges"), db_path=str(tmp_path))
    client = TestClient(app)
    client.post("/api/chat", json={"text": "Hello."})
    payload = client.post("/api/session/export", json={"transcript": [], "report_markdown": ""}).json()
    payload["transcript"].append({"role": "Character", "text": "forged"})
    response = client.post("/api/session/replay", json=payload)
    assert response.status_code == 400
    assert "checksum mismatch" in response.json()["detail"]
