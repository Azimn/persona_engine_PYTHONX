"""Continuity-pressure tests for long wall-clock silence and restart."""

from pathlib import Path
import os
import subprocess
import sys
import tempfile

from persona_engine.agent import CharacterAgent

ROOT = Path(__file__).resolve().parents[1]
CART = ROOT / "cartridges" / "pretorius.snp"
SCRIPT = ROOT / "simulator_scripts" / "long_silence_resume.yaml"


def test_long_silence_resume_script_runs():
    completed = subprocess.run(
        [
            sys.executable,
            str(ROOT / "simulator.py"),
            "--script",
            str(SCRIPT),
            "--cartridge",
            str(CART),
        ],
        cwd=str(ROOT.parent),
        text=True,
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr


def test_restart_preserves_identity_and_applies_bounded_idle_catchup():
    with tempfile.TemporaryDirectory() as d:
        db = os.path.join(d, "state.db")
        agent = CharacterAgent(cartridge_path=str(CART), user_id="silence", db_path=db)
        agent.say("Hello.", server_truth={"user_presence": "present"}, visible_context={"user_presence": "present"})
        identity_before = agent.engine.identity
        agent.engine.last_wall_time -= 8 * 60 * 60
        agent.engine._persist()

        restarted = CharacterAgent(cartridge_path=str(CART), user_id="silence", db_path=db)
        before_timestep = restarted.engine.timestep
        result = restarted.say("...")

        assert restarted.engine.identity == identity_before
        # Current pre-M4 catch-up is deliberately bounded at 200 internal steps,
        # then the resumed user turn advances one more step.
        assert restarted.engine.timestep - before_timestep == 201
        assert result["body"]["fatigue"] >= 0.75
        assert result["body"]["energy"] <= 0.55
