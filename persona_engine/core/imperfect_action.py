"""Bounded decision, execution, and learning imperfection."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
from typing import Any

from .capability_artifacts import CapabilityArtifact, CapabilityArtifactStore


@dataclass(frozen=True)
class ActionAttempt:
    action_id: str
    decision: str
    objectively_reasonable: bool
    executed: bool
    succeeded: bool
    failure_reason: str | None
    observed_outcome: str
    objective_cause: str
    learned_artifact_id: str | None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class ImperfectActionEngine:
    def __init__(self, seed: int):
        self.seed = int(seed) & 0xFFFFFFFFFFFFFFFF
        self.counter = 0

    def _draw(self, channel: str) -> float:
        payload = f"{self.seed}:{self.counter}:{channel}".encode("utf-8")
        self.counter += 1
        return int.from_bytes(hashlib.blake2b(payload, digest_size=8).digest(), "big") / float(2**64 - 1)

    def attempt(self, *, decision: str, objectively_reasonable: bool, skill: float, distraction: float,
                fatigue: float, observed_outcome: str, objective_cause: str, artifacts: CapabilityArtifactStore,
                now: float, supporting_event_ids=(), force_execution_failure: bool = False,
                force_wrong_learning: bool = False) -> ActionAttempt:
        skill = max(0.0, min(1.0, float(skill)))
        burden = max(0.0, min(1.0, (float(distraction) + float(fatigue)) / 2.0))
        success_probability = max(0.05, min(0.95, skill * (1.0 - burden * 0.65)))
        succeeded = not force_execution_failure and self._draw("execution") <= success_probability
        failure_reason = None if succeeded else "timing, distraction, fatigue, or insufficient skill"
        learned: CapabilityArtifact | None = None
        if force_wrong_learning or (succeeded and self._draw("learning") < 0.18):
            learned = artifacts.add(
                kind="belief_evidence",
                content=f"I inferred that {decision} caused {observed_outcome}.",
                source_tier=0,
                provenance={"stage": "learning", "objective_cause": objective_cause, "may_be_wrong": True},
                confidence=0.62,
                verification_state="uncertain",
                supporting_event_ids=supporting_event_ids,
                canonicality="subjective",
                created_at=now,
            )
        action_id = "action_" + hashlib.blake2b(f"{self.seed}:{self.counter}:{decision}".encode("utf-8"), digest_size=8).hexdigest()
        return ActionAttempt(
            action_id=action_id, decision=str(decision), objectively_reasonable=bool(objectively_reasonable),
            executed=True, succeeded=succeeded, failure_reason=failure_reason,
            observed_outcome=str(observed_outcome), objective_cause=str(objective_cause),
            learned_artifact_id=learned.artifact_id if learned else None,
        )
