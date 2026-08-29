"""Contracts for the early Study-A character-kernel ablation harness."""

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "tools" / "mvi_character_baseline.py"


def _load_tool():
    spec = importlib.util.spec_from_file_location("wayfarer_mvi_character_baseline", TOOL)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def test_early_mvi_study_has_fixed_renderer_and_all_declared_conditions():
    tool = _load_tool()
    study = tool.run_study()
    assert study["renderer_control"] == "deterministic offline renderer"
    assert set(study["conditions"]) == set(tool.CONDITIONS)
    assert len(study["conditions"]["full"]["turns"]) == 10
    assert len(study["conditions"]["full"]["time_advances"]) == 2


def test_clean_ablation_seams_remove_the_mechanism_they_claim_to_remove():
    tool = _load_tool()
    study = tool.run_study()
    conditions = study["conditions"]
    assert conditions["memory_retrieval_off"]["totals"]["retrieved_memories"] == 0
    assert conditions["interpretation_off"]["totals"]["interpretive_beliefs"] == 0
    assert conditions["symbols_off"]["final"]["symbol_count"] == 0
    assert conditions["habits_off"]["final"]["habit_count"] == 0


def test_mvi_report_does_not_reduce_results_to_a_single_lifelikeness_score():
    tool = _load_tool()
    study = tool.run_study()
    markdown = tool.to_markdown(study).lower()
    assert "lifelikeness score" not in markdown
    assert "zero difference" in markdown
    assert all("semantic_digest_equal" in row for row in study["comparisons"])
