"""Packaging/import contract tests for editable installs."""

from __future__ import annotations

from pathlib import Path
import tempfile


def test_package_imports_cleanly():
    import persona_engine

    assert persona_engine.__version__


def test_core_modules_import_cleanly():
    from persona_engine.agent import CharacterAgent
    from persona_engine.core.engine import InteriorEngine
    from persona_engine.core.public_state import public_status_from_engine
    from persona_engine.core.world_authority import WorldAuthority

    assert CharacterAgent
    assert InteriorEngine
    assert public_status_from_engine
    assert WorldAuthority


def test_ui_app_factory_imports_cleanly():
    from persona_engine.ui import create_app

    assert callable(create_app)


def test_simulator_module_imports_cleanly():
    from persona_engine import simulator

    assert callable(simulator.main)


def test_cartridges_directory_is_discoverable():
    import persona_engine

    root = Path(persona_engine.__file__).resolve().parent
    cartridges = root / "cartridges"
    assert cartridges.is_dir()
    assert (cartridges / "pretorius.snp").exists()
    assert list(cartridges.glob("*.snp"))


def test_static_ui_assets_are_discoverable():
    import persona_engine

    root = Path(persona_engine.__file__).resolve().parent
    static = root / "ui_static"
    assert (static / "index.html").exists()
    assert (static / "styles.css").exists()
    assert (static / "app.js").exists()


def test_dependency_free_mock_renderer_path_still_works():
    from persona_engine.agent import CharacterAgent

    import persona_engine

    root = Path(persona_engine.__file__).resolve().parent
    cartridge = root / "cartridges" / "neutral.snp"
    with tempfile.TemporaryDirectory() as tmpdir:
        agent = CharacterAgent(
            cartridge_path=str(cartridge),
            db_path=str(Path(tmpdir) / "state.db"),
            user_id="package_contract",
        )
        result = agent.say("Hello.")
    assert result["response"]
    lowered = result["response"].lower()
    assert "ollama" not in lowered
    assert "mock renderer" not in lowered
    assert any(term in lowered for term in ["i hear you", "listening", "hello", "thread", "here"])
