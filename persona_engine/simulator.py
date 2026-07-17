"""Scripted conversation simulator for deterministic engine checks.

Supports optional server_truth and visible_context per turn, plus a conservative
fact-leak diagnostic that warns if the renderer introduces capitalized proper
nouns or known concrete-object terms outside the visible frame.
"""

from __future__ import annotations

import argparse
import os
import re
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import yaml

from persona_engine.agent import CharacterAgent
from persona_engine.core.autobiographical_reconsolidation import ReconsolidationContext

_CONCRETE_OBJECTS = {"door", "car", "phone", "window", "person", "someone", "outside", "footsteps"}
_SAFE_INTERPRETIVE_TERMS = {
    "a", "an", "and", "as", "be", "can", "character", "cause", "certainty", "challenge",
    "caution", "closeness", "continuity", "distance", "evidence", "for", "integrity",
    "better", "is", "long", "may", "not", "or", "phrase", "possible", "precision", "pressure",
    "proof", "read", "safer", "settle", "sincere", "some", "support", "tension", "than",
    "the", "to", "trust", "uncertainty", "unproven", "user", "visible", "watchfulness",
    "while", "without",
}
def _get_path(data: dict, dotted: str):
    cur = data
    for part in dotted.split("."):
        if isinstance(cur, dict):
            cur = cur.get(part)
        else:
            return None
    return cur


def _terms_from(value) -> set[str]:
    text = str(value)
    return {t.lower() for t in re.findall(r"[A-Za-z][A-Za-z0-9_'-]*", text)}


def _fact_leak_warnings(text: str, turn: dict, result: dict, label: str = "response") -> list[str]:
    allowed: set[str] = set()
    allowed |= _terms_from(turn.get("user_input", ""))
    allowed |= _terms_from(turn.get("server_truth", {}))
    allowed |= _terms_from(turn.get("visible_context", {}))
    allowed |= _terms_from(result.get("system_prompt", ""))
    for belief in result.get("interpretive_belief_trace", []) or []:
        for key in ("support_keys", "source_ids"):
            allowed |= _terms_from(belief.get(key, []))
    allowed |= _SAFE_INTERPRETIVE_TERMS
    sentence_initials = {
        match.group(1).lower()
        for match in re.finditer(r"(?:^|[.!?:;]\s+)([A-Z][a-zA-Z0-9_'-]{1,})", text)
    }
    # Capitalization at a sentence boundary is not named-entity evidence by
    # itself. Concrete vocabulary is still checked independently below.
    warnings = []
    for token in re.findall(r"\b[A-Z][a-zA-Z0-9_'-]{2,}\b", text):
        lowered = token.lower()
        if lowered in sentence_initials:
            continue
        if lowered not in allowed and lowered not in {"the", "and", "but"}:
            warnings.append(f"{label} proper noun/object not in visible frame: {token}")
    for obj in _CONCRETE_OBJECTS:
        if re.search(rf"\b{re.escape(obj)}\b", text.lower()) and obj not in allowed:
            warnings.append(f"{label} concrete object not in visible frame: {obj}")
    return warnings


def _run_life_steps(agent: CharacterAgent, steps: list[dict], aliases: dict[str, str] | None = None) -> int:
    """Run compact simulated-life setup/check steps through approved agent APIs."""

    aliases = aliases if aliases is not None else {}
    failures = 0
    for index, step in enumerate(steps, start=1):
        kind = str(step.get("type", ""))
        result = None
        try:
            if kind == "world_event":
                payload = dict(step.get("event", {}))
                event_payload = dict(payload.get("payload", {}))
                for key in ("corrects_world_event_id", "contradicts_interpretation_id"):
                    if key in event_payload:
                        event_payload[key] = aliases.get(str(event_payload[key]), str(event_payload[key]))
                payload["payload"] = event_payload
                result = agent.record_world_event(**payload)
                if step.get("as"):
                    aliases[str(step["as"])] = result["event_id"]
            elif kind == "subjective_experience":
                event_id = aliases.get(str(step.get("event")), str(step.get("event", "")))
                result = agent.perceive_world_event(event_id, **dict(step.get("perception", {})))
                if step.get("as") and result:
                    aliases[str(step["as"])] = result["experience_id"]
            elif kind == "decay_experiences":
                result = {"pruned": agent.engine.experiences.decay(
                    float(step.get("now", time.time())),
                    detail_after=float(step.get("detail_after", 86400.0)),
                )}
                agent.engine._persist()
            elif kind == "reinterpret_experience":
                experience_id = aliases.get(str(step.get("experience")), str(step.get("experience", "")))
                context_data = dict(step.get("context", {}))
                for key in ("supporting_world_event_ids", "contradicting_world_event_ids"):
                    context_data[key] = tuple(aliases.get(str(item), str(item)) for item in context_data.get(key, ()))
                context = ReconsolidationContext(**context_data)
                revised = agent.engine.reconsider_experience(experience_id, context)
                result = revised.to_dict() if revised else {
                    "deferred": True,
                    "reason": agent.engine.deferred_reinterpretations[-1].deferred_reason,
                }
            elif kind == "inspect_autobiographical":
                experience_id = aliases.get(str(step.get("experience")), str(step.get("experience", "")))
                experience = next(item for item in agent.engine.experiences.experiences if item.experience_id == experience_id)
                versions = agent.engine.autobiographical_interpretations.for_experience(experience_id)
                result = {
                    "version_count": len(versions),
                    "current_version": agent.engine.autobiographical_interpretations.current(experience_id).version,
                    "perceived_summary": experience.perceived_summary,
                    "interpretation": experience.interpretation,
                    "emotional_residue": experience.emotional_residue,
                    "recall_surface": experience.recall_surface(),
                    "deferred_count": len([item for item in agent.engine.deferred_reinterpretations if item.experience_id == experience_id]),
                }
            elif kind == "life_event":
                result = agent.force_life_event(str(step.get("category", "whim")))
            elif kind == "action_attempt":
                payload = dict(step.get("attempt", {}))
                payload["supporting_event_ids"] = tuple(aliases.get(str(item), str(item)) for item in payload.get("supporting_event_ids", ()))
                result = agent.attempt_imperfect_action(**payload)
                if step.get("as") and result.get("learned_artifact_id"):
                    aliases[str(step["as"])] = result["learned_artifact_id"]
            elif kind == "challenge_artifact":
                artifact_id = aliases.get(str(step.get("artifact")), str(step.get("artifact", "")))
                artifact = agent.engine.capability_artifacts.challenge(artifact_id, float(step.get("evidence_strength", 0.5)))
                agent.engine._persist()
                result = artifact.to_dict() if artifact else None
            elif kind == "idle":
                for _ in range(max(0, int(step.get("cycles", 1)))):
                    agent.idle()
                result = agent.engine.life_state.to_dict()
            elif kind == "recall":
                results = agent.engine.memory.retrieve_explained(str(step.get("query", "")), time.time(), top_k=int(step.get("top_k", 3)))
                result = [{"memory_id": item.memory.id, "content": item.memory.content, "reasons": item.reasons} for item in results]
            elif kind == "activity":
                result = agent.begin_activity(
                    str(step.get("activity", "quiet observation")),
                    str(step.get("intention", "continue current task")),
                    str(step.get("attention_target", "current task")),
                )
            elif kind == "pressure":
                agent.add_pressure(str(step.get("name", "strain")), float(step.get("magnitude", 0.5)))
                result = {"capacity": agent.engine.integration_capacity()}
            elif kind == "habit":
                result = agent.reinforce_habit(
                    str(step.get("name", "situated_habit")),
                    str(step.get("trigger", "default")),
                    str(step.get("response_pattern", "repeat the familiar action")),
                    int(step.get("repetitions", 1)),
                )
            elif kind == "pressure_decay":
                result = {"capacity": agent.decay_pressures_for_elapsed_time(int(step.get("dt_steps", 1)))}
            else:
                raise ValueError(f"unsupported life step: {kind}")
            expected = step.get("expect") or {}
            for key, value in expected.items():
                if _get_path(result, key) != value:
                    raise AssertionError(f"{key} expected {value!r}, got {_get_path(result, key)!r}")
            print(f"Life step {index} ({kind}): PASS")
        except (KeyError, TypeError, ValueError, AssertionError) as exc:
            failures += 1
            print(f"Life step {index} ({kind}): FAIL - {exc}")
    return failures


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--script", required=True)
    parser.add_argument("--cartridge", required=True)
    parser.add_argument("--db", default=None)
    args = parser.parse_args(argv)

    with open(args.script, "r", encoding="utf-8") as handle:
        script = yaml.safe_load(handle)
    db_path = args.db or os.path.join(tempfile.mkdtemp(), "sim_state.db")
    agent = CharacterAgent(cartridge_path=args.cartridge, user_id="sim_user", db_path=db_path)

    life_aliases: dict[str, str] = {}
    failures = _run_life_steps(agent, script.get("life_steps", []), life_aliases)
    leak_warnings = 0
    for idx, turn in enumerate(script.get("turns", []), start=1):
        user_input = turn["user_input"]
        result = agent.say(user_input, server_truth=turn.get("server_truth"), visible_context=turn.get("visible_context"))
        response = result["response"]
        ok = True
        reasons = []
        pattern = turn.get("expect_response_pattern")
        if pattern and not re.search(pattern, response, re.IGNORECASE):
            ok = False
            reasons.append(f"response did not match /{pattern}/: {response!r}")
        for key, expected in (turn.get("expect_state") or {}).items():
            actual = _get_path(result, key)
            if actual != expected:
                ok = False
                reasons.append(f"state {key} expected {expected!r}, got {actual!r}")
        monitor = result.get("self_monitor") or {}
        regulation_text = " | ".join(
            str(item.get("kind", "")) for item in monitor.get("regulation_candidates", ())
        )
        if turn.get("expect_regulation_pattern") and not re.search(
            turn["expect_regulation_pattern"], regulation_text, re.IGNORECASE,
        ):
            ok = False
            reasons.append(
                f"regulation candidates did not match /{turn['expect_regulation_pattern']}/: {regulation_text!r}"
            )
        if turn.get("expect_attributed_cause") and monitor.get("attributed_cause") != turn["expect_attributed_cause"]:
            ok = False
            reasons.append(
                f"attributed cause expected {turn['expect_attributed_cause']!r}, got {monitor.get('attributed_cause')!r}"
            )
        reject_response_pattern = turn.get("reject_response_pattern")
        if reject_response_pattern and re.search(reject_response_pattern, response, re.IGNORECASE):
            ok = False
            reasons.append(f"response matched rejected /{reject_response_pattern}/: {response!r}")
        beliefs = result.get("interpretive_belief_trace", []) or []
        min_beliefs = turn.get("expect_min_beliefs")
        if min_beliefs is not None and len(beliefs) < int(min_beliefs):
            ok = False
            reasons.append(f"expected at least {min_beliefs} interpretive beliefs, got {len(beliefs)}")
        if turn.get("require_belief_support", False):
            for belief in beliefs:
                if not belief.get("source_ids") or not belief.get("support_keys") or belief.get("canonical") is not False:
                    ok = False
                    reasons.append(f"belief lacks noncanonical source support: {belief!r}")
        belief_text = " | ".join(str(b.get("text", "")) for b in beliefs)
        belief_pattern = turn.get("expect_belief_pattern")
        if belief_pattern and not re.search(belief_pattern, belief_text, re.IGNORECASE):
            ok = False
            reasons.append(f"beliefs did not match /{belief_pattern}/: {belief_text!r}")
        reject_belief_pattern = turn.get("reject_belief_pattern")
        if reject_belief_pattern and re.search(reject_belief_pattern, belief_text, re.IGNORECASE):
            ok = False
            reasons.append(f"beliefs matched rejected /{reject_belief_pattern}/: {belief_text!r}")
        considered_text = " | ".join(
            f"{item.get('influence_id', '')} {item.get('label', '')}"
            for item in (result.get("synthesis", {}).get("considered_influences", []) or [])
        )
        inhibited_text = " | ".join(
            f"{item.get('influence_id', '')} {item.get('label', '')}"
            for item in (result.get("synthesis", {}).get("inhibited_influences", []) or [])
        )
        if turn.get("expect_considered_pattern") and not re.search(turn["expect_considered_pattern"], considered_text, re.IGNORECASE):
            ok = False
            reasons.append(f"considered influences did not match /{turn['expect_considered_pattern']}/: {considered_text!r}")
        if turn.get("expect_inhibited_pattern") and not re.search(turn["expect_inhibited_pattern"], inhibited_text, re.IGNORECASE):
            ok = False
            reasons.append(f"inhibited influences did not match /{turn['expect_inhibited_pattern']}/: {inhibited_text!r}")
        warnings = _fact_leak_warnings(response, turn, result, "response")
        for belief in beliefs:
            warnings.extend(_fact_leak_warnings(str(belief.get("text", "")), turn, result, "belief"))
        if warnings:
            leak_warnings += len(warnings)
            print(f"FACT LEAK WARNING turn {idx}: " + "; ".join(warnings))
        print(f"Turn {idx}: {'PASS' if ok else 'FAIL'}")
        if not ok:
            failures += 1
            print("  input:", user_input)
            for reason in reasons:
                print(" ", reason)
            print("  result:", result)
        failures += _run_life_steps(agent, turn.get("after_life_steps", []), life_aliases)
    failures += _run_life_steps(agent, script.get("life_steps_after", []), life_aliases)
    changed = agent.dream(min_interval_seconds=0)
    print("Dream changed:", changed)
    if script.get("fail_on_fact_leak", False) and leak_warnings:
        failures += 1
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
