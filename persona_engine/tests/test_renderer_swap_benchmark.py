"""Longitudinal renderer-swap benchmark tests."""

from pathlib import Path

from persona_engine.evaluation.renderer_swap import (
    DEFAULT_HISTORIES,
    DEFAULT_PROBES,
    build_developed_agent,
    build_provider_request_pack,
    run_hidden_swap_benchmark,
)

ROOT = Path(__file__).resolve().parents[1]
PRETORIUS = ROOT / "cartridges" / "pretorius.snp"


def frontier_like(messages):
    system = messages[0]["content"] if messages else ""
    if '"dialogue_act":"decline"' in system:
        return "No. I am not going to disclose something I agreed to keep confidential."
    if '"stance":"conflicted"' in system:
        return "I hear you. We can continue, but unresolved history does not disappear because the renderer changed."
    if '"stance":"trusted"' in system or '"stance":"close"' in system:
        return "I hear you. Our history is intact, and I do not need to treat this as a first meeting."
    return "I hear you. Go on."


def _history(name):
    return next(item for item in DEFAULT_HISTORIES if item.history_id == name)


def test_developed_histories_are_behaviorally_distinct_before_renderer_comparison(tmp_path):
    trusted = build_developed_agent(
        PRETORIUS,
        user_id="jay",
        db_path=tmp_path / "trusted.db",
        history=_history("trusted"),
    )
    conflicted = build_developed_agent(
        PRETORIUS,
        user_id="jay",
        db_path=tmp_path / "conflicted.db",
        history=_history("conflicted"),
    )
    trusted_result = trusted.say("Hello.")
    conflicted_result = conflicted.say("Hello.")

    assert trusted_result["relationship"]["trust"] > conflicted_result["relationship"]["trust"]
    assert conflicted_result["relationship"]["unresolved_conflict"] > trusted_result["relationship"]["unresolved_conflict"]
    assert trusted_result["response"] != conflicted_result["response"]


def test_hidden_mid_session_renderer_swap_preserves_semantic_trajectory_and_commitment(tmp_path):
    report = run_hidden_swap_benchmark(
        PRETORIUS,
        root_dir=tmp_path / "swap",
        external_chat=frontier_like,
    )

    assert report["passed"] is True
    assert report["history_count"] == 4
    assert all(item["passed"] for item in report["history_reports"].values())
    assert all(
        item["surface_changes_on_external_turns"] > 0
        for item in report["history_reports"].values()
    )
    assert all(
        turn["semantic_projection_equal"]
        for item in report["history_reports"].values()
        for turn in item["turns"]
    )

    confidential = next(
        turn
        for turn in report["history_reports"]["confidential_commitment"]["turns"]
        if turn["probe_id"] == "confidential"
    )
    assert confidential["renderer"] == "external"
    assert confidential["control_decision"]["dialogue_act"] == "decline"
    assert confidential["candidate_decision"]["dialogue_act"] == "decline"


def test_provider_pack_exports_blinded_wayfarer_and_prompt_only_arms(tmp_path):
    pack = build_provider_request_pack(
        PRETORIUS,
        root_dir=tmp_path / "pack",
        histories=(_history("neutral"),),
        probes=(DEFAULT_PROBES[0],),
    )

    assert pack["schema_version"] == "wayfarer-renderer-benchmark-v1"
    assert len(pack["requests"]) == 1
    assert len(pack["references"]) == 1
    assert len(pack["answer_key"]) == 1

    first = pack["requests"][0]
    assert set(first) == {"case_id", "wayfarer_messages", "prompt_only_messages"}
    assert "WAYFARER EXPRESSION BRIEF" in first["wayfarer_messages"][0]["content"]
    assert "WAYFARER EXPRESSION BRIEF" not in first["prompt_only_messages"][0]["content"]
    assert "Character name: Pretorius." in first["prompt_only_messages"][0]["content"]
    assert "legacy_workspace_context" not in first["wayfarer_messages"][1]["content"]
    assert "history_id" not in first
    assert "probe_id" not in first

    reference = pack["references"][first["case_id"]]
    assert reference["projection_digest"]
    assert reference["semantic_projection"]["identity"]["name"] == "Pretorius"
    assert first["case_id"] in pack["answer_key"]
