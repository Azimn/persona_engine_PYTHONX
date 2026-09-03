from tools.compare_ensemble_reports import compare_reports
from tools.relationship_expression_probe import symptoms


def test_observed_parameter_language_is_measured_as_mechanistic():
    assert symptoms("I operate on established parameters, not spontaneous judgment.")["mechanistic_speech"]
    assert symptoms("I process information, not sentiment.")["mechanistic_speech"]
    assert not symptoms("I need more evidence before deciding.")["mechanistic_speech"]


def sample(
    history,
    prompt,
    seed,
    output,
    *,
    symptom=False,
    trace=None,
    candidate_authority=None,
    projection_match=None,
    validation_fallback=False,
    invalid_reason=None,
):
    status = {"actual_provider": "ollama"}
    if candidate_authority is not None:
        status["candidate_authority"] = candidate_authority
    row = {
        "history": history,
        "prompt": prompt,
        "seed": seed,
        "output": output,
        "symptoms": {"mechanistic_speech": symptom},
        "renderer_status": status,
        "expression_delivery": {"validation_fallback": validation_fallback},
    }
    if projection_match is not None:
        row["semantic_projection_matches_reference"] = projection_match
    if invalid_reason is not None:
        row["invalid_reason"] = invalid_reason
    if trace is not None:
        row["ensemble_trace"] = trace
    return row


def test_comparator_counts_surface_duplicates_and_matched_changes():
    single = {
        "schema": "single",
        "model": "qwen",
        "split": "dev",
        "samples": [
            sample("neutral", "p1", 1, "Same answer.", symptom=True),
            sample("neutral", "p2", 2, "Same answer.", symptom=False),
        ],
    }
    ensemble = {
        "schema": "ensemble",
        "model": "qwen",
        "split": "dev",
        "samples": [
            sample(
                "neutral", "p1", 1, "A different answer.", symptom=False,
                candidate_authority="engine_live", projection_match=True,
                trace={
                    "candidate_authority": "engine_live",
                    "selected_source": "model",
                    "selected_performance_mode": "contextual",
                    "prevalidation_rejections": [{"issue_codes": ["unsupported_private_user_state"]}],
                    "surviving_candidate_count": 2,
                    "requested_candidate_count": 3,
                    "agenda": {"initiative_allowed": True},
                },
            ),
            sample(
                "neutral", "p2", 2, "Another answer.", symptom=False,
                candidate_authority="engine_live", projection_match=True,
                trace={
                    "candidate_authority": "engine_live",
                    "selected_source": "authored",
                    "selected_performance_mode": None,
                    "prevalidation_rejections": [],
                    "surviving_candidate_count": 3,
                    "requested_candidate_count": 3,
                    "agenda": {"initiative_allowed": False},
                },
            ),
        ],
    }

    result = compare_reports(single, ensemble)
    assert result["single_shot"]["surface"]["exact_duplicate_count"] == 1
    assert result["ensemble"]["surface"]["exact_duplicate_count"] == 0
    assert result["matched"]["matched_sample_count"] == 2
    assert result["matched"]["changed_output_count"] == 2
    assert result["matched"]["symptom_improvements"]["mechanistic_speech"] == 1
    assert result["ensemble"]["ensemble"]["prevalidation_rejection_count"] == 1
    assert result["ensemble"]["ensemble"]["initiative_allowed_count"] == 1
    assert result["ensemble"]["ensemble"]["trace_candidate_authority_counts"] == {"engine_live": 2}
    assert result["ensemble"]["collection_integrity"]["candidate_authority_counts"] == {"engine_live": 2}
    assert result["ensemble"]["collection_integrity"]["semantic_projection_match_count"] == 2
    assert result["ensemble"]["collection_integrity"]["semantic_projection_mismatch_count"] == 0
    assert result["ensemble"]["collection_integrity"]["engine_validation_fallback_count"] == 0


def test_comparator_surfaces_collection_integrity_failures():
    ensemble = {
        "samples": [
            sample(
                "neutral", "p1", 1, "answer",
                candidate_authority="request_reconstruction",
                projection_match=False,
                validation_fallback=True,
                invalid_reason="semantic_projection_mismatch",
                trace={"candidate_authority": "request_reconstruction"},
            )
        ]
    }

    result = compare_reports({"samples": []}, ensemble)
    integrity = result["ensemble"]["collection_integrity"]

    assert integrity["candidate_authority_counts"] == {"request_reconstruction": 1}
    assert integrity["semantic_projection_checked_count"] == 1
    assert integrity["semantic_projection_mismatch_count"] == 1
    assert integrity["engine_validation_fallback_count"] == 1
    assert integrity["invalid_reason_counts"] == {"semantic_projection_mismatch": 1}


def test_comparator_reports_unmatched_samples_instead_of_silently_dropping_them():
    single = {"samples": [sample("a", "p", 1, "one")]}
    ensemble = {"samples": [sample("b", "p", 1, "two")]}
    result = compare_reports(single, ensemble)
    assert result["matched"]["matched_sample_count"] == 0
    assert result["matched"]["unmatched_single_count"] == 1
    assert result["matched"]["unmatched_ensemble_count"] == 1
