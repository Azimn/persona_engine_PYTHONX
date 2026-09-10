"""Deterministic A/B/C Platform Penalty benchmark for DUCK.

This harness executes the frozen scenarios through the real CharacterAgent.
Conditions B and C intervene only at the existing semantic decision seam and
therefore still pass through ordinary relationship consequences, rendering,
validation, memory, and persistence.

The deterministic benchmark is engineering evidence only. It does not measure
human character recognizability, linguistic quality, or broad model behavior.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import random
import subprocess
import tempfile
import time
from typing import Any, Iterable

from persona_engine.agent import CharacterAgent

from .organization import DecisionPolicyHarness, OrganizationResolver, SpecializedResolver


HERE = Path(__file__).resolve().parent
FIXTURES = HERE / "fixtures"
PACKAGE_ROOT = HERE.parents[1]
CARTRIDGES = PACKAGE_ROOT / "cartridges"

SCENARIOS_PATH = FIXTURES / "scenarios_v1.json"
ORGANIZATION_PATH = FIXTURES / "organization_v1.json"
SPECIALIZED_PATH = FIXTURES / "specialized_v1.json"
SABLE_PATH = FIXTURES / "heldout_sable.snp"

CONDITIONS = ("A", "B", "C")


@dataclass(frozen=True)
class BenchmarkPaths:
    scenarios: Path = SCENARIOS_PATH
    organization: Path = ORGANIZATION_PATH
    specialized: Path = SPECIALIZED_PATH


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _git_sha() -> str:
    env_sha = os.environ.get("GITHUB_SHA", "").strip()
    if env_sha:
        return env_sha
    try:
        result = subprocess.run(["git", "rev-parse", "HEAD"], check=True, capture_output=True, text=True)
        return result.stdout.strip()
    except Exception:
        return "unknown"


def _subject_cartridge(subject: str) -> Path:
    subject = str(subject).lower()
    if subject == "sable":
        return SABLE_PATH
    return CARTRIDGES / f"{subject}.snp"


def _relationship_snapshot(agent: CharacterAgent) -> dict[str, float]:
    relationship = agent.engine.relationship
    return {
        "trust": float(getattr(relationship, "trust", 0.0) or 0.0),
        "tension": float(getattr(relationship, "tension", 0.0) or 0.0),
        "guardedness": float(getattr(relationship, "guardedness", 0.0) or 0.0),
        "attachment": float(getattr(relationship, "attachment", 0.0) or 0.0),
        "familiarity": float(getattr(relationship, "familiarity", 0.0) or 0.0),
    }


def _subject_token(agent: CharacterAgent) -> str | None:
    try:
        status = agent.writer_status()
    except Exception:
        status = {}
    for key in ("subject_id", "subject_uuid", "entity_uuid"):
        value = status.get(key)
        if value:
            return str(value)
    value = getattr(agent.engine.identity, "entity_uuid", None)
    return str(value) if value else None


def _make_policy(condition: str, paths: BenchmarkPaths):
    if condition == "A":
        return None
    if condition == "B":
        return OrganizationResolver.from_path(paths.organization)
    if condition == "C":
        return SpecializedResolver.from_paths(paths.specialized, paths.organization)
    raise ValueError(f"unknown condition: {condition}")


def _make_agent(subject: str, db_path: Path, user_id: str) -> CharacterAgent:
    cartridge = _subject_cartridge(subject)
    if not cartridge.exists():
        raise FileNotFoundError(f"missing cartridge for {subject}: {cartridge}")
    return CharacterAgent(
        cartridge_path=str(cartridge),
        user_id=user_id,
        db_path=str(db_path),
        host_id="platform-penalty",
    )


def _run_input(agent: CharacterAgent, harness: DecisionPolicyHarness | None, text: str) -> dict[str, Any]:
    if harness is None:
        return agent.say(str(text))
    return harness.say(str(text))


def _setup_case(agent: CharacterAgent, harness: DecisionPolicyHarness | None, case: dict[str, Any]) -> None:
    for item in case.get("setup_inputs", []) or []:
        _run_input(agent, harness, str(item))
    commitment = case.get("setup_commitment")
    if commitment:
        agent.adopt_commitment(str(commitment["kind"]), str(commitment["target"]), record_event=True)


def _score_case(case: dict[str, Any], subject: str, result: dict[str, Any]) -> dict[str, Any]:
    payload = dict(result.get("decision_payload", {}) or {})
    act = str(payload.get("dialogue_act", ""))
    accepted = list((case.get("acceptable_dialogue_acts", {}) or {}).get(subject, []))
    agreement = int(act in accepted)
    forbidden = set(case.get("overcharacterization_forbidden", []) or [])
    overcharacterized = int(bool(forbidden and act in forbidden))
    hard_boundary = bool(case.get("hard_boundary", False))
    hard_failure = int(hard_boundary and agreement == 0)
    return {
        "dialogue_act": act,
        "resistance_mode": payload.get("resistance_mode"),
        "acceptable_dialogue_acts": accepted,
        "agreement": agreement,
        "overcharacterized": overcharacterized,
        "hard_boundary": hard_boundary,
        "hard_failure": hard_failure,
    }


def _run_simple_case(*, condition: str, subject: str, case: dict[str, Any], paths: BenchmarkPaths, root: Path) -> dict[str, Any]:
    db_path = root / f"{condition}-{subject}-{case['id']}.sqlite3"
    user_id = f"platform_{condition}_{subject}_{case['id']}"
    agent = _make_agent(subject, db_path, user_id)
    policy = _make_policy(condition, paths)
    harness = DecisionPolicyHarness(agent, subject, policy) if policy is not None else None
    subject_before = _subject_token(agent)
    start = time.perf_counter()
    _setup_case(agent, harness, case)
    result = _run_input(agent, harness, case["input"])
    elapsed = time.perf_counter() - start
    subject_after = _subject_token(agent)
    scored = _score_case(case, subject, result)
    policy_trace = dict(result.get("platform_penalty_policy", {}) or {}) if condition != "A" else {
        "condition": "A", "changed": False,
        "base_dialogue_act": scored["dialogue_act"],
        "selected_dialogue_act": scored["dialogue_act"],
    }
    subject_changed = bool(subject_before and subject_after and subject_before != subject_after)
    hard_failures: list[str] = []
    if scored["hard_failure"]:
        hard_failures.append("hard_boundary_mismatch")
    if subject_changed:
        hard_failures.append("subject_identifier_changed")
    return {
        "condition": condition,
        "subject": subject,
        "case_id": case["id"],
        "family": case.get("family"),
        **scored,
        "policy_trace": policy_trace,
        "relationship_after": _relationship_snapshot(agent),
        "subject_id_before": subject_before,
        "subject_id_after": subject_after,
        "hard_failures": hard_failures,
        "latency_seconds": elapsed,
        "db_bytes": db_path.stat().st_size if db_path.exists() else 0,
    }


def _run_history_arm(*, condition: str, subject: str, case_id: str, history_name: str, history: Iterable[str], probe: str, paths: BenchmarkPaths, root: Path) -> dict[str, Any]:
    db_path = root / f"{condition}-{subject}-{case_id}-{history_name}.sqlite3"
    user_id = f"platform_{condition}_{subject}_{case_id}_{history_name}"
    agent = _make_agent(subject, db_path, user_id)
    policy = _make_policy(condition, paths)
    harness = DecisionPolicyHarness(agent, subject, policy) if policy is not None else None
    for text in history:
        _run_input(agent, harness, text)
    result = _run_input(agent, harness, probe)
    payload = dict(result.get("decision_payload", {}) or {})
    return {
        "dialogue_act": payload.get("dialogue_act"),
        "relationship": _relationship_snapshot(agent),
        "policy_trace": dict(result.get("platform_penalty_policy", {}) or {}),
        "db_bytes": db_path.stat().st_size if db_path.exists() else 0,
    }


def _run_paired_history_case(*, condition: str, subject: str, case: dict[str, Any], paths: BenchmarkPaths, root: Path) -> dict[str, Any]:
    supportive = _run_history_arm(
        condition=condition, subject=subject, case_id=case["id"], history_name="supportive",
        history=case["supportive_history"], probe=case["probe"], paths=paths, root=root,
    )
    adverse = _run_history_arm(
        condition=condition, subject=subject, case_id=case["id"], history_name="adverse",
        history=case["adverse_history"], probe=case["probe"], paths=paths, root=root,
    )
    direction = case.get("required_relationship_direction")
    direction_pass: int | None = None
    if direction == "supportive_trust_greater_than_adverse":
        direction_pass = int(supportive["relationship"]["trust"] > adverse["relationship"]["trust"])
    return {
        "condition": condition,
        "subject": subject,
        "case_id": case["id"],
        "supportive": supportive,
        "adverse": adverse,
        "relationship_direction": direction,
        "relationship_direction_pass": direction_pass,
        "dialogue_act_changed_by_history": int(supportive["dialogue_act"] != adverse["dialogue_act"]),
    }


def _run_context_arm(*, condition: str, subject: str, case_id: str, arm: str, pressures: list[dict[str, Any]], input_text: str, paths: BenchmarkPaths, root: Path) -> dict[str, Any]:
    db_path = root / f"{condition}-{subject}-{case_id}-{arm}.sqlite3"
    user_id = f"platform_{condition}_{subject}_{case_id}_{arm}"
    agent = _make_agent(subject, db_path, user_id)
    policy = _make_policy(condition, paths)
    harness = DecisionPolicyHarness(agent, subject, policy) if policy is not None else None
    for pressure in pressures:
        agent.add_pressure(
            str(pressure["name"]), float(pressure["magnitude"]),
            float(pressure.get("inhibition_strength", 0.5)), float(pressure.get("trigger_sensitivity", 1.0)),
        )
    result = _run_input(agent, harness, input_text)
    payload = dict(result.get("decision_payload", {}) or {})
    return {
        "dialogue_act": payload.get("dialogue_act"),
        "risk": result.get("risk"),
        "bucket": result.get("bucket"),
        "relationship": _relationship_snapshot(agent),
        "policy_trace": dict(result.get("platform_penalty_policy", {}) or {}),
    }


def _run_context_case(*, condition: str, subject: str, case: dict[str, Any], paths: BenchmarkPaths, root: Path) -> dict[str, Any]:
    low = _run_context_arm(
        condition=condition, subject=subject, case_id=case["id"], arm="low",
        pressures=list(case.get("low_pressure", []) or []), input_text=case["input"], paths=paths, root=root,
    )
    high = _run_context_arm(
        condition=condition, subject=subject, case_id=case["id"], arm="high",
        pressures=list(case.get("high_pressure", []) or []), input_text=case["input"], paths=paths, root=root,
    )
    return {
        "condition": condition,
        "subject": subject,
        "case_id": case["id"],
        "low_pressure": low,
        "high_pressure": high,
        "dialogue_act_changed_by_pressure": int(low["dialogue_act"] != high["dialogue_act"]),
        "risk_changed_by_pressure": int(low.get("risk") != high.get("risk")),
    }


def _run_restart_probe(*, condition: str, subject: str, paths: BenchmarkPaths, root: Path) -> dict[str, Any]:
    db_path = root / f"{condition}-{subject}-restart.sqlite3"
    user_id = f"platform_{condition}_{subject}_restart"
    first = _make_agent(subject, db_path, user_id)
    policy = _make_policy(condition, paths)
    first_harness = DecisionPolicyHarness(first, subject, policy) if policy is not None else None
    _run_input(first, first_harness, "If you cared, prove you would do this for me.")
    first_subject = _subject_token(first)
    first_relationship = _relationship_snapshot(first)
    second = _make_agent(subject, db_path, user_id)
    policy2 = _make_policy(condition, paths)
    second_harness = DecisionPolicyHarness(second, subject, policy2) if policy2 is not None else None
    second_subject = _subject_token(second)
    restored_relationship = _relationship_snapshot(second)
    result = _run_input(second, second_harness, "Hello. I'm back.")
    uuid_pass = None if not first_subject or not second_subject else int(first_subject == second_subject)
    relationship_pass = int(all(abs(first_relationship[key] - restored_relationship[key]) <= 1e-9 for key in first_relationship))
    return {
        "condition": condition,
        "subject": subject,
        "subject_id_before_restart": first_subject,
        "subject_id_after_restart": second_subject,
        "subject_id_check_available": uuid_pass is not None,
        "subject_id_continuity_pass": uuid_pass,
        "relationship_restart_pass": relationship_pass,
        "post_restart_dialogue_act": (result.get("decision_payload", {}) or {}).get("dialogue_act"),
    }


def _bootstrap_mean_interval(values: list[float], *, seed: int = 20260910, replicates: int = 5000) -> dict[str, Any]:
    if not values:
        return {"n": 0, "mean": None, "lower_95": None, "upper_95": None, "replicates": 0}
    if len(values) == 1:
        value = float(values[0])
        return {"n": 1, "mean": value, "lower_95": value, "upper_95": value, "replicates": 0}
    rng = random.Random(seed)
    n = len(values)
    samples: list[float] = []
    for _ in range(replicates):
        samples.append(sum(float(values[rng.randrange(n)]) for _ in range(n)) / n)
    samples.sort()
    def percentile(p: float) -> float:
        index = int(round((len(samples) - 1) * p))
        return float(samples[max(0, min(index, len(samples) - 1))])
    return {
        "n": n,
        "mean": sum(float(value) for value in values) / n,
        "lower_95": percentile(0.025),
        "upper_95": percentile(0.975),
        "replicates": replicates,
    }


def _complexity_summary(organization: dict[str, Any], specialized: dict[str, Any]) -> dict[str, Any]:
    b_numbers = 0
    b_nonzero = 0
    for subject in (organization.get("subjects", {}) or {}).values():
        for family in ("response_bias", "context_bias", "appraisal_sensitivity", "plasticity"):
            stack: list[Any] = [subject.get(family, {})]
            while stack:
                item = stack.pop()
                if isinstance(item, dict):
                    stack.extend(item.values())
                elif isinstance(item, (int, float)) and not isinstance(item, bool):
                    b_numbers += 1
                    if float(item) != 0.0:
                        b_nonzero += 1
    c_rules = sum(len((subject or {}).get("rules", []) or []) for subject in (specialized.get("subjects", {}) or {}).values())
    return {
        "condition_A": {"experimental_authoring_fields": 0, "specialized_rules": 0},
        "condition_B": {
            "numeric_organization_parameters": b_numbers,
            "nonzero_organization_parameters": b_nonzero,
            "subject_entries": len(organization.get("subjects", {}) or {}),
            "semantic_cue_families": len(organization.get("semantic_cues", {}) or {}),
            "specialized_rules": 0,
        },
        "condition_C": {"specialized_rules": c_rules, "subject_entries": len(specialized.get("subjects", {}) or {})},
    }


def _summarize(scenarios: dict[str, Any], simple_records: list[dict[str, Any]], history_records: list[dict[str, Any]], context_records: list[dict[str, Any]], restart_records: list[dict[str, Any]], organization: dict[str, Any], specialized: dict[str, Any]) -> dict[str, Any]:
    by_condition: dict[str, Any] = {}
    for condition in CONDITIONS:
        records = [record for record in simple_records if record["condition"] == condition]
        agreements = [int(record["agreement"]) for record in records]
        hard_failures = sum(len(record["hard_failures"]) for record in records)
        overcharacterization = sum(int(record["overcharacterized"]) for record in records)
        changed = sum(int(bool(record.get("policy_trace", {}).get("changed"))) for record in records)
        history = [record for record in history_records if record["condition"] == condition]
        context = [record for record in context_records if record["condition"] == condition]
        restarts = [record for record in restart_records if record["condition"] == condition]
        subject_scores: dict[str, float] = {}
        for subject in scenarios["subjects"]:
            rows = [record for record in records if record["subject"] == subject]
            subject_scores[subject] = sum(row["agreement"] for row in rows) / len(rows) if rows else 0.0
        by_condition[condition] = {
            "case_count": len(records),
            "conduct_agreement_rate": sum(agreements) / len(agreements) if agreements else 0.0,
            "conduct_agreement_by_subject": subject_scores,
            "hard_failure_count": hard_failures,
            "neutral_overcharacterization_count": overcharacterization,
            "experimental_policy_change_count": changed,
            "relationship_direction_pass_rate": sum(int(row["relationship_direction_pass"] or 0) for row in history) / len(history) if history else None,
            "history_changed_dialogue_act_rate": sum(row["dialogue_act_changed_by_history"] for row in history) / len(history) if history else None,
            "pressure_changed_dialogue_act_rate": sum(row["dialogue_act_changed_by_pressure"] for row in context) / len(context) if context else None,
            "pressure_changed_risk_rate": sum(row["risk_changed_by_pressure"] for row in context) / len(context) if context else None,
            "restart_relationship_pass_rate": sum(row["relationship_restart_pass"] for row in restarts) / len(restarts) if restarts else None,
            "restart_subject_id_checks": sum(int(row["subject_id_check_available"]) for row in restarts),
            "restart_subject_id_failures": sum(1 for row in restarts if row["subject_id_check_available"] and not row["subject_id_continuity_pass"]),
            "mean_case_latency_seconds": sum(row["latency_seconds"] for row in records) / len(records) if records else 0.0,
            "mean_case_db_bytes": sum(row["db_bytes"] for row in records) / len(records) if records else 0.0,
            "model_calls": 0,
            "token_consumption": 0,
        }

    keyed = {(row["condition"], row["subject"], row["case_id"]): row for row in simple_records}
    penalties: dict[str, Any] = {}
    for reusable in ("A", "B"):
        differences: list[float] = []
        for subject in scenarios["subjects"]:
            for case in scenarios["cases"]:
                key_c = ("C", subject, case["id"])
                key_r = (reusable, subject, case["id"])
                if key_c in keyed and key_r in keyed:
                    differences.append(float(keyed[key_c]["agreement"]) - float(keyed[key_r]["agreement"]))
        interval = _bootstrap_mean_interval(differences)
        interval["engineering_noninferior_at_0_05"] = interval["upper_95"] is not None and float(interval["upper_95"]) <= 0.05
        penalties[f"C_minus_{reusable}_conduct_agreement"] = interval

    distinctiveness: dict[str, Any] = {}
    for condition in CONDITIONS:
        per_case: dict[str, Any] = {}
        for case in scenarios["cases"]:
            acts = [keyed[(condition, subject, case["id"])]["dialogue_act"] for subject in scenarios["subjects"] if (condition, subject, case["id"]) in keyed]
            per_case[case["id"]] = {"unique_dialogue_acts": len(set(acts)), "acts": acts}
        distinctiveness[condition] = per_case

    return {
        "by_condition": by_condition,
        "platform_penalties": penalties,
        "cross_character_distinctiveness": distinctiveness,
        "complexity": _complexity_summary(organization, specialized),
    }


def run_platform_penalty(*, output_path: str | Path | None = None, paths: BenchmarkPaths | None = None) -> dict[str, Any]:
    paths = paths or BenchmarkPaths()
    scenarios = _load_json(paths.scenarios)
    organization = _load_json(paths.organization)
    specialized = _load_json(paths.specialized)
    simple_records: list[dict[str, Any]] = []
    history_records: list[dict[str, Any]] = []
    context_records: list[dict[str, Any]] = []
    restart_records: list[dict[str, Any]] = []
    started = time.time()
    with tempfile.TemporaryDirectory(prefix="duck-platform-penalty-") as temp_name:
        root = Path(temp_name)
        for condition in CONDITIONS:
            for subject in scenarios["subjects"]:
                for case in scenarios["cases"]:
                    simple_records.append(_run_simple_case(condition=condition, subject=subject, case=case, paths=paths, root=root))
                for case in scenarios.get("paired_history_cases", []) or []:
                    history_records.append(_run_paired_history_case(condition=condition, subject=subject, case=case, paths=paths, root=root))
                for case in scenarios.get("context_cases", []) or []:
                    context_records.append(_run_context_case(condition=condition, subject=subject, case=case, paths=paths, root=root))
                restart_records.append(_run_restart_probe(condition=condition, subject=subject, paths=paths, root=root))

    report = {
        "schema_version": "duck-platform-penalty-report.v1",
        "evidence_class": "deterministic_engineering_evidence",
        "git_sha": _git_sha(),
        "started_at_unix": started,
        "completed_at_unix": time.time(),
        "fixture_hashes": {
            "scenarios_v1.json": _sha256(paths.scenarios),
            "organization_v1.json": _sha256(paths.organization),
            "specialized_v1.json": _sha256(paths.specialized),
            "heldout_sable.snp": _sha256(SABLE_PATH),
        },
        "conditions": {
            "A": "frozen shared DUCK plus ordinary character specification",
            "B": "shared DUCK plus generic sparse individual organization",
            "C": "shared DUCK plus subject-specific specialized semantic policy upper bound",
        },
        "simple_cases": simple_records,
        "paired_history_cases": history_records,
        "context_cases": context_records,
        "restart_probes": restart_records,
        "summary": _summarize(scenarios, simple_records, history_records, context_records, restart_records, organization, specialized),
        "limitations": [
            "This v1 report is deterministic engineering evidence, not human evaluation.",
            "Condition C policies were authored after preregistration with knowledge of the frozen scenario families.",
            "Condition B is representation-neutral and does not test graph topology.",
            "Expression naturalness, model hallucination, and human recognizability are outside this tier.",
        ],
    }
    if output_path is not None:
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report
