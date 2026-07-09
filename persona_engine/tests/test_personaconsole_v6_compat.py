"""Compatibility tests for converted PersonaConsole_v6 character cartridges."""

from pathlib import Path
import tempfile

from persona_engine.agent import CharacterAgent
from persona_engine.core.cartridge import load_cartridge

ROOT = Path(__file__).resolve().parents[1]
COMPAT = [
    "friendly.snp",
    "kiki.snp",
    "mentor.snp",
    "pretorius_v6.snp",
    "quiet.snp",
    "rival.snp",
]


def test_converted_personaconsole_v6_cartridges_load():
    for filename in COMPAT:
        core, ledger, raw = load_cartridge(str(ROOT / "cartridges" / filename))
        assert core.name
        assert core.core_beliefs
        assert raw["body_profile"]
        assert raw["world_profile"]
        assert raw["sensory_profile"]
        assert raw["voice_profile"]
        assert raw["avatar_profile"]


def test_converted_personaconsole_v6_cartridges_run_one_turn():
    for filename in COMPAT:
        with tempfile.TemporaryDirectory() as td:
            agent = CharacterAgent(
                cartridge_path=str(ROOT / "cartridges" / filename),
                user_id="compat_user",
                db_path=str(Path(td) / "state.db"),
            )
            result = agent.say(
                "Hello. Are you still yourself?",
                server_truth={"user_presence": "present"},
                visible_context={"user_presence": "present"},
            )
            assert isinstance(result["response"], str)
            assert result["response"].strip()
            assert result["violations_caught"] == []


def test_converted_personaconsole_v6_public_projection_and_voice_avatar():
    with tempfile.TemporaryDirectory() as td:
        agent = CharacterAgent(
            cartridge_path=str(ROOT / "cartridges" / "kiki.snp"),
            user_id="compat_user",
            db_path=str(Path(td) / "state.db"),
        )
        agent.say("Hey, Kiki.")
        status = agent.public_status()
        voice = agent.plan_voice("Hello.")
        avatar = agent.avatar_projection()
        assert "energy" in status
        assert voice["rate_bucket"] in {"slow", "normal", "fluid", "fast"}
        assert avatar["face_state"]
