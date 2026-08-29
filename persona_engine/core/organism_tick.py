"""World-body tick loop for the artificial character organism.

This module is generic. It applies profile parameters from a cartridge to
mutable world, body, sensorium, pressure, memory, and intention state without
knowing any character by name.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .memory import MemoryUnit, KnowledgeSource
from .intention import OpenLoop


@dataclass
class OrganismTickResult:
    server_truth: dict[str, Any]
    visible_context: dict[str, Any]
    sensorium_events: list[Any]


class OrganismTick:
    """Coordinates world and body changes before cognition/rendering."""

    def __init__(self, world_profile, body_profile):
        self.world_profile = world_profile
        self.body_profile = body_profile

    def idle(self, *, elapsed_seconds: float, now: float, world, body, sensorium, pressures, memory, intentions, world_elapsed_seconds: float | None = None) -> OrganismTickResult:
        # World duration and legacy body dynamics are deliberately separable.
        # M4 preserves full elapsed subject time without pretending old per-tick
        # body coefficients are validated real-time physiology.
        world_elapsed = elapsed_seconds if world_elapsed_seconds is None else max(0.0, float(world_elapsed_seconds))
        world_events = world.idle_events(world_elapsed, self.world_profile, now)
        sensory_delta = sum(getattr(ev, "intensity", 0.0) for ev in world_events if getattr(ev, "kind", "") in {"sensory_load", "ambient_event", "noise_change"})
        body_before = body.to_dict()
        body.apply_idle(elapsed_seconds, self.body_profile, sensory_delta=sensory_delta)
        made = sensorium.extend_from_world_events(world_events)
        made.extend(sensorium.derive_from_body(body, now, previous_body_state=body_before))
        self._couple_events(made, pressures, memory, intentions, now)
        return self._as_result(made, world, body)

    def interaction(self, *, user_text: str, server_truth: dict[str, Any], visible_context: dict[str, Any], now: float, world, body, sensorium, pressures, memory, intentions) -> OrganismTickResult:
        world_events = world.apply_host_facts(server_truth, visible_context, now)
        body_before = body.to_dict()
        body.apply_interaction(intensity=0.2 + min(0.8, len(user_text) / 500.0))
        if any(getattr(ev, "kind", "") in {"ambient_event", "noise_change"} for ev in world_events):
            body.apply_ambient_load(0.12)
        made = sensorium.extend_from_world_events(world_events)
        made.extend(sensorium.derive_from_body(body, now, previous_body_state=body_before))
        self._couple_events(made, pressures, memory, intentions, now)
        return self._as_result(made, world, body)

    def _couple_events(self, events, pressures, memory, intentions, now: float):
        for ev in events:
            kind = getattr(ev, "kind", "")
            intensity = float(getattr(ev, "intensity", 0.0))
            detail = str(getattr(ev, "detail", ""))
            if kind in {"user_absence"}:
                pressures.ensure("attachment").magnitude = min(1.0, pressures.ensure("attachment").magnitude + intensity * 0.10)
                pressures.ensure("fear").magnitude = min(1.0, pressures.ensure("fear").magnitude + intensity * 0.08)
                intentions.add_open_loop(OpenLoop(
                    topic="unresolved absence pressure",
                    emotional_charge=intensity,
                    created_at=now,
                    last_touched=now,
                    urgency=intensity,
                    preferred_resolution="notice return without claiming hidden motive",
                ))
            elif kind in {"ambient_event", "movement_need", "body_state", "sensory_load"}:
                # These are transition events, so pressure changes represent the
                # onset/change itself rather than simulation sampling frequency.
                pressures.ensure("curiosity").magnitude = min(1.0, pressures.ensure("curiosity").magnitude + intensity * 0.10)
                if kind in {"sensory_load", "body_state"}:
                    pressures.ensure("fear").magnitude = min(1.0, pressures.ensure("fear").magnitude + intensity * 0.05)
            if intensity >= 0.45:
                if kind == "body_state":
                    content = f"I noticed my body state: {detail}"
                elif kind == "movement_need":
                    content = f"I felt a need to move: {detail}"
                elif kind == "sensory_load":
                    content = f"I felt sensory load: {detail}"
                elif kind == "user_absence":
                    content = f"I noticed your absence: {detail}"
                elif kind == "ambient_event":
                    content = f"I noticed an ambient event: {detail}"
                else:
                    content = f"I noticed {kind}: {detail}"
                memory.add(MemoryUnit(
                    content=content,
                    created_at=now,
                    emotional_intensity=min(1.0, intensity),
                    relationship_relevance=0.3 if kind == "user_absence" else 0.1,
                    identity_relevance=0.2,
                    unresolved=kind in {"user_absence", "movement_need"},
                    source=KnowledgeSource.OBSERVED,
                    tags={"sensorium", kind},
                ))

    def _as_result(self, events, world, body) -> OrganismTickResult:
        server_truth: dict[str, Any] = {}
        visible_context: dict[str, Any] = {
            "world_summary": world.summary(),
            "body_summary": body.summary(),
        }
        for idx, ev in enumerate(events):
            if getattr(ev, "visible_to_character", True):
                key, value = ev.to_fact(idx)
                server_truth[key] = value
        return OrganismTickResult(server_truth=server_truth, visible_context=visible_context, sensorium_events=events)
