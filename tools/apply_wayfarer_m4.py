from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CORE = ROOT / "persona_engine" / "core"
TESTS = ROOT / "persona_engine" / "tests"
DOCS = ROOT / "persona_engine" / "docs"


def replace_once(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    if old not in text:
        raise RuntimeError(f"Expected patch anchor not found in {path}: {old[:100]!r}")
    if text.count(old) != 1:
        raise RuntimeError(f"Patch anchor is not unique in {path}: {old[:100]!r}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


(CORE / "continuity_clock.py").write_text('''"""Linear subject-time authority for Project Wayfarer.

The clock answers one question only: how much elapsed time has the continuing
subject actually accumulated? It does not decide what that duration means
psychologically. Body, affect, relationship, memory, and scheduler systems may
consume elapsed time only through their own explicit contracts.

Wall-clock regressions never make subject time run backward. Timezone metadata is
portable context, not part of elapsed-time arithmetic.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class ClockAdvance:
    elapsed_seconds: float
    subject_elapsed_seconds: float
    prior_wall_time: float
    observed_wall_time: float
    backward_correction_seconds: float = 0.0
    source: str = "wall_clock"

    @property
    def duration_bucket(self) -> str:
        seconds = self.elapsed_seconds
        if seconds < 60.0:
            return "seconds"
        if seconds < 3600.0:
            return "minutes"
        if seconds < 86400.0:
            return "hours"
        return "days"

    def to_payload(self) -> dict:
        return {
            "elapsed_seconds": round(float(self.elapsed_seconds), 6),
            "subject_elapsed_seconds": round(float(self.subject_elapsed_seconds), 6),
            "prior_wall_time": float(self.prior_wall_time),
            "observed_wall_time": float(self.observed_wall_time),
            "backward_correction_seconds": round(float(self.backward_correction_seconds), 6),
            "duration_bucket": self.duration_bucket,
            "source": self.source,
        }


@dataclass
class ContinuityClock:
    """Monotonic elapsed subject time plus a fallible wall-clock anchor."""

    subject_elapsed_seconds: float = 0.0
    last_wall_time: float = 0.0
    timezone_name: str = "unknown"
    correction_count: int = 0

    @classmethod
    def from_dict(cls, data: dict | None) -> "ContinuityClock":
        data = dict(data or {})
        return cls(
            subject_elapsed_seconds=max(0.0, float(data.get("subject_elapsed_seconds", 0.0))),
            last_wall_time=float(data.get("last_wall_time", 0.0)),
            timezone_name=str(data.get("timezone_name", "unknown") or "unknown"),
            correction_count=max(0, int(data.get("correction_count", 0))),
        )

    def to_dict(self) -> dict:
        return asdict(self)

    def observe_wall(self, observed_wall_time: float, *, source: str = "wall_clock_catchup") -> ClockAdvance:
        observed = float(observed_wall_time)
        prior = float(self.last_wall_time or observed)
        raw_delta = observed - prior
        if raw_delta < 0.0:
            self.correction_count += 1
            self.last_wall_time = observed
            return ClockAdvance(
                elapsed_seconds=0.0,
                subject_elapsed_seconds=self.subject_elapsed_seconds,
                prior_wall_time=prior,
                observed_wall_time=observed,
                backward_correction_seconds=abs(raw_delta),
                source=source,
            )
        elapsed = max(0.0, raw_delta)
        self.subject_elapsed_seconds += elapsed
        self.last_wall_time = observed
        return ClockAdvance(
            elapsed_seconds=elapsed,
            subject_elapsed_seconds=self.subject_elapsed_seconds,
            prior_wall_time=prior,
            observed_wall_time=observed,
            source=source,
        )

    def advance_by(self, elapsed_seconds: float, *, observed_wall_time: float, source: str = "explicit") -> ClockAdvance:
        elapsed = max(0.0, float(elapsed_seconds))
        prior = float(self.last_wall_time or observed_wall_time)
        self.subject_elapsed_seconds += elapsed
        self.last_wall_time = float(observed_wall_time)
        return ClockAdvance(
            elapsed_seconds=elapsed,
            subject_elapsed_seconds=self.subject_elapsed_seconds,
            prior_wall_time=prior,
            observed_wall_time=float(observed_wall_time),
            source=source,
        )
''', encoding="utf-8")

continuity = CORE / "continuity.py"
replace_once(
    continuity,
    '    if event_type in {"input", "user_statement"}:\n        return ContinuityAuthority(explicit_actor or "user", "external_user", "reported_input")\n',
    '    if event_type in {"input", "user_statement"}:\n        return ContinuityAuthority(explicit_actor or "user", "external_user", "reported_input")\n    if event_type == "time_advance":\n        return ContinuityAuthority(explicit_actor or "continuity_clock", "internal_clock", "elapsed_time_authority", "private")\n',
)
replace_once(
    continuity,
    '    if event_type == "world_action_resolution":\n',
    '    if event_type == "time_advance":\n        elapsed = payload.get("elapsed_seconds")\n        subject_elapsed = payload.get("subject_elapsed_seconds")\n        return isinstance(elapsed, (int, float)) and elapsed >= 0.0 and isinstance(subject_elapsed, (int, float)) and subject_elapsed >= 0.0\n    if event_type == "world_action_resolution":\n',
)

organism = CORE / "organism_tick.py"
replace_once(
    organism,
    '    def idle(self, *, elapsed_seconds: float, now: float, world, body, sensorium, pressures, memory, intentions) -> OrganismTickResult:\n        world_events = world.idle_events(elapsed_seconds, self.world_profile, now)\n',
    '    def idle(self, *, elapsed_seconds: float, now: float, world, body, sensorium, pressures, memory, intentions, world_elapsed_seconds: float | None = None) -> OrganismTickResult:\n        # World duration and legacy body dynamics are deliberately separable.\n        # M4 preserves full elapsed subject time without pretending old per-tick\n        # body coefficients are validated real-time physiology.\n        world_elapsed = elapsed_seconds if world_elapsed_seconds is None else max(0.0, float(world_elapsed_seconds))\n        world_events = world.idle_events(world_elapsed, self.world_profile, now)\n',
)

agent = ROOT / "persona_engine" / "agent.py"
replace_once(
    agent,
    '    def idle(self):\n        self.engine.run_idle_cycle()\n',
    '    def idle(self):\n        self.engine.run_idle_cycle()\n\n    def advance_time(self, elapsed_seconds: float, *, source: str = "explicit", record_event: bool = True) -> dict:\n        """Advance canonical subject time without requiring a wall-clock wait."""\n        return self.engine.advance_time(elapsed_seconds, source=source, record_event=record_event)\n',
)

replay = CORE / "replay.py"
replace_once(
    replay,
    '    Current replay roots:\n    - ``input`` / ``user_statement`` through ``CharacterAgent.say``;\n    - bounded ``sensor_observation`` through audio/vision observation APIs.\n',
    '    Current replay roots:\n    - ``time_advance`` through the canonical subject-time API;\n    - ``input`` / ``user_statement`` through ``CharacterAgent.say``;\n    - bounded ``sensor_observation`` through audio/vision observation APIs.\n',
)
replace_once(
    replay,
    '        if event_type in {"input", "user_statement"}:\n',
    '        if event_type == "time_advance":\n            elapsed = payload.get("elapsed_seconds")\n            if not isinstance(elapsed, (int, float)) or elapsed < 0.0:\n                raise ReplayContractError("time_advance lacks non-negative elapsed_seconds")\n            agent.advance_time(float(elapsed), source="continuity_replay", record_event=False)\n            replayed += 1\n            continue\n        if event_type in {"input", "user_statement"}:\n',
)

engine = CORE / "engine.py"
replace_once(
    engine,
    'from .suppression import SuppressionTrace\n',
    'from .suppression import SuppressionTrace\nfrom .continuity_clock import ClockAdvance, ContinuityClock\n',
)
replace_once(
    engine,
    'def _suppression_trace(gate: str, action: str, reason: str, severity: str = "info") -> SuppressionTrace:\n    return SuppressionTrace(gate=gate, action=action, reason=reason, severity=severity)\n',
    'def _suppression_trace(gate: str, action: str, reason: str, severity: str = "info") -> SuppressionTrace:\n    return SuppressionTrace(gate=gate, action=action, reason=reason, severity=severity)\n\n\n# Compatibility budget for pre-M4 per-five-second dynamics. Full elapsed subject\n# time is never truncated. These 1,000 seconds only bound legacy body/pressure\n# integration until those rates are empirically calibrated against real duration.\nLEGACY_IDLE_STEP_SECONDS = 5.0\nLEGACY_CATCHUP_DYNAMICS_BUDGET_SECONDS = 1000.0\n',
)
replace_once(
    engine,
    '        self.timestep = 0\n        self.last_wall_time = time.time()\n        self.last_reflection_time = 0.0\n\n        self._load_state()\n',
    '        self.timestep = 0\n        self.clock = ContinuityClock(last_wall_time=time.time())\n        self.last_reflection_time = 0.0\n\n        self._load_state()\n',
)
replace_once(
    engine,
    '    def renderer_status(self) -> dict:\n        status = getattr(self.renderer, "runtime_status", None)\n        if callable(status):\n            return status()\n        return {"requested_provider": "custom", "actual_provider": "custom", "model_name": type(self.renderer).__name__}\n\n    # ---------------- persistence ----------------\n',
    '    def renderer_status(self) -> dict:\n        status = getattr(self.renderer, "runtime_status", None)\n        if callable(status):\n            return status()\n        return {"requested_provider": "custom", "actual_provider": "custom", "model_name": type(self.renderer).__name__}\n\n    @property\n    def last_wall_time(self) -> float:\n        """Compatibility alias for pre-M4 callers; ContinuityClock owns time."""\n        return self.clock.last_wall_time\n\n    @last_wall_time.setter\n    def last_wall_time(self, value: float) -> None:\n        self.clock.last_wall_time = float(value)\n\n    # ---------------- persistence ----------------\n',
)
replace_once(
    engine,
    '        self.timestep = meta.get("timestep", self.timestep)\n        self.last_wall_time = meta.get("last_wall_time", self.last_wall_time)\n        self.last_reflection_time = meta.get("last_reflection_time", self.last_reflection_time)\n',
    '        self.timestep = meta.get("timestep", self.timestep)\n        clock_state = self.persistence.load(cid, uid, "continuity_clock")\n        if clock_state:\n            self.clock = ContinuityClock.from_dict(clock_state)\n        else:\n            # v1 compatibility: preserve the old wall anchor, but do not invent\n            # historical elapsed subject time that was never recorded.\n            self.clock.last_wall_time = float(meta.get("last_wall_time", self.clock.last_wall_time))\n        self.last_reflection_time = meta.get("last_reflection_time", self.last_reflection_time)\n',
)
replace_once(
    engine,
    '            "world": self.world.to_dict(),\n            "sensorium": self.sensorium.to_dict(),\n',
    '            "world": self.world.to_dict(),\n            "continuity_clock": self.clock.to_dict(),\n            "sensorium": self.sensorium.to_dict(),\n',
)
old_idle = '''    # ---------------- idle and silent processing ----------------\n    def _catch_up_idle(self):\n        now = time.time()\n        elapsed = max(0.0, now - self.last_wall_time)\n        self.last_wall_time = now\n        steps = min(int(elapsed / 5.0), 200)\n        for _ in range(steps):\n            self._run_single_idle_cycle(elapsed_seconds=5.0)\n        self.timestep += steps\n\n    def run_idle_cycle(self):\n        self._run_single_idle_cycle(elapsed_seconds=5.0)\n        self.timestep += 1\n        self.last_wall_time = time.time()\n        self._persist()\n\n    def _run_single_idle_cycle(self, elapsed_seconds: float = 5.0):\n        now = time.time()\n        total_pressure = sum(p.magnitude for p in self.pressures.pressures.values())\n        self.energy = max(0.1, self.energy - total_pressure * 0.01)\n        self.restlessness = min(1.0, self.restlessness + 0.02)\n        self.pressures.decay_all()\n        self.organism_tick.idle(\n            elapsed_seconds=elapsed_seconds,\n            now=now,\n            world=self.world,\n            body=self.body,\n            sensorium=self.sensorium,\n            pressures=self.pressures,\n            memory=self.memory,\n            intentions=self.intentions,\n        )\n        self.intentions.decay_open_loops()\n        self.habits.decay_all()\n        self.symbols.lifecycle_tick(now)\n        self.memory.compress_old(now)\n        if (self.energy < 0.3 or self.relationship.unresolved_conflict > 0.6) and (now - self.last_reflection_time > 300):\n            self._trigger_reflection(now)\n'''
new_idle = '''    # ---------------- idle and silent processing ----------------\n    def _catch_up_idle(self):\n        advance = self.clock.observe_wall(time.time(), source="wall_clock_catchup")\n        self._apply_clock_advance(advance, record_event=True, persist=False)\n\n    def advance_time(self, elapsed_seconds: float, *, source: str = "explicit", record_event: bool = True, persist: bool = True) -> dict:\n        """Advance linear subject time and apply only explicitly bounded dynamics.\n\n        Full elapsed time is preserved in ContinuityClock and the canonical\n        ``time_advance`` root. Legacy five-second body/pressure mechanics receive\n        at most the compatibility budget until those coefficients are calibrated.\n        """\n        advance = self.clock.advance_by(elapsed_seconds, observed_wall_time=time.time(), source=source)\n        return self._apply_clock_advance(advance, record_event=record_event, persist=persist)\n\n    def _apply_clock_advance(self, advance: ClockAdvance, *, record_event: bool, persist: bool) -> dict:\n        elapsed = max(0.0, float(advance.elapsed_seconds))\n        dynamics_seconds = min(elapsed, LEGACY_CATCHUP_DYNAMICS_BUDGET_SECONDS)\n        steps = int(dynamics_seconds / LEGACY_IDLE_STEP_SECONDS)\n        for index in range(steps):\n            self._run_single_idle_cycle(\n                elapsed_seconds=LEGACY_IDLE_STEP_SECONDS,\n                world_elapsed_seconds=elapsed if index == 0 else 0.0,\n            )\n        self.timestep += steps\n        payload = advance.to_payload()\n        payload.update({\n            "dynamics_seconds": round(steps * LEGACY_IDLE_STEP_SECONDS, 6),\n            "dynamics_steps": steps,\n            "dynamics_profile": "legacy_bounded_v1",\n            "memory_types": ["time_advance"],\n        })\n        if record_event and (elapsed > 0.0 or advance.backward_correction_seconds > 0.0):\n            self.persistence.log_event(self.identity.name, self.user_id, self.timestep, "time_advance", payload)\n        if persist:\n            self._persist()\n        return payload\n\n    def run_idle_cycle(self):\n        return self.advance_time(LEGACY_IDLE_STEP_SECONDS, source="manual_idle", record_event=True, persist=True)\n\n    def _run_single_idle_cycle(self, elapsed_seconds: float = 5.0, *, world_elapsed_seconds: float | None = None):\n        now = time.time()\n        total_pressure = sum(p.magnitude for p in self.pressures.pressures.values())\n        self.energy = max(0.1, self.energy - total_pressure * 0.01)\n        self.restlessness = min(1.0, self.restlessness + 0.02)\n        self.pressures.decay_all()\n        self.organism_tick.idle(\n            elapsed_seconds=elapsed_seconds,\n            world_elapsed_seconds=world_elapsed_seconds,\n            now=now,\n            world=self.world,\n            body=self.body,\n            sensorium=self.sensorium,\n            pressures=self.pressures,\n            memory=self.memory,\n            intentions=self.intentions,\n        )\n        self.intentions.decay_open_loops()\n        self.habits.decay_all()\n        self.symbols.lifecycle_tick(now)\n        self.memory.compress_old(now)\n        if (self.energy < 0.3 or self.relationship.unresolved_conflict > 0.6) and (now - self.last_reflection_time > 300):\n            self._trigger_reflection(now)\n'''
replace_once(engine, old_idle, new_idle)
replace_once(
    engine,
    '            while not self._idle_stop.wait(interval_seconds):\n                self.run_idle_cycle()\n',
    '            while not self._idle_stop.wait(interval_seconds):\n                self.advance_time(interval_seconds, source="background_idle", record_event=True, persist=True)\n',
)

(TESTS / "test_continuity_clock.py").write_text('''"""M4 linear subject-time and replay contracts."""

from pathlib import Path
import os
import tempfile

from persona_engine.agent import CharacterAgent
from persona_engine.core.continuity_clock import ContinuityClock
from persona_engine.core.replay import replay_from_continuity_bundle, semantic_digest

ROOT = Path(__file__).resolve().parents[1]
CART = ROOT / "cartridges" / "pretorius.snp"


def test_clock_preserves_full_elapsed_time_and_never_runs_backward():
    clock = ContinuityClock(last_wall_time=1000.0)
    forward = clock.observe_wall(1000.0 + 8 * 60 * 60)
    assert forward.elapsed_seconds == 8 * 60 * 60
    assert clock.subject_elapsed_seconds == 8 * 60 * 60

    backward = clock.observe_wall(900.0)
    assert backward.elapsed_seconds == 0.0
    assert backward.backward_correction_seconds > 0.0
    assert clock.subject_elapsed_seconds == 8 * 60 * 60
    assert clock.correction_count == 1


def test_explicit_time_advance_persists_and_is_canonical():
    with tempfile.TemporaryDirectory() as d:
        db = os.path.join(d, "state.db")
        agent = CharacterAgent(cartridge_path=str(CART), user_id="clock", db_path=db)
        result = agent.advance_time(8 * 60 * 60, source="test")
        assert result["elapsed_seconds"] == 8 * 60 * 60
        assert result["subject_elapsed_seconds"] >= 8 * 60 * 60
        # Old body/pressure coefficients are not granted eight hours of fake\n        # scientific meaning. Their compatibility integration remains bounded.\n        assert result["dynamics_seconds"] == 1000.0

        restarted = CharacterAgent(cartridge_path=str(CART), user_id="clock", db_path=db)
        assert restarted.engine.clock.subject_elapsed_seconds >= 8 * 60 * 60
        bundle = restarted.engine.persistence.export_continuity_tail(restarted.engine.identity.name, restarted.engine.user_id)
        time_events = [event for event in bundle["events"] if event["event_type"] == "time_advance"]
        assert time_events
        assert time_events[-1]["payload"]["elapsed_seconds"] == 8 * 60 * 60


def test_time_advance_is_a_replayable_root():
    with tempfile.TemporaryDirectory() as d:
        source = CharacterAgent(cartridge_path=str(CART), user_id="time_replay", db_path=os.path.join(d, "source.db"))
        source.advance_time(3600.0, source="test")
        bundle = source.engine.persistence.export_continuity_tail(source.engine.identity.name, source.engine.user_id)
        result = replay_from_continuity_bundle(str(CART), bundle, user_id="time_replay")
        assert result.complete is True
        assert result.root_events_replayed == 1
        assert result.semantic_digest == semantic_digest(source)
''', encoding="utf-8")

(TESTS / "test_long_silence_contract.py").write_text('''"""Continuity-pressure tests for long wall-clock silence and restart."""

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
        # Compatibility dynamics remain bounded while the clock preserves the\n        # entire eight-hour interval. Timestep is processing work, not time.\n        assert result["body"]["fatigue"] >= 0.75
        bundle = restarted.engine.persistence.export_continuity_tail(restarted.engine.identity.name, restarted.engine.user_id)
        time_events = [event for event in bundle["events"] if event["event_type"] == "time_advance"]
        assert any(event["payload"]["elapsed_seconds"] >= 8 * 60 * 60 - 1.0 for event in time_events)
''', encoding="utf-8")

(DOCS / "CONTINUITY_CLOCK.md").write_text('''# Project Wayfarer ContinuityClock Contract

## Purpose

M4 gives the portable individual one monotonic elapsed timeline. The clock records
how much time has passed for the subject. It does not decide what that duration
means emotionally, socially, or autobiographically.

## Two quantities must not be confused

**Subject elapsed time** is authoritative continuity state. An eight-hour absence
advances the clock by eight hours even on weak hardware and even if the process
was shut down for the whole interval.

**Dynamics integration time** is the amount of an existing subsystem's old update
rule that Wayfarer is currently willing to execute. Pre-M4 body and pressure
coefficients were tuned as short simulation ticks, not validated as real-hour
physiology or affect. M4 therefore retains a clearly labeled 1,000-second
compatibility budget for those legacy dynamics while preserving the full elapsed
duration in the clock.

This is deliberate. Numerical coefficients do not gain scientific meaning merely
because a real clock was added.

## Authority

Wall-clock observation and explicit host time advancement may create canonical
`time_advance` root events. Language-model output cannot advance subject time.
A backwards system-clock jump records a correction and advances subject time by
zero. Subject time never runs backwards.

## Replay

`time_advance` is an exogenous canonical replay root. Replay applies the recorded
elapsed duration through the same public time-advance interface before replaying
later experiences. Derived body, pressure, memory, and other consequences are not
replayed as independent causes.

## Timestep is not time

The historical `engine.timestep` remains a deterministic processing/work index for
compatibility. It is no longer an elapsed-time measurement. M3 schema 1.0's
`subject_time` column still uses that legacy processing index; the authoritative
M4 elapsed timeline is `ContinuityClock.subject_elapsed_seconds` and the canonical
`time_advance` payload. A future ledger-schema migration may normalize those two
representations, but M4 does not rewrite historical evidence.

## What M4 deliberately does not add

The clock does not add loneliness, attachment decay, routines, sleep, calendar
psychology, relationship cooling, or off-screen narrative. Those mechanisms must
be justified separately by longitudinal behavior that Wayfarer cannot otherwise
produce or preserve.
''', encoding="utf-8")

print("Applied Wayfarer M4 continuity clock integration")
