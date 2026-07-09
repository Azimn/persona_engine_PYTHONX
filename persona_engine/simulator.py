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
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import yaml

from persona_engine.agent import CharacterAgent

_CONCRETE_OBJECTS = {"door", "car", "phone", "window", "person", "someone", "outside", "footsteps"}
_SAFE_INTERPRETIVE_TERMS = {
    "a", "an", "and", "as", "be", "can", "character", "cause", "certainty", "challenge",
    "caution", "closeness", "continuity", "distance", "evidence", "for", "integrity",
    "is", "long", "may", "not", "or", "phrase", "possible", "precision", "pressure",
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
    # Capitalized proper noun style leak, excluding first word of sentence by allowing common character names from prompt.
    warnings = []
    for token in re.findall(r"\b[A-Z][a-zA-Z0-9_'-]{2,}\b", text):
        if token.lower() not in allowed and token.lower() not in {"the", "and", "but"}:
            warnings.append(f"{label} proper noun/object not in visible frame: {token}")
    for obj in _CONCRETE_OBJECTS:
        if re.search(rf"\b{re.escape(obj)}\b", text.lower()) and obj not in allowed:
            warnings.append(f"{label} concrete object not in visible frame: {obj}")
    return warnings


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

    failures = 0
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
    changed = agent.dream(min_interval_seconds=0)
    print("Dream changed:", changed)
    if script.get("fail_on_fact_leak", False) and leak_warnings:
        failures += 1
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
