"""Noncanonical candidate-expression ecology for Project Ensemble.

The subject core has already resolved the character moment before this module is
used. Candidates are alternative *performances* of that same moment. This
module owns no identity, memory, relationship, commitment, belief, goal, or
world-truth authority.

V1 deliberately solves one demonstrated failure class: pathological surface
repetition. It does not invent a second planner or semantic judge. Higher
layer consistency validation remains authoritative over whether the selected
candidate faithfully realizes the already-resolved decision.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from difflib import SequenceMatcher
from enum import Enum
import re
from typing import Any, Iterable, Sequence


class CandidateSource(str, Enum):
    """Where one proposed realization came from."""

    MODEL = "model"
    OFFLINE = "offline"
    AUTHORED = "authored"
    RETRIEVAL = "retrieval"


@dataclass(frozen=True)
class RealizationCandidate:
    """One noncanonical way to express an already-resolved character moment."""

    text: str
    source: CandidateSource = CandidateSource.MODEL
    ordinal: int = 0
    seed: int | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class CandidateScore:
    """Deterministic surface-diversity diagnostics for one candidate."""

    candidate: RealizationCandidate
    score: float
    exact_recent_match: bool
    normalized_recent_match: bool
    max_recent_similarity: float
    repeated_opening: bool
    repeated_phrase: bool


@dataclass(frozen=True)
class SelectionResult:
    selected: RealizationCandidate
    ranked: tuple[CandidateScore, ...]
    rejected_empty: int = 0


_WORD_RE = re.compile(r"[a-z0-9']+")


def normalize_surface(text: str) -> str:
    """Normalize only for repetition comparison, never for user-visible output."""

    return " ".join(_WORD_RE.findall(str(text).lower()))


def _opening(text: str, words: int = 5) -> tuple[str, ...]:
    tokens = normalize_surface(text).split()
    return tuple(tokens[:words]) if len(tokens) >= words else tuple(tokens)


def _ngrams(text: str, size: int = 5) -> set[tuple[str, ...]]:
    tokens = normalize_surface(text).split()
    if len(tokens) < size:
        return set()
    return {tuple(tokens[index:index + size]) for index in range(len(tokens) - size + 1)}


def _surface_similarity(left: str, right: str) -> float:
    a = normalize_surface(left)
    b = normalize_surface(right)
    if not a or not b:
        return 0.0
    return SequenceMatcher(a=a, b=b).ratio()


def score_candidate(candidate: RealizationCandidate, recent_outputs: Sequence[str]) -> CandidateScore:
    """Score surface novelty without deciding what the character should mean.

    Penalties intentionally dominate tiny ordinal tie-breaking. This prevents
    the selector from becoming stochastic while still preferring a fresh
    realization when several semantically equivalent candidates are available.
    """

    text = str(candidate.text or "").strip()
    normalized = normalize_surface(text)
    exact = any(text == str(previous).strip() for previous in recent_outputs if str(previous).strip())
    normalized_match = bool(normalized) and any(
        normalized == normalize_surface(previous) for previous in recent_outputs if str(previous).strip()
    )
    similarities = [_surface_similarity(text, previous) for previous in recent_outputs if str(previous).strip()]
    max_similarity = max(similarities, default=0.0)

    opening = _opening(text)
    repeated_opening = bool(opening) and any(opening == _opening(previous) for previous in recent_outputs)
    phrases = _ngrams(text)
    repeated_phrase = bool(phrases) and any(bool(phrases & _ngrams(previous)) for previous in recent_outputs)

    score = 100.0
    if exact:
        score -= 100.0
    elif normalized_match:
        score -= 80.0
    score -= 35.0 * max_similarity
    if repeated_opening:
        score -= 12.0
    if repeated_phrase:
        score -= 8.0
    # Stable deterministic tie-break: earlier candidate wins by a tiny amount.
    score -= max(0, int(candidate.ordinal)) * 0.0001

    return CandidateScore(
        candidate=candidate,
        score=round(score, 6),
        exact_recent_match=exact,
        normalized_recent_match=normalized_match,
        max_recent_similarity=round(max_similarity, 6),
        repeated_opening=repeated_opening,
        repeated_phrase=repeated_phrase,
    )


def select_candidate(
    candidates: Iterable[RealizationCandidate],
    recent_outputs: Sequence[str] = (),
) -> SelectionResult:
    """Select the least pathologically repetitive non-empty realization.

    The function assumes every candidate expresses the same higher-authority
    decision. It therefore ranks *surface form only*. Semantic validity is a
    separate consistency-layer responsibility.
    """

    materialized = tuple(candidates)
    usable = [candidate for candidate in materialized if str(candidate.text or "").strip()]
    rejected_empty = len(materialized) - len(usable)
    if not usable:
        raise ValueError("at least one non-empty realization candidate is required")

    ranked = sorted(
        (score_candidate(candidate, recent_outputs) for candidate in usable),
        key=lambda row: (-row.score, row.candidate.ordinal),
    )
    return SelectionResult(
        selected=ranked[0].candidate,
        ranked=tuple(ranked),
        rejected_empty=rejected_empty,
    )


class RecentSurfaceWindow:
    """Small noncanonical memory of delivered wording for anti-repeat ranking.

    This cache is expression state, not biography. Losing it on renderer swap
    or process restart may reduce anti-repeat quality but cannot change the
    subject's canonical trajectory.
    """

    def __init__(self, max_items: int = 8, initial: Sequence[str] = ()):
        if max_items < 1:
            raise ValueError("max_items must be positive")
        self.max_items = int(max_items)
        self._items = [str(item).strip() for item in initial if str(item).strip()][-self.max_items:]

    def add(self, text: str) -> None:
        value = str(text or "").strip()
        if not value:
            return
        self._items.append(value)
        if len(self._items) > self.max_items:
            self._items = self._items[-self.max_items:]

    def snapshot(self) -> tuple[str, ...]:
        return tuple(self._items)
