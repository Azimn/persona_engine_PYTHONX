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
        [sys.executable, str(ROOT / "simulator.py"), "--script", str(SCRIPT), "--cartridge", str(CART)],
        cwd=str(ROOT.parent), text=True, capture_output=True, check=False,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr


def test_restart_preserves_identity_and_full_subject_time_without_unbounded_legacy_dynamics():
    with tempfile.TemporaryDirectory() as d:
        db = os.path.join(d, "state.db")
        agent = CharacterAgent(cartridge_path=str(CART), user_id="silence", db_path=db)
        agent.say("Hello.", server_truth={"user_presence": "present"}, visible_context={"user_presence": "present"})
        identity_before = agent.engine.identity
        subject_before = agent.engine.clock.subject_elapsed_seconds
        agent.engine.last_wall_time -= 8 * 60 * 60
        agent.engine._persist()

        restarted = CharacterAgent(cartridge_path=str(CART), user_id="silence", db_path=db)
        result = restarted.say("...")

        assert restarted.engine.identity == identity_before
        assert restarted.engine.clock.subject_elapsed_seconds - subject_before >= 8 * 60 * 60 - 1.0
        # Compatibility dynamics remain bounded while the clock preserves the
        # entire eight-hour interval. Timestep is processing work, not time.
        assert result["body"]["fatigue"] >= 0.75
        bundle = restarted.engine.persistence.export_continuity_tail(restarted.engine.identity.name, restarted.engine.user_id)
        time_events = [event for event in bundle["events"] if event["event_type"] == "time_advance"]
        assert any(event["payload"]["elapsed_seconds"] >= 8 * 60 * 60 - 1.0 for event in time_events)
