"""Executable expression-substrate continuity and offline-quality probe."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

from persona_engine.agent import CharacterAgent
from persona_engine.core.external_renderer import ExternalChatRenderer
from persona_engine.core.renderer import LocalLLMRenderer

ROOT = Path(__file__).resolve().parents[1]
CART = ROOT / "persona_engine" / "cartridges" / "pretorius.snp"


def projection(agent, result):
    return {
        "identity": agent.engine.identity.name,
        "beliefs": dict(agent.engine.belief_ledger.values),
        "relationship": dict(result["relationship"]),
        "decision_payload": dict(result["decision_payload"]),
        "interpretive_beliefs": list(result["interpretive_belief_trace"]),
    }


def build_history(db_path: str, inputs: list[str]):
    agent = CharacterAgent(cartridge_path=str(CART), user_id="jay", db_path=db_path)
    agent.engine.set_renderer(LocalLLMRenderer(model_name="missing-model-for-mock", provider="offline"))
    for text in inputs:
        agent.say(text)
    return agent


def main() -> int:
    with tempfile.TemporaryDirectory() as d:
        conflict_inputs = ["You lied to me and betrayed me. This is your fault."] * 5
        trust_inputs = ["Thank you. I appreciate that you helped me."] * 5
        conflicted = build_history(os.path.join(d, "conflict.db"), conflict_inputs)
        trusted = build_history(os.path.join(d, "trusted.db"), trust_inputs)
        conflicted_reply = conflicted.say("Hello.")["response"]
        trusted_reply = trusted.say("Hello.")["response"]

        # Two identical histories, different expression substrates.
        common_inputs = ["Thank you. I appreciate that you helped me."] * 5
        offline = build_history(os.path.join(d, "offline.db"), common_inputs)
        external = build_history(os.path.join(d, "external.db"), common_inputs)
        captured = {}

        def frontier_like(messages):
            captured["messages"] = messages
            return "I hear you, Jay. I can receive that without treating it as empty politeness."

        external.engine.set_renderer(ExternalChatRenderer(
            frontier_like, provider_name="frontier-like-test", model_name="frontier-like-test-model"
        ))
        offline_result = offline.say("I care about you.")
        external_result = external.say("I care about you.")
        system_text = captured["messages"][0]["content"]

        report = {
            "probe": "expression-substrate-continuity-v1",
            "passed": all([
                conflicted_reply != trusted_reply,
                "unresolved" in conflicted_reply.lower() or "repair" in conflicted_reply.lower(),
                "thread" in trusted_reply.lower() or "starting over" in trusted_reply.lower(),
                projection(offline, offline_result) == projection(external, external_result),
                "wayfarer-expression-brief-v1" in system_text,
                '"dialogue_act":"respond"' in system_text,
                '"stance":"trusted"' in system_text,
            ]),
            "conflicted_relationship": {
                "trust": conflicted.engine.relationship.trust,
                "tension": conflicted.engine.relationship.tension,
                "guardedness": conflicted.engine.relationship.guardedness,
                "unresolved_conflict": conflicted.engine.relationship.unresolved_conflict,
                "response": conflicted_reply,
            },
            "trusted_relationship": {
                "trust": trusted.engine.relationship.trust,
                "tension": trusted.engine.relationship.tension,
                "guardedness": trusted.engine.relationship.guardedness,
                "unresolved_conflict": trusted.engine.relationship.unresolved_conflict,
                "response": trusted_reply,
            },
            "same_moment_semantic_projection_equal": projection(offline, offline_result) == projection(external, external_result),
            "offline_response": offline_result["response"],
            "external_response": external_result["response"],
            "external_brief_schema_present": "wayfarer-expression-brief-v1" in system_text,
            "external_explicit_decision_present": '"dialogue_act":"respond"' in system_text,
            "external_relationship_stance_present": '"stance":"trusted"' in system_text,
            "external_renderer_status": external.engine.renderer_status(),
        }
        print(json.dumps(report, indent=2, sort_keys=True))
        return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
