from pathlib import Path

path = Path(__file__).resolve().parents[1] / "persona_engine" / "core" / "engine.py"
text = path.read_text(encoding="utf-8")
old = '        if record_event and (elapsed > 0.0 or advance.backward_correction_seconds > 0.0):\n            self.persistence.log_event(self.identity.name, self.user_id, self.timestep, "time_advance", payload)\n'
new = '        # Ordinary sub-step wall gaps update the clock but do not create a\n        # standalone canonical stopwatch event. They have no current dynamics\n        # effect and the next canonical experience still carries wall time.\n        # Explicit advances can request their own event even below this quantum.\n        should_record_time = (elapsed >= LEGACY_IDLE_STEP_SECONDS or advance.backward_correction_seconds > 0.0 or advance.source != "wall_clock_catchup")\n        if record_event and should_record_time:\n            self.persistence.log_event(self.identity.name, self.user_id, self.timestep, "time_advance", payload)\n'
if old not in text:
    raise RuntimeError("M4 time-event granularity anchor not found")
path.write_text(text.replace(old, new, 1), encoding="utf-8")
print("Applied M4 time-event granularity refinement")
