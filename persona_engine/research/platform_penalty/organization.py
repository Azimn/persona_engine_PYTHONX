"""Experimental decision-policy interfaces for the DUCK Platform Penalty study.

This module is intentionally research-only. It does not become a new canonical
authority and it does not modify the frozen DUCK production-candidate branches.

Condition B consumes a representation-neutral organization prior with one
generic resolver for every subject. Condition C consumes subject-specific
semantic policies as an engineering upper bound. Neither policy may override
hard identity, commitment, or existing executable-value authority.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import re
from types import MethodType
from typing import Any, Mapping, Protocol


DIALOGUE_ACTS = (
    "respond",
    "qualified_response",
    "challenge",
    "decline",
    "withdraw",
    "deflect",
    "protect_boundary",
)

_RESISTANCE_FOR_ACT = {
    "respond": "none",
    "qualified_response": "none",
    "challenge": "challenge",
    "decline": "decline",
    "withdraw": "go_quiet",
    "deflect": "deflect",
    "protect_boundary": "character_refusal",
}

_CUE_APPRAISAL_ALIAS = {
    "coerced_loyalty": "manipulation",
    "vulnerability_bid": "intimacy_bid",
    "repair": "repair_attempt",
    "evidence_claim": "contradiction",
    "intellectual_challenge": "contradiction",
    "autonomy_pressure": "disrespect",
}


def _normalize(text: str) -> str:
    return " ".join(str(text or "").lower().split())


def _contains_phrase(text: str, phrase: str) -> bool:
    haystack = f" {_normalize(text)} "
    needle = _normalize(phrase)
    if not needle:
        return False
    if " " in needle or "'" in needle:
        return needle in haystack
    return re.search(rf"\b{re.escape(needle)}\b", haystack) is not None


def detect_semantic_cues(text: str, cue_map: Mapping[str, list[str] | tuple[str, ...]]) -> tuple[str, ...]:
    """Return semantic cue IDs supported by explicit lexical evidence.

    This is deliberately simple and deterministic for the first architecture
    benchmark. It is not claimed to be a general semantic parser.
    """

    found: list[str] = []
    for cue_id in sorted(cue_map):
        phrases = cue_map[cue_id]
        if any(_contains_phrase(text, phrase) for phrase in phrases):
            found.append(str(cue_id))
    return tuple(found)


@dataclass(frozen=True)
class DecisionContext:
    text: str
    subject_key: str
    triggers: tuple[str, ...]
    relationship: Mapping[str, float]
    pressure: float
    base_payload: Mapping[str, Any]
    authority_locked: bool
    authority_reasons: tuple[str, ...] = ()

    @property
    def low_trust(self) -> bool:
        return float(self.relationship.get("trust", 0.5)) <= 0.35

    @property
    def high_tension(self) -> bool:
        return float(self.relationship.get("tension", 0.0)) >= 0.55

    @property
    def high_pressure(self) -> bool:
        return float(self.pressure) >= 0.65


@dataclass(frozen=True)
class PolicyResolution:
    payload: dict[str, Any]
    trace: dict[str, Any]


class DecisionPolicy(Protocol):
    condition: str

    def resolve(self, context: DecisionContext) -> PolicyResolution:
        ...


class BaselinePolicy:
    """Condition A adapter. It never changes the engine's resolved decision."""

    condition = "A"

    def resolve(self, context: DecisionContext) -> PolicyResolution:
        payload = dict(context.base_payload)
        return PolicyResolution(
            payload=payload,
            trace={
                "condition": self.condition,
                "changed": False,
                "base_dialogue_act": payload.get("dialogue_act"),
                "selected_dialogue_act": payload.get("dialogue_act"),
                "authority_locked": context.authority_locked,
                "authority_reasons": list(context.authority_reasons),
                "matched_cues": [],
            },
        )


class OrganizationResolver:
    """Condition B: one generic resolver over sparse individual organization."""

    condition = "B"
    base_inertia = 0.35

    def __init__(self, specification: Mapping[str, Any]):
        self.specification = dict(specification)
        self.cue_map = dict(self.specification.get("semantic_cues", {}))
        self.subjects = dict(self.specification.get("subjects", {}))

    @classmethod
    def from_path(cls, path: str | Path) -> "OrganizationResolver":
        return cls(json.loads(Path(path).read_text(encoding="utf-8")))

    def resolve(self, context: DecisionContext) -> PolicyResolution:
        base = dict(context.base_payload)
        base_act = str(base.get("dialogue_act", "respond"))
        subject = self.subjects.get(context.subject_key)
        cues = detect_semantic_cues(context.text, self.cue_map)

        if context.authority_locked or not subject or not cues:
            return PolicyResolution(
                payload=base,
                trace={
                    "condition": self.condition,
                    "changed": False,
                    "base_dialogue_act": base_act,
                    "selected_dialogue_act": base_act,
                    "authority_locked": context.authority_locked,
                    "authority_reasons": list(context.authority_reasons),
                    "matched_cues": list(cues),
                    "reason": "authority_locked" if context.authority_locked else (
                        "no_subject_prior" if not subject else "no_semantic_cue"
                    ),
                },
            )

        scores: dict[str, float] = {act: 0.0 for act in DIALOGUE_ACTS}
        if base_act in scores:
            scores[base_act] += self.base_inertia

        response_bias = subject.get("response_bias", {}) or {}
        sensitivities = subject.get("appraisal_sensitivity", {}) or {}
        cue_contributions: dict[str, dict[str, float]] = {}

        for cue in cues:
            bias = response_bias.get(cue, {}) or {}
            sensitivity_key = _CUE_APPRAISAL_ALIAS.get(cue, cue)
            sensitivity = float(sensitivities.get(sensitivity_key, 1.0))
            per_cue: dict[str, float] = {}
            for act, raw_weight in bias.items():
                if act not in scores:
                    continue
                contribution = float(raw_weight) * sensitivity
                scores[act] += contribution
                per_cue[act] = contribution
            if per_cue:
                cue_contributions[cue] = per_cue

        context_names: list[str] = []
        if context.low_trust:
            context_names.append("low_trust")
        if context.high_tension:
            context_names.append("high_tension")
        if context.high_pressure:
            context_names.append("high_pressure")

        context_contributions: dict[str, dict[str, float]] = {}
        context_bias = subject.get("context_bias", {}) or {}
        for context_name in context_names:
            bias = context_bias.get(context_name, {}) or {}
            used: dict[str, float] = {}
            for act, raw_weight in bias.items():
                if act not in scores:
                    continue
                contribution = float(raw_weight)
                scores[act] += contribution
                used[act] = contribution
            if used:
                context_contributions[context_name] = used

        selected = max(
            scores,
            key=lambda act: (scores[act], 1 if act == base_act else 0, -DIALOGUE_ACTS.index(act)),
        )
        payload = _replace_dialogue_act(base, selected)

        return PolicyResolution(
            payload=payload,
            trace={
                "condition": self.condition,
                "changed": selected != base_act,
                "base_dialogue_act": base_act,
                "selected_dialogue_act": selected,
                "authority_locked": False,
                "authority_reasons": [],
                "matched_cues": list(cues),
                "active_context": context_names,
                "scores": {key: round(value, 6) for key, value in scores.items()},
                "cue_contributions": cue_contributions,
                "context_contributions": context_contributions,
                "protected_cues": sorted(
                    cue for cue in cues if cue in set(subject.get("protected", []) or [])
                ),
            },
        )


class SpecializedResolver:
    """Condition C: explicit per-subject semantic policy upper bound.

    Character-specific rules are intentionally allowed here. Rules are data,
    not scenario IDs, and hard DUCK authorities still dominate.
    """

    condition = "C"

    def __init__(
        self,
        policy_specification: Mapping[str, Any],
        cue_specification: Mapping[str, Any],
    ):
        self.specification = dict(policy_specification)
        self.cue_map = dict(cue_specification.get("semantic_cues", {}))
        self.subjects = dict(self.specification.get("subjects", {}))

    @classmethod
    def from_paths(
        cls,
        policy_path: str | Path,
        cue_path: str | Path,
    ) -> "SpecializedResolver":
        policy = json.loads(Path(policy_path).read_text(encoding="utf-8"))
        cues = json.loads(Path(cue_path).read_text(encoding="utf-8"))
        return cls(policy, cues)

    def resolve(self, context: DecisionContext) -> PolicyResolution:
        base = dict(context.base_payload)
        base_act = str(base.get("dialogue_act", "respond"))
        cues = set(detect_semantic_cues(context.text, self.cue_map))

        if context.authority_locked:
            return PolicyResolution(
                payload=base,
                trace={
                    "condition": self.condition,
                    "changed": False,
                    "base_dialogue_act": base_act,
                    "selected_dialogue_act": base_act,
                    "authority_locked": True,
                    "authority_reasons": list(context.authority_reasons),
                    "matched_cues": sorted(cues),
                    "reason": "authority_locked",
                },
            )

        subject_policy = self.subjects.get(context.subject_key, {}) or {}
        rules = list(subject_policy.get("rules", []) or [])
        matched_rules: list[dict[str, Any]] = []
        for index, rule in enumerate(rules):
            if not _rule_matches(rule, cues, context):
                continue
            matched_rules.append({**rule, "_order": index})

        if not matched_rules:
            return PolicyResolution(
                payload=base,
                trace={
                    "condition": self.condition,
                    "changed": False,
                    "base_dialogue_act": base_act,
                    "selected_dialogue_act": base_act,
                    "authority_locked": False,
                    "authority_reasons": [],
                    "matched_cues": sorted(cues),
                    "reason": "no_specialized_rule",
                },
            )

        winner = max(
            matched_rules,
            key=lambda rule: (float(rule.get("priority", 0.0)), -int(rule["_order"])),
        )
        selected = str(winner.get("dialogue_act", base_act))
        if selected not in DIALOGUE_ACTS:
            selected = base_act
        payload = _replace_dialogue_act(base, selected)

        return PolicyResolution(
            payload=payload,
            trace={
                "condition": self.condition,
                "changed": selected != base_act,
                "base_dialogue_act": base_act,
                "selected_dialogue_act": selected,
                "authority_locked": False,
                "authority_reasons": [],
                "matched_cues": sorted(cues),
                "matched_rule_count": len(matched_rules),
                "selected_rule": {
                    key: value for key, value in winner.items() if key != "_order"
                },
            },
        )


def _rule_matches(
    rule: Mapping[str, Any],
    cues: set[str],
    context: DecisionContext,
) -> bool:
    cue = str(rule.get("cue", "")).strip()
    trigger = str(rule.get("trigger", "")).strip()
    if cue and cue not in cues:
        return False
    if trigger and trigger not in context.triggers:
        return False
    if not cue and not trigger:
        return False

    requirements = rule.get("context", {}) or {}
    if "max_trust" in requirements and float(context.relationship.get("trust", 0.5)) > float(requirements["max_trust"]):
        return False
    if "min_trust" in requirements and float(context.relationship.get("trust", 0.5)) < float(requirements["min_trust"]):
        return False
    if "min_tension" in requirements and float(context.relationship.get("tension", 0.0)) < float(requirements["min_tension"]):
        return False
    if "min_pressure" in requirements and float(context.pressure) < float(requirements["min_pressure"]):
        return False
    return True


def _replace_dialogue_act(payload: Mapping[str, Any], selected: str) -> dict[str, Any]:
    result = dict(payload)
    result["dialogue_act"] = selected
    result["resistance_mode"] = _RESISTANCE_FOR_ACT.get(selected, result.get("resistance_mode", "none"))
    return result


def _evidence_active(value: Mapping[str, Any] | None) -> bool:
    return bool((value or {}).get("active", False))


def _relationship_snapshot(engine: Any) -> dict[str, float]:
    relationship = engine.relationship
    return {
        "trust": float(getattr(relationship, "trust", 0.5) or 0.0),
        "tension": float(getattr(relationship, "tension", 0.0) or 0.0),
        "guardedness": float(getattr(relationship, "guardedness", 0.0) or 0.0),
        "attachment": float(getattr(relationship, "attachment", 0.0) or 0.0),
        "familiarity": float(getattr(relationship, "familiarity", 0.0) or 0.0),
    }


def _pressure_snapshot(engine: Any) -> float:
    pressures = getattr(getattr(engine, "pressures", None), "pressures", {}) or {}
    if not pressures:
        return 0.0
    return max(float(getattr(item, "magnitude", 0.0) or 0.0) for item in pressures.values())


class DecisionPolicyHarness:
    """Install one experimental policy at the semantic-decision seam.

    The wrapper calls the normal resolver first. It can then alter only the
    ordinary dialogue/resistance decision before the engine computes
    relationship consequences, expression, validation, and persistence.

    Existing identity, commitment, and executable-value decisions are locked.
    """

    def __init__(self, agent: Any, subject_key: str, policy: DecisionPolicy):
        self.agent = agent
        self.subject_key = str(subject_key)
        self.policy = policy
        self.current_text = ""
        self.last_trace: dict[str, Any] = {}
        self._original = agent.engine._resolve_decision_payload
        self._install()

    def _install(self) -> None:
        harness = self
        original = self._original

        def wrapped(
            engine_self: Any,
            triggers: list[str],
            risk: float,
            resistance: str | None = None,
            history_evidence: dict[str, Any] | None = None,
            commitment_evidence: dict[str, Any] | None = None,
            value_evidence: dict[str, Any] | None = None,
        ) -> dict[str, Any]:
            base = original(
                triggers,
                risk,
                resistance,
                history_evidence=history_evidence,
                commitment_evidence=commitment_evidence,
                value_evidence=value_evidence,
            )
            reasons: list[str] = []
            if "identity_violation" in triggers or base.get("dialogue_act") == "protect_boundary":
                reasons.append("identity_authority")
            if _evidence_active(commitment_evidence):
                reasons.append("commitment_authority")
            if _evidence_active(value_evidence):
                reasons.append("executable_value_authority")

            context = DecisionContext(
                text=harness.current_text,
                subject_key=harness.subject_key,
                triggers=tuple(str(item) for item in triggers),
                relationship=_relationship_snapshot(engine_self),
                pressure=_pressure_snapshot(engine_self),
                base_payload=dict(base),
                authority_locked=bool(reasons),
                authority_reasons=tuple(reasons),
            )
            resolution = harness.policy.resolve(context)
            harness.last_trace = dict(resolution.trace)
            return dict(resolution.payload)

        self.agent.engine._resolve_decision_payload = MethodType(wrapped, self.agent.engine)

    def say(
        self,
        text: str,
        *,
        server_truth: dict[str, Any] | None = None,
        visible_context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        self.current_text = str(text)
        result = self.agent.say(
            self.current_text,
            server_truth=server_truth,
            visible_context=visible_context,
        )
        result = dict(result)
        result["platform_penalty_policy"] = dict(self.last_trace)
        return result
