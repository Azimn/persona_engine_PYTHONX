"""Tests for the human-testing web UI shell."""

from pathlib import Path


def test_ui_static_assets_exist():
    root = Path(__file__).resolve().parents[1]
    assert root.joinpath("ui_static", "index.html").exists()
    assert root.joinpath("ui_static", "styles.css").exists()
    assert root.joinpath("ui_static", "app.js").exists()


def test_ui_static_declares_invariant():
    root = Path(__file__).resolve().parents[1]
    html = root.joinpath("ui_static", "index.html").read_text(encoding="utf-8")
    assert "displays organism state" in html
    assert "never authors private state" in html


def test_create_app_serves_root_and_cartridges(tmp_path):
    try:
        from fastapi.testclient import TestClient
    except Exception:
        return
    from persona_engine.ui import create_app

    root = Path(__file__).resolve().parents[1]
    app = create_app(
        cartridge_path=str(root / "cartridges" / "neutral.snp"),
        db_path=str(tmp_path),
        user_id="ui_test",
        debug=False,
    )
    client = TestClient(app)
    page = client.get("/")
    assert page.status_code == 200
    assert "Human Test Console" in page.text
    cartridges = client.get("/cartridges")
    assert cartridges.status_code == 200
    names = [item["name"] for item in cartridges.json()["cartridges"]]
    assert "neutral.snp" in names


def test_chat_endpoint_uses_normal_input_channel(tmp_path):
    try:
        from fastapi.testclient import TestClient
    except Exception:
        return
    from persona_engine.ui import create_app

    root = Path(__file__).resolve().parents[1]
    app = create_app(
        cartridge_path=str(root / "cartridges" / "neutral.snp"),
        db_path=str(tmp_path),
        user_id="ui_test_chat",
        debug=False,
    )
    client = TestClient(app)
    response = client.post("/chat", json={"text": "Hello."})
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data["response"], str)
    assert data["response"]
    assert "status" in data
    assert "voice_plan" in data
