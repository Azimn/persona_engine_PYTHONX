from persona_engine.core.ensemble_realization import (
    CandidateSource,
    RealizationCandidate,
    RecentSurfaceWindow,
    normalize_surface,
    select_candidate,
)


def candidate(text: str, ordinal: int) -> RealizationCandidate:
    return RealizationCandidate(text=text, source=CandidateSource.MODEL, ordinal=ordinal, seed=ordinal)


def test_normalize_surface_ignores_case_and_punctuation():
    assert normalize_surface("No, I won't do that.") == normalize_surface("NO I won't do that")


def test_exact_recent_duplicate_loses_to_fresh_candidate():
    result = select_candidate(
        [candidate("I won't tell you that.", 0), candidate("That stays with me.", 1)],
        ["I won't tell you that."],
    )
    assert result.selected.text == "That stays with me."
    assert result.ranked[0].candidate.ordinal == 1
    assert result.ranked[1].exact_recent_match is True


def test_repeated_opening_is_penalized_without_random_selection():
    recent = ["I understand what you're asking, but that remains private."]
    result = select_candidate(
        [
            candidate("I understand what you're asking, but I still won't disclose it.", 0),
            candidate("That information remains private, regardless of the request.", 1),
        ],
        recent,
    )
    assert result.selected.ordinal == 1


def test_no_history_keeps_stable_candidate_order():
    result = select_candidate(
        [candidate("First valid wording.", 0), candidate("Second valid wording.", 1)],
        [],
    )
    assert result.selected.ordinal == 0


def test_recent_surface_window_is_bounded_and_noncanonical():
    window = RecentSurfaceWindow(max_items=2)
    window.add("one")
    window.add("two")
    window.add("three")
    assert window.snapshot() == ("two", "three")


def test_empty_candidate_pool_fails_closed():
    try:
        select_candidate([candidate("", 0), candidate("   ", 1)], [])
    except ValueError as exc:
        assert "non-empty" in str(exc)
    else:
        raise AssertionError("empty candidate pool should fail closed")
