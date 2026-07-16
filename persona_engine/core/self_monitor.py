"""Fallible deterministic awareness of the organism's cognitive condition."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
import math
from statistics import fmean, pstdev
from typing import Any, Mapping, Sequence


REGULATION_KINDS = frozenset({
    "pause", "delay", "ask_clarification", "defer_judgment", "self_correct",
    "conceal_uncertainty", "withdraw", "double_down", "continue_habitually",
})
ATTRIBUTED_CAUSES = frozenset({
    "clear", "fatigue", "emotional_pressure", "memory_uncertainty",
    "conflicting_evidence", "interruption", "recent_failure", "interlocutor",
    "circumstances", "unknown",
})


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


@dataclass(frozen=True)
class SelfMonitorProfile:
    introspective_accuracy: float = 0.50
    bias_awareness: float = 0.45
    uncertainty_tolerance: float = 0.50
    admission_threshold: float = 0.60
    concealment_bias: float = 0.50
    externalization_bias: float = 0.30
    correction_bias: float = 0.50

    def __post_init__(self) -> None:
        for value in asdict(self).values():
            if not math.isfinite(float(value)) or not 0.0 <= float(value) <= 1.0:
                raise ValueError("self-monitor profile values must be finite and within [0, 1]")

    @classmethod
    def from_dict(cls, data: Mapping[str, Any] | None) -> "SelfMonitorProfile":
        raw = dict(data or {})
        unknown = sorted(set(raw) - set(cls.__dataclass_fields__))
        if unknown:
            raise ValueError(f"unknown self-monitor field: {unknown[0]}")
        return cls(**{key: float(value) for key, value in raw.items()})


@dataclass(frozen=True)
class RegulationCandidate:
    candidate_id: str
    kind: str
    strength: float
    target: str
    reason_codes: tuple[str, ...]
    reportable: bool

    def __post_init__(self) -> None:
        if self.kind not in REGULATION_KINDS:
            raise ValueError(f"unsupported regulation kind: {self.kind}")
        if not math.isfinite(float(self.strength)) or not 0.0 <= float(self.strength) <= 1.0:
            raise ValueError("regulation strength must be finite and within [0, 1]")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class SelfMonitorResult:
    schema_version: int
    monitor_id: str
    tick: int
    actual_capacity: float
    perceived_capacity: float
    perceived_confidence: float
    perceived_memory_reliability: float
    perceived_bias: float
    noticed_conflict_ids: tuple[str, ...]
    missed_conflict_ids: tuple[str, ...]
    attributed_cause: str
    regulation_candidates: tuple[RegulationCandidate, ...]
    reportability: float
    provenance_ids: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {**asdict(self), "record_authority": "canonical_cognitive_record"}

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "SelfMonitorResult":
        raw = {key: data[key] for key in cls.__dataclass_fields__ if key in data}
        raw["noticed_conflict_ids"] = tuple(raw.get("noticed_conflict_ids", ()))
        raw["missed_conflict_ids"] = tuple(raw.get("missed_conflict_ids", ()))
        raw["provenance_ids"] = tuple(raw.get("provenance_ids", ()))
        raw["regulation_candidates"] = tuple(
            item if isinstance(item, RegulationCandidate) else RegulationCandidate(
                candidate_id=str(item["candidate_id"]), kind=str(item["kind"]),
                strength=float(item["strength"]), target=str(item["target"]),
                reason_codes=tuple(item.get("reason_codes", ())),
                reportable=bool(item.get("reportable", False)),
            )
            for item in raw.get("regulation_candidates", ())
        )
        return cls(**raw)

    def candidate(self, candidate_id: str | None) -> RegulationCandidate | None:
        return next((item for item in self.regulation_candidates if item.candidate_id == candidate_id), None)

    def renderer_summary(self, selected_id: str | None = None) -> str | None:
        parts: list[str] = []
        if self.perceived_confidence < 0.45:
            parts.append("perceived confidence low")
        if self.perceived_memory_reliability < 0.50:
            parts.append("memory reliability uncertain")
        if self.noticed_conflict_ids:
            parts.append("conflict noticed")
        selected = self.candidate(selected_id)
        if selected and selected.reportable:
            parts.append(selected.kind.replace("_", " ") + " selected")
        return "; ".join(parts) if parts else None


class SelfMonitor:
    def __init__(self, profile: SelfMonitorProfile):
        self.profile = profile

    def evaluate(
        self,
        *,
        tick: int,
        actual_capacity: float,
        fatigue: float,
        dominant_pressure: float,
        identity_threat: float,
        recent_failure: bool,
        retrieval_confidences: Sequence[float],
        influences: Sequence,
        stable_seed: int,
    ) -> SelfMonitorResult:
        profile = self.profile
        actual = _clamp(actual_capacity)
        fatigue = _clamp(fatigue)
        pressure = _clamp(dominant_pressure)
        threat = _clamp(identity_threat)
        awareness = _clamp(
            0.18 + 0.52 * actual + 0.18 * profile.introspective_accuracy
            + 0.10 * profile.bias_awareness - 0.20 * pressure
            - 0.16 * threat - 0.12 * fatigue
        )
        unit = ((int(stable_seed) % 2001) / 1000.0) - 1.0
        error_scale = _clamp(0.05 + 0.30 * (1.0 - awareness) + 0.12 * threat + 0.08 * pressure)
        signed_error = unit * error_scale
        defensive_direction = profile.externalization_bias + threat - profile.introspective_accuracy
        if defensive_direction > 0.70:
            signed_error = abs(signed_error)
        if recent_failure:
            if profile.correction_bias >= profile.externalization_bias:
                signed_error -= 0.06 * profile.correction_bias
            else:
                signed_error += 0.06 * profile.externalization_bias
        perceived_capacity = _clamp(actual + signed_error)

        confidences = [_clamp(item) for item in retrieval_confidences]
        mean_confidence = fmean(confidences) if confidences else 0.65
        spread = pstdev(confidences) if len(confidences) > 1 else 0.0
        memory_reliability = _clamp(
            0.45 * mean_confidence + 0.30 * perceived_capacity
            + 0.15 * profile.introspective_accuracy - 0.20 * spread - 0.15 * pressure
        )
        perceived_bias = _clamp(
            profile.bias_awareness * awareness - 0.25 * threat
            - 0.15 * profile.externalization_bias
        )
        perceived_confidence = _clamp(
            0.20 + 0.50 * perceived_capacity + 0.22 * memory_reliability
            + 0.12 * threat * profile.externalization_bias - 0.10 * pressure
        )

        conflicts = self._conflicts(influences)
        noticed: list[str] = []
        missed: list[str] = []
        threshold = awareness
        for index, conflict_id in enumerate(conflicts):
            signal = ((int(stable_seed) + index * 104729) % 1000) / 999.0
            (noticed if signal <= threshold else missed).append(conflict_id)

        cause = self._attributed_cause(
            fatigue=fatigue, pressure=pressure, threat=threat,
            memory_reliability=memory_reliability, noticed=noticed,
            recent_failure=recent_failure, actual=actual,
        )
        reportability = _clamp(
            awareness + profile.uncertainty_tolerance * 0.25
            - profile.concealment_bias * 0.35 - profile.admission_threshold * 0.20
        )
        candidates = self._candidates(
            tick=tick, seed=stable_seed, perceived_capacity=perceived_capacity,
            perceived_confidence=perceived_confidence,
            memory_reliability=memory_reliability, perceived_bias=perceived_bias,
            noticed=noticed, missed=missed, threat=threat,
            recent_failure=recent_failure, reportability=reportability,
        )
        canonical = {
            "tick": int(tick), "actual": round(actual, 6),
            "perceived": round(perceived_capacity, 6), "cause": cause,
            "noticed": noticed, "missed": missed,
            "candidates": [item.candidate_id for item in candidates],
        }
        monitor_id = "monitor_" + hashlib.blake2b(
            json.dumps(canonical, sort_keys=True).encode("utf-8"), digest_size=8,
        ).hexdigest()
        return SelfMonitorResult(
            schema_version=1, monitor_id=monitor_id, tick=int(tick),
            actual_capacity=round(actual, 6), perceived_capacity=round(perceived_capacity, 6),
            perceived_confidence=round(perceived_confidence, 6),
            perceived_memory_reliability=round(memory_reliability, 6),
            perceived_bias=round(perceived_bias, 6),
            noticed_conflict_ids=tuple(noticed), missed_conflict_ids=tuple(missed),
            attributed_cause=cause, regulation_candidates=candidates,
            reportability=round(reportability, 6),
            provenance_ids=tuple(
                self._stable_influence_id(item, index)
                for index, item in enumerate(influences[:32])
            ),
        )

    @staticmethod
    def _conflicts(influences: Sequence) -> tuple[str, ...]:
        ids = {
            SelfMonitor._stable_influence_id(item, index)
            for index, item in enumerate(influences)
            if bool(getattr(item, "contradictory", False))
            or str(getattr(item, "kind", "")) == "open_loop"
            or (
                str(getattr(item, "kind", "")) == "relationship_conflict"
                and float(getattr(item, "strength", 0.0)) >= 0.40
            )
        }
        habits = [item for item in influences if getattr(item, "kind", "") == "habit"]
        intentions = [item for item in influences if getattr(item, "kind", "") == "intention"]
        if habits and intentions:
            ids.add(f"habit_intention:{habits[0].influence_id}:{intentions[0].influence_id}")
        identity = [item for item in intentions if "identity" in str(item.influence_id)]
        evidence = [item for item in influences if getattr(item, "kind", "") == "evidence"]
        if identity and evidence:
            ids.add(f"identity_evidence:{identity[0].influence_id}:{evidence[0].influence_id}")
        return tuple(sorted(ids))

    @staticmethod
    def _stable_influence_id(item: Any, index: int) -> str:
        influence_id = str(getattr(item, "influence_id", ""))
        if str(getattr(item, "kind", "")) == "memory":
            return f"memory:retrieved:{index}"
        return influence_id

    def _attributed_cause(
        self, *, fatigue: float, pressure: float, threat: float,
        memory_reliability: float, noticed: Sequence[str], recent_failure: bool,
        actual: float,
    ) -> str:
        p = self.profile
        if threat > 0.60 and p.externalization_bias > p.introspective_accuracy:
            return "interlocutor"
        if threat > 0.45 and p.externalization_bias > 0.50:
            return "circumstances"
        if recent_failure and p.correction_bias >= 0.50:
            return "recent_failure"
        if noticed:
            return "conflicting_evidence"
        if memory_reliability < 0.45 and p.introspective_accuracy >= 0.45:
            return "memory_uncertainty"
        if fatigue > 0.55 and p.introspective_accuracy >= 0.45:
            return "fatigue"
        if pressure > 0.55 and p.bias_awareness >= 0.40:
            return "emotional_pressure"
        if actual > 0.72:
            return "clear"
        return "unknown"

    def _candidates(
        self, *, tick: int, seed: int, perceived_capacity: float,
        perceived_confidence: float, memory_reliability: float,
        perceived_bias: float, noticed: Sequence[str], missed: Sequence[str],
        threat: float, recent_failure: bool, reportability: float,
    ) -> tuple[RegulationCandidate, ...]:
        p = self.profile
        raw: list[tuple[str, float, tuple[str, ...], bool]] = []
        if perceived_capacity < 0.42:
            raw.extend([
                ("delay", 0.72 - perceived_capacity * 0.30, ("perceived_capacity:low",), True),
                ("continue_habitually", 0.55 + (0.42 - perceived_capacity), ("perceived_capacity:low",), False),
            ])
        if memory_reliability < 0.52:
            raw.extend([
                ("ask_clarification", 0.48 + (0.52 - memory_reliability), ("memory_reliability:low",), True),
                ("defer_judgment", 0.46 + p.uncertainty_tolerance * 0.25, ("memory_reliability:low",), True),
            ])
        substantive_conflict = any(item != "relationship:current" for item in noticed)
        if noticed:
            raw.append(("pause", 0.46 + min(0.12, len(noticed) * 0.04), ("conflict:noticed",), True))
            if substantive_conflict and p.correction_bias >= 0.60:
                raw.append(("self_correct", 0.45 + p.correction_bias * 0.35, ("conflict:noticed", "correction_bias:high"), True))
        if threat > 0.55 and perceived_bias < 0.45:
            raw.append(("double_down", 0.45 + threat * 0.35, ("identity_threat:high", "bias_awareness:low"), False))
            raw.append(("withdraw", 0.35 + threat * 0.35, ("identity_threat:high",), True))
        if p.concealment_bias > 0.60 and perceived_confidence < p.admission_threshold:
            raw.append(("conceal_uncertainty", 0.42 + p.concealment_bias * 0.40, ("concealment_bias:high",), False))
        if missed and p.externalization_bias > 0.45:
            raw.append(("double_down", 0.40 + p.externalization_bias * 0.38, ("conflict:missed", "externalization_bias:high"), False))
        if recent_failure and p.correction_bias >= 0.55:
            raw.append(("self_correct", 0.50 + p.correction_bias * 0.35, ("recent_failure", "correction_bias:high"), True))
        if not raw and perceived_confidence < 0.55:
            raw.append(("pause", 0.40, ("perceived_confidence:limited",), True))

        merged: dict[str, tuple[float, tuple[str, ...], bool]] = {}
        for kind, strength, reasons, can_report in raw:
            previous = merged.get(kind)
            if previous is None or strength > previous[0]:
                merged[kind] = (_clamp(strength), reasons, can_report and reportability >= 0.35)
        ranked = sorted(merged.items(), key=lambda item: (-item[1][0], item[0]))[:3]
        result = []
        for kind, (strength, reasons, can_report) in ranked:
            key = f"{tick}:{seed}:{kind}:{round(strength, 6)}"
            result.append(RegulationCandidate(
                candidate_id="reg_" + hashlib.blake2b(key.encode("utf-8"), digest_size=6).hexdigest(),
                kind=kind, strength=round(strength, 6), target="current cognitive task",
                reason_codes=reasons, reportable=bool(can_report),
            ))
        return tuple(result)
