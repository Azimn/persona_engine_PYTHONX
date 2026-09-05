#!/usr/bin/env python3
"""Deterministic integration probe for the DUCK future-build composition root."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import tempfile

from persona_engine.duck.embodiment_port import Affordance, BodySnapshot, EmbodimentOutcome
from persona_engine.duck.future_runtime import FutureDuckRuntime
from persona_engine.duck.persistence import DuckPersistence


class ProbeSubject:
    subject_id = "duck-future-probe-subject"

    def __init__(self):
        self.elapsed = 0.0
        self.observed = 0

    def snapshot(self):
        return {"subject_id": self.subject_id, "elapsed": self.elapsed, "observed": self.observed}

    def observe_event(self, payload):
        del payload
        self.observed += 1
        return {"accepted": True}

    def advance_time(self, elapsed_seconds):
        self.elapsed += float(elapsed_seconds)
        return {"elapsed": self.elapsed}


class ProbeBody:
    def __init__(self, body_id: str):
        self.body_id = body_id
        self.executions = 0

    def snapshot(self):
        return BodySnapshot(
            body_id=self.body_id,
            location="mockpond",
            orientation="forward",
            sensors=("vision", "sound"),
            effectors=("seek_information", "communicate", "practice", "inspect", "choose_independently", "reaffirm_commitment", "maintain", "wait"),
            state={"energy": 0.75, "sensory_load": 0.10, "need_for_movement": 0.10},
        )

    def observe(self, *, tick):
        del tick
        return []

    def affordances(self):
        return [
            Affordance("inspect", expected_world_effects={"information": 0.20}),
            Affordance("communicate", expected_world_effects={"social_contact": 0.20}),
            Affordance("wait"),
        ]

    def supports(self, action_type):
        return action_type in self.snapshot().effectors

    def execute(self, action, simulation, context):
        del action, context
        self.executions += 1
        return EmbodimentOutcome(True, "probe_executed", dict(simulation.predicted_world_effects), dict(simulation.predicted_self_effects))


def run_probe(cycles: int) -> dict:
    cycles = max(20, int(cycles))
    subject = ProbeSubject()
    body_a = ProbeBody("probe-body-a")
    body_b = ProbeBody("probe-body-b")
    base_utc = 1_800_000_000.0
    traces = 0
    service_errors = 0

    with tempfile.TemporaryDirectory(prefix="duck-future-probe-") as temp:
        persistence = DuckPersistence(temp)
        runtime = FutureDuckRuntime(subject, embodiment=body_a, persistence=persistence)
        split = cycles // 2
        for index in range(cycles):
            if index == split:
                runtime.swap_embodiment(body_b)
                trace = runtime.step()
                traces += int(trace is not None)
                if trace:
                    service_errors += len(trace.service_errors)
            runtime.ingest_observation(
                {
                    "description": f"deterministic probe observation {index}",
                    "salience": 0.10 + ((index % 5) * 0.02),
                    "self_relevance": 0.20,
                    "temporal_pattern_key": "probe-arrival",
                },
                utc_epoch=base_utc + index * 86.4,
                event_id=f"probe:{index}",
            )
            trace = runtime.step()
            if trace is None:
                raise RuntimeError(f"future runtime failed to process probe cycle {index}")
            traces += 1
            service_errors += len(trace.service_errors)
            if index == split:
                runtime.save()
                state = persistence.load()
                runtime = FutureDuckRuntime(subject, embodiment=body_b, persistence=persistence, state=state)

        digest = runtime.save()
        status = runtime.status()
        if runtime.subject_id != ProbeSubject.subject_id:
            raise RuntimeError("subject identity changed during future probe")
        if status["body_history"] != ["probe-body-a", "probe-body-b"]:
            raise RuntimeError(f"body transfer history mismatch: {status['body_history']}")
        if service_errors:
            raise RuntimeError(f"unexpected cognitive service failures: {service_errors}")
        routine = status["temporal_patterns"].get("routines", {}).get("probe-arrival", {})
        if int(routine.get("count", 0)) != cycles:
            raise RuntimeError("temporal routine did not survive full run/restart")
        return {
            "subject_id": runtime.subject_id,
            "cycles_requested": cycles,
            "cognitive_traces": traces,
            "final_tick": runtime.tick,
            "subject_elapsed_seconds": round(subject.elapsed, 6),
            "body_history": status["body_history"],
            "body_a_executions": body_a.executions,
            "body_b_executions": body_b.executions,
            "temporal_pattern_observations": int(routine.get("count", 0)),
            "last_beat": status["temporal_stamp"]["beat"],
            "service_errors": service_errors,
            "canonical_digest": digest,
            "result": "PASS",
        }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Run the deterministic DUCK future-build integration probe")
    parser.add_argument("--cycles", type=int, default=200)
    parser.add_argument("--output", default="")
    args = parser.parse_args(argv)
    result = run_probe(args.cycles)
    text = json.dumps(result, indent=2, sort_keys=True)
    if args.output:
        path = Path(args.output)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text + "\n", encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
