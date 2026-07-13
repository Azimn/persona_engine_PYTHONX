"""Contract tests for the human-testing UI adapter."""

from __future__ import annotations

from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
CARTRIDGES = ROOT / "cartridges"
PRIVATE_TERMS = {
    "pressures",
    "pressure",
    "relationship",
    "trust",
    "shame",
    "fear",
    "attachment",
    "belief_ledger",
    "private",
    "memories",
    "memory_count",
    "server_truth",
    "hidden",
}


def _client(tmp_path, *, debug=False, cartridge="neutral.snp"):
    TestClient = pytest.importorskip("fastapi.testclient").TestClient
    from persona_engine.ui import create_app

    app = create_app(
        cartridge_path=str(CARTRIDGES / cartridge),
        cartridges_dir=str(CARTRIDGES),
        db_path=str(tmp_path),
        user_id="human_ui_contract",
        debug=debug,
    )
    return TestClient(app)


def _walk_strings(value):
    if isinstance(value, dict):
        for key, item in value.items():
            yield str(key)
            yield from _walk_strings(item)
    elif isinstance(value, list):
        for item in value:
            yield from _walk_strings(item)
    else:
        yield str(value)


def test_api_status_exposes_only_public_status(tmp_path):
    client = _client(tmp_path)
    client.post("/api/chat", json={"text": "Hello.", "server_truth": {"hidden_note": "do not reveal"}})

    response = client.get("/api/status")
    assert response.status_code == 200
    data = response.json()
    assert set(data) == {"session", "status", "avatar_state"}
    assert data["session"]["cartridge"] == "neutral.snp"
    assert all(isinstance(value, str) for value in data["status"].values())
    assert not any(isinstance(value, (int, float)) for value in data["status"].values())

    lowered = " ".join(_walk_strings(data)).lower()
    for term in PRIVATE_TERMS:
        assert term not in lowered


def test_mock_sensor_endpoints_do_not_directly_mutate_private_state(tmp_path):
    client = _client(tmp_path, debug=True)
    before = client.get("/api/debug").json()["private_snapshot"]

    audio = client.post("/api/sensor/audio", json={"sound_level": "high", "sudden_onset": True, "confidence": 0.9})
    vision = client.post("/api/sensor/vision", json={"face_present": True, "user_presence": "present", "confidence": 0.9})
    after = client.get("/api/debug").json()["private_snapshot"]

    assert audio.status_code == 200
    assert vision.status_code == 200
    assert audio.json()["pressure_unchanged"] is True
    assert vision.json()["relationship_unchanged"] is True
    assert before["pressures"] == after["pressures"]
    assert before["relationship"] == after["relationship"]


def test_cartridge_switching_and_reset_do_not_touch_cartridge_files(tmp_path):
    client = _client(tmp_path, debug=True)
    neutral = CARTRIDGES / "neutral.snp"
    friendly = CARTRIDGES / "friendly.snp"
    before_times = {path.name: path.stat().st_mtime_ns for path in (neutral, friendly)}

    cartridges = client.get("/api/cartridges")
    assert cartridges.status_code == 200
    assert "friendly.snp" in [item["name"] for item in cartridges.json()["cartridges"]]

    selected = client.post("/api/session/select", json={"cartridge": "friendly.snp"})
    assert selected.status_code == 200
    assert selected.json()["session"]["cartridge"] == "friendly.snp"

    client.post("/api/chat", json={"text": "Remember this test turn."})
    assert client.get("/api/debug").json()["event_ids"]
    reset = client.post("/api/session/reset")
    assert reset.status_code == 200
    assert reset.json()["session"]["cartridge"] == "friendly.snp"
    assert client.get("/api/debug").json()["event_ids"] == []

    after_times = {path.name: path.stat().st_mtime_ns for path in (neutral, friendly)}
    assert before_times == after_times


def test_chat_returns_non_empty_response_with_mock_safe_renderer(tmp_path):
    client = _client(tmp_path)
    response = client.post("/api/chat", json={"text": "Hello."})
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data["response"], str)
    assert data["response"].strip()
    assert data["voice_plan"]["text"] == data["response"]


def test_debug_mode_is_off_by_default_in_frontend_and_backend(tmp_path):
    client = _client(tmp_path, debug=False)
    debug_response = client.get("/api/debug")
    assert debug_response.status_code == 200
    assert debug_response.json()["enabled"] is False

    app_js = ROOT.joinpath("ui_static", "app.js").read_text(encoding="utf-8")
    html = ROOT.joinpath("ui_static", "index.html").read_text(encoding="utf-8")
    assert "debugEnabled: false" in app_js
    assert 'id="debugToggle" type="checkbox"' in html
    assert "checked" not in html


def test_no_frontend_request_can_write_private_state_fields():
    app_js = ROOT.joinpath("ui_static", "app.js").read_text(encoding="utf-8")
    forbidden_paths = [
        "/pressure",
        "/pressures",
        "/relationship",
        "/memory",
        "/belief",
        "/identity",
        "/body",
        "/world",
        "/state",
    ]
    for path in forbidden_paths:
        assert path not in app_js
    assert "fetch(`${API_BASE}${path}`" in app_js


def test_ui_static_files_are_served(tmp_path):
    client = _client(tmp_path)
    page = client.get("/")
    css = client.get("/assets/styles.css")
    script = client.get("/assets/app.js")
    assert page.status_code == 200
    assert css.status_code == 200
    assert script.status_code == 200
    assert "Human Test Console" in page.text
    assert "debugEnabled: false" in script.text


def test_session_reports_new_resumed_and_fresh_modes(tmp_path):
    client = _client(tmp_path)
    assert client.get("/health").json()["session"]["mode"] == "new"

    switched = client.post("/api/session/select", json={"cartridge": "friendly.snp"})
    assert switched.json()["session"]["mode"] == "new"

    resumed = client.post("/api/session/select", json={"cartridge": "neutral.snp"})
    assert resumed.json()["session"]["mode"] == "resumed"

    fresh = client.post("/api/session/reset")
    assert fresh.json()["session"]["mode"] == "fresh"


def test_debug_trace_exposes_retrieved_memory_provenance(tmp_path):
    client = _client(tmp_path, debug=True)
    client.post("/api/chat", json={"text": "Lantern is the word for this test."})
    client.post("/api/chat", json={"text": "What word did I give you?"})

    trace = client.get("/api/debug").json()["workspace_summary"]["retrieved_memory_trace"]
    assert trace
    assert {"memory_id", "source", "tags", "created_at", "content"}.issubset(trace[0])
    assert trace[0]["content"].lower().startswith(("i ", "i'", "my ", "we "))
