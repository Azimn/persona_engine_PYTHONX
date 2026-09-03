"""Compare matched single-shot and Ensemble actual-model reports.

This scorer intentionally focuses on measurements available in the frozen report
artifacts themselves. It does not pretend that surface diversity proves
character fidelity. Semantic/behavioral correctness remains a separate contract
and human recognition remains a separate evaluation layer.
"""

from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
import re
from statistics import mean


SCHEMA = "ensemble-report-comparison-v1"
_WORD_RE = re.compile(r"[a-z0-9']+")


def normalize(text: str) -> str:
    return " ".join(_WORD_RE.findall(str(text or "").lower()))


def opening(text: str, words: int = 5) -> str:
    return " ".join(normalize(text).split()[:words])


def _duplicate_metrics(values: list[str]) -> dict:
    exact_counts = Counter(str(value or "").strip() for value in values if str(value or "").strip())
    normalized_counts = Counter(normalize(value) for value in values if normalize(value))
    exact_duplicates = sum(count - 1 for count in exact_counts.values() if count > 1)
    normalized_duplicates = sum(count - 1 for count in normalized_counts.values() if count > 1)

    seen_openings: set[str] = set()
    repeated_openings = 0
    for value in values:
        key = opening(value)
        if not key:
            continue
        if key in seen_openings:
            repeated_openings += 1
        seen_openings.add(key)

    denominator = max(1, len(values))
    return {
        "sample_count": len(values),
        "unique_exact_outputs": len(exact_counts),
        "unique_normalized_outputs": len(normalized_counts),
        "exact_duplicate_count": exact_duplicates,
        "exact_duplicate_rate": round(exact_duplicates / denominator, 6),
        "normalized_duplicate_count": normalized_duplicates,
        "normalized_duplicate_rate": round(normalized_duplicates / denominator, 6),
        "repeated_opening_count": repeated_openings,
        "repeated_opening_rate": round(repeated_openings / denominator, 6),
        "mean_output_characters": round(mean([len(str(value or "")) for value in values]) if values else 0.0, 3),
    }


def _symptom_counts(samples: list[dict]) -> dict:
    keys: set[str] = set()
    for sample in samples:
        symptoms = sample.get("symptoms", {})
        if isinstance(symptoms, dict):
            keys.update(str(key) for key in symptoms)
    return {
        key: sum(bool((sample.get("symptoms") or {}).get(key)) for sample in samples)
        for key in sorted(keys)
    }


def report_metrics(report: dict) -> dict:
    samples = list(report.get("samples", []))
    outputs = [str(sample.get("output", "")) for sample in samples]
    provider_counts = Counter(
        str((sample.get("renderer_status") or {}).get("actual_provider", "unknown"))
        for sample in samples
    )
    result = {
        "schema": report.get("schema"),
        "status": report.get("status"),
        "model": report.get("model"),
        "split": report.get("split"),
        "surface": _duplicate_metrics(outputs),
        "symptoms": _symptom_counts(samples),
        "provider_counts": dict(provider_counts),
    }

    traces = [sample.get("ensemble_trace") for sample in samples if isinstance(sample.get("ensemble_trace"), dict)]
    if traces:
        result["ensemble"] = {
            "selected_source_counts": dict(Counter(str(trace.get("selected_source", "unknown")) for trace in traces)),
            "selected_performance_mode_counts": dict(Counter(str(trace.get("selected_performance_mode", "none")) for trace in traces)),
            "prevalidation_rejection_count": sum(len(trace.get("prevalidation_rejections", [])) for trace in traces),
            "mean_surviving_candidates": round(mean([
                float(trace.get("surviving_candidate_count", 0) or 0) for trace in traces
            ]), 3),
            "mean_requested_model_candidates": round(mean([
                float(trace.get("requested_candidate_count", 0) or 0) for trace in traces
            ]), 3),
            "initiative_allowed_count": sum(bool((trace.get("agenda") or {}).get("initiative_allowed")) for trace in traces),
        }
    return result


def _sample_key(sample: dict) -> tuple:
    return (
        str(sample.get("history", "")),
        str(sample.get("prompt", "")),
        int(sample.get("seed", 0) or 0),
    )


def matched_comparison(single: dict, ensemble: dict) -> dict:
    single_samples = {_sample_key(sample): sample for sample in single.get("samples", [])}
    ensemble_samples = {_sample_key(sample): sample for sample in ensemble.get("samples", [])}
    keys = sorted(set(single_samples) & set(ensemble_samples))

    changed = 0
    improved_symptoms = Counter()
    worsened_symptoms = Counter()
    for key in keys:
        left = single_samples[key]
        right = ensemble_samples[key]
        if str(left.get("output", "")) != str(right.get("output", "")):
            changed += 1
        symptom_keys = set((left.get("symptoms") or {})) | set((right.get("symptoms") or {}))
        for symptom in symptom_keys:
            before = bool((left.get("symptoms") or {}).get(symptom))
            after = bool((right.get("symptoms") or {}).get(symptom))
            if before and not after:
                improved_symptoms[symptom] += 1
            elif after and not before:
                worsened_symptoms[symptom] += 1

    denominator = max(1, len(keys))
    return {
        "matched_sample_count": len(keys),
        "changed_output_count": changed,
        "changed_output_rate": round(changed / denominator, 6),
        "symptom_improvements": dict(improved_symptoms),
        "symptom_regressions": dict(worsened_symptoms),
        "unmatched_single_count": len(single_samples) - len(keys),
        "unmatched_ensemble_count": len(ensemble_samples) - len(keys),
    }


def compare_reports(single: dict, ensemble: dict) -> dict:
    return {
        "schema": SCHEMA,
        "single_shot": report_metrics(single),
        "ensemble": report_metrics(ensemble),
        "matched": matched_comparison(single, ensemble),
        "interpretation": (
            "Surface and narrow symptom metrics only. A lower duplicate rate is not evidence of preserved identity by itself; "
            "pair these results with decision, recall, commitment, provenance and human-recognition evaluation."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--single", type=Path, required=True, help="Single-shot relationship probe report.json")
    parser.add_argument("--ensemble", type=Path, required=True, help="Ensemble relationship probe report.json")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    result = compare_reports(
        json.loads(args.single.read_text(encoding="utf-8")),
        json.loads(args.ensemble.read_text(encoding="utf-8")),
    )
    text = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
