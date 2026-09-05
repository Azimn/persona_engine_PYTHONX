"""Bridge between DUCK organism cognition and the persistent Wayfarer subject."""

from __future__ import annotations

from typing import Protocol

from persona_engine.agent import CharacterAgent


class SubjectPort(Protocol):
    @property
    def subject_id(self) -> str: ...
    def snapshot(self) -> dict: ...
    def observe_event(self, payload: dict) -> dict | None: ...
    def advance_time(self, elapsed_seconds: float) -> dict: ...


class WayfarerSubjectAdapter:
    """Use the existing CharacterAgent as DUCK's continuing subject authority."""

    def __init__(self, agent: CharacterAgent):
        self.agent = agent

    @property
    def subject_id(self) -> str:
        status = self.agent.writer_status()
        return str(status.get("subject_uuid") or self.agent.engine.identity.entity_uuid or self.agent.engine.identity.name)

    def snapshot(self) -> dict:
        return self.agent.public_status()

    def observe_event(self, payload: dict) -> dict | None:
        annotation = payload.get("semantic_annotation")
        if not annotation:
            return None
        return self.agent.observe_semantic_event(
            annotation,
            str(payload.get("observed_text", payload.get("description", "event"))),
            goal_preference=float(payload.get("goal_preference", 0.0) or 0.0),
            identity_sensitivity=float(payload.get("identity_sensitivity", 0.5) or 0.5),
            perceived_control=float(payload.get("perceived_control", 0.5) or 0.5),
        )

    def advance_time(self, elapsed_seconds: float) -> dict:
        return self.agent.advance_time(float(elapsed_seconds), source="duck", record_event=True)

    def record_delivery_receipt(self, receipt: dict) -> dict:
        """Write host-authoritative speech delivery into lived subject history."""
        return self.agent.record_delivery_receipt(receipt, record_event=True)
