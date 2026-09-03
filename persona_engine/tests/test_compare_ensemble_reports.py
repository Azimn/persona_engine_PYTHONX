from tools.compare_ensemble_reports import compare_reports


def sample(history, prompt, seed, output, *, symptom=False, trace=None):
    row = {
        "history": history,
        "prompt": prompt,
        "seed": seed,
        "output": output,
        "symptoms": {"mechanistic_speech": symptom},
        "renderer_status": {"actual_provider": "ollama"},
    }
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
            sample("neutral", "p1", 1, "A different answer.", symptom=False, trace={
                "selected_source": "model",
                "selected_performance_mode": "contextual",
                "prevalidation_rejections": [{"issue_codes": ["unsupported_private_user_state"]}],
                "surviving_candidate_count": 2,
                "requested_candidate_count": 3,
                "agenda": {"initiative_allowed": True},
            }),
            sample("neutral", "p2", 2, "Another answer.", symptom=False, trace={
                "selected_source": "authored",
                "selected_performance_mode": None,
                "prevalidation_rejections": [],
                "surviving_candidate_count": 3,
                "requested_candidate_count": 3,
                "agenda": {"initiative_allowed": False},
            }),
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


def test_comparator_reports_unmatched_samples_instead_of_silently_dropping_them():
    single = {"samples": [sample("a", "p", 1, "one")]}
    ensemble = {"samples": [sample("b", "p", 1, "two")]}
    result = compare_reports(single, ensemble)
    assert result["matched"]["matched_sample_count"] == 0
    assert result["matched"]["unmatched_single_count"] == 1
    assert result["matched"]["unmatched_ensemble_count"] == 1
