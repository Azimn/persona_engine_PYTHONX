"""Multi-candidate model realization for Project Ensemble.

The renderer broadens linguistic possibility without broadening model authority.
Every candidate receives the same already-resolved ``ExpressionRequest``. The
model may vary wording, pacing, metaphor, elaboration, and conversational shape;
it may not choose a different decision, memory, fact, commitment, relationship
state, or identity.

Ensemble v2 also reuses the deterministic production consistency layer *before*
soft ranking. Hard/critical candidates never enter the diversity competition.
The engine still validates the selected utterance again before exposure.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from .ensemble_realization import (
    CandidateSource,
    RealizationCandidate,
    RecentSurfaceWindow,
    select_candidate,
)
from .ensemble_validation import (
    ENSEMBLE_PREVALIDATION_VERSION,
    filter_candidate_pool,
    validate_candidate,
)
from .expression_bridge import build_expression_messages
from .renderer import LocalLLMRenderer
from .renderer_contract import ExpressionRequest


ENSEMBLE_REALIZATION_VERSION = "ensemble-candidate-realization-v2"

_PERFORMANCE_MODES = ("direct", "contextual", "initiative")


def _performance_license(mode: str, request: ExpressionRequest) -> str:
    """Give the model bounded expressive freedom without granting new authority."""

    resolved = request.resolved_state if isinstance(request.resolved_state, dict) else {}
    experience = resolved.get("experience_context", {}) if isinstance(resolved, dict) else {}
    continuity = experience.get("continuity", {}) if isinstance(experience, dict) else {}
    if not isinstance(continuity, dict):
        continuity = {}

    if mode == "direct":
        return (
            "ENSEMBLE PERFORMANCE MODE: DIRECT. Realize the resolved moment naturally and specifically. "
            "Avoid stock phrasing. You may choose any fresh wording that preserves the selected act and evidence."
        )

    if mode == "contextual":
        return (
            "ENSEMBLE PERFORMANCE MODE: CONTEXTUAL. Answer the current message directly, but let the subject's "
            "current relationship, affect, habit, shared symbol, or unresolved thread shape emphasis and phrasing when "
            "relevant. Do not force a callback and do not invent a new event or goal."
        )

    available = [
        str(continuity.get(key, "")).strip()
        for key in ("selected_intention", "open_loop", "shared_symbol", "active_habit")
        if str(continuity.get(key, "")).strip()
    ]
    agenda_hint = " | ".join(available[:3])
    suffix = f" Current character-owned continuity cues: {agenda_hint}." if agenda_hint else ""
    return (
        "ENSEMBLE PERFORMANCE MODE: INITIATIVE. First honor the already-resolved response. If it is natural, the "
        "character may also contribute one brief question, observation, or topic connection rooted in an existing "
        "character-owned intention, unresolved thread, shared symbol, or habit. This is permission for initiative, not "
        "permission to create new canonical goals, memories, facts, or relationship state. Do not manufacture a concern "
        "merely to use this mode." + suffix
    )


def _messages_for_mode(request: ExpressionRequest, mode: str) -> list[dict[str, str]]:
    messages = deepcopy(build_expression_messages(request))
    if messages:
        messages[0]["content"] = messages[0].get("content", "") + "\n\n" + _performance_license(mode, request)
    return messages


def _authored_landmark_candidates(request: ExpressionRequest, start_ordinal: int) -> list[RealizationCandidate]:
    """Promote sparse authored relational examples into peer candidates.

    These strings were already selected upstream from typed act/stance context.
    They are no longer shown to the model as sentences to imitate in V3. In
    Ensemble they may compete directly as authored performances, but they must
    pass the same candidate consistency contracts as model output.
    """

    resolved = request.resolved_state if isinstance(request.resolved_state, dict) else {}
    experience = resolved.get("experience_context", {}) if isinstance(resolved, dict) else {}
    voice = experience.get("voice", {}) if isinstance(experience, dict) else {}
    examples = voice.get("authored_examples", ()) if isinstance(voice, dict) else ()
    if not isinstance(examples, (list, tuple)):
        return []

    result: list[RealizationCandidate] = []
    for index, text in enumerate(examples):
        value = str(text or "").strip()
        if not value:
            continue
        result.append(RealizationCandidate(
            text=value,
            source=CandidateSource.AUTHORED,
            ordinal=start_ordinal + index,
            seed=None,
            metadata={"candidate_kind": "authored_landmark"},
        ))
    return result


class EnsembleLLMRenderer(LocalLLMRenderer):
    """Generate several performances of one resolved turn and select one.

    V2 uses three complementary mechanisms:

    * several model candidates, rotating direct/contextual/initiative licenses;
    * sparse authored landmark candidates already selected by typed context;
    * deterministic candidate prevalidation before surface-diversity ranking.

    This class still does not choose the character's conduct. Every candidate is
    a realization of the same immutable ``ExpressionRequest``.
    """

    def __init__(
        self,
        *args,
        candidate_count: int = 3,
        recent_surface_window: int = 8,
        candidate_seed_stride: int = 7919,
        prevalidate_candidates: bool = True,
        include_authored_landmarks: bool = True,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        if not 1 <= int(candidate_count) <= 8:
            raise ValueError("candidate_count must be between 1 and 8")
        if int(candidate_seed_stride) == 0:
            raise ValueError("candidate_seed_stride must be non-zero")
        self.candidate_count = int(candidate_count)
        self.candidate_seed_stride = int(candidate_seed_stride)
        self.prevalidate_candidates = bool(prevalidate_candidates)
        self.include_authored_landmarks = bool(include_authored_landmarks)
        self._recent_surface = RecentSurfaceWindow(max_items=int(recent_surface_window))
        self._last_ensemble_trace: dict[str, Any] | None = None

    def runtime_status(self) -> dict:
        status = dict(super().runtime_status())
        status.update({
            "realization_mode": ENSEMBLE_REALIZATION_VERSION,
            "candidate_count": self.candidate_count,
            "prevalidation": self.prevalidate_candidates,
            "prevalidation_version": ENSEMBLE_PREVALIDATION_VERSION if self.prevalidate_candidates else None,
            "authored_landmarks": self.include_authored_landmarks,
            "recent_surface_count": len(self._recent_surface.snapshot()),
            "last_ensemble_trace": self._last_ensemble_trace,
        })
        return status

    def recent_surfaces(self) -> tuple[str, ...]:
        return self._recent_surface.snapshot()

    def remember_surface(self, text: str) -> None:
        """Seed noncanonical expression history for evaluation or host handoff."""

        self._recent_surface.add(text)

    def last_ensemble_trace(self) -> dict[str, Any] | None:
        return self._last_ensemble_trace

    def _candidate_seed(self, base_seed: int | None, ordinal: int) -> int:
        base = int(base_seed or 0)
        return base + ordinal * self.candidate_seed_stride

    def _offline_fallback(self, request: ExpressionRequest, max_chars: int, *, failures, rejected) -> str:
        self._actual_backend = "offline"
        self._fallback_reason = "No valid Ensemble candidate survived generation and prevalidation."
        rendered = self._offline.render_expression_request(request, max_chars=max_chars)
        offline_candidate = RealizationCandidate(
            text=rendered,
            source=CandidateSource.OFFLINE,
            ordinal=10_000,
            metadata={"candidate_kind": "deterministic_fallback"},
        )
        offline_record = validate_candidate(offline_candidate, request) if self.prevalidate_candidates else None
        if offline_record is not None and not offline_record.accepted:
            rendered = "..."
        elif offline_record is not None:
            rendered = offline_record.result.output_text
        self._recent_surface.add(rendered)
        self._last_ensemble_trace = {
            "version": ENSEMBLE_REALIZATION_VERSION,
            "mode": "offline_fallback",
            "candidate_failures": failures,
            "prevalidation_rejections": rejected,
            "selected_source": CandidateSource.OFFLINE.value,
            "selected_text": rendered,
        }
        return rendered

    def generate_expression(self, request: ExpressionRequest) -> str:
        if isinstance(request.expression_constraints, dict):
            max_chars = int(request.expression_constraints.get("max_chars", 200))
        else:
            max_chars = int(getattr(request.expression_constraints, "max_chars", 200))

        if self.provider != "ollama":
            rendered = super().generate_expression(request)
            self._recent_surface.add(rendered)
            self._last_ensemble_trace = {
                "version": ENSEMBLE_REALIZATION_VERSION,
                "mode": "single_non_ollama_fallback",
                "selected_source": CandidateSource.OFFLINE.value,
                "selected_text": rendered,
            }
            return rendered

        candidates: list[RealizationCandidate] = []
        failures: list[dict[str, Any]] = []

        for ordinal in range(self.candidate_count):
            seed = self._candidate_seed(request.seed, ordinal)
            mode = _PERFORMANCE_MODES[ordinal % len(_PERFORMANCE_MODES)]
            messages = _messages_for_mode(request, mode)
            try:
                content = self._ollama_chat(messages, seed)
                if not content:
                    failures.append({"ordinal": ordinal, "seed": seed, "mode": mode, "reason": "empty_response"})
                    continue
                candidates.append(RealizationCandidate(
                    text=self._clean_truncate(content, max_chars),
                    source=CandidateSource.MODEL,
                    ordinal=ordinal,
                    seed=seed,
                    metadata={
                        "provider": "ollama",
                        "model": self.model_name,
                        "performance_mode": mode,
                    },
                ))
            except Exception as exc:
                failures.append({
                    "ordinal": ordinal,
                    "seed": seed,
                    "mode": mode,
                    "reason": f"{type(exc).__name__}",
                })

        model_candidate_count = len(candidates)
        if self.include_authored_landmarks:
            candidates.extend(_authored_landmark_candidates(request, start_ordinal=self.candidate_count))
        authored_candidate_count = len(candidates) - model_candidate_count

        rejected: list[dict[str, Any]] = []
        if self.prevalidate_candidates and candidates:
            batch = filter_candidate_pool(candidates, request)
            for record in batch.rejected:
                rejected.append({
                    "ordinal": record.candidate.ordinal,
                    "source": record.candidate.source.value,
                    "action": record.result.action.value,
                    "issue_codes": [issue.code for issue in record.result.issues],
                })
            candidates = list(batch.survivors)

        if not candidates:
            return self._offline_fallback(request, max_chars, failures=failures, rejected=rejected)

        selection = select_candidate(candidates, self._recent_surface.snapshot())
        selected = selection.selected.text
        self._recent_surface.add(selected)
        self._actual_backend = "ollama" if any(candidate.source == CandidateSource.MODEL for candidate in candidates) else "authored"
        self._fallback_reason = None
        self._last_ensemble_trace = {
            "version": ENSEMBLE_REALIZATION_VERSION,
            "mode": "validated_candidate_selection" if self.prevalidate_candidates else "candidate_selection",
            "requested_candidate_count": self.candidate_count,
            "generated_model_candidate_count": model_candidate_count,
            "authored_candidate_count": authored_candidate_count,
            "surviving_candidate_count": len(candidates),
            "candidate_failures": failures,
            "prevalidation_rejections": rejected,
            "selected_ordinal": selection.selected.ordinal,
            "selected_seed": selection.selected.seed,
            "selected_source": selection.selected.source.value,
            "selected_performance_mode": selection.selected.metadata.get("performance_mode"),
            "ranked": [
                {
                    "ordinal": row.candidate.ordinal,
                    "source": row.candidate.source.value,
                    "seed": row.candidate.seed,
                    "performance_mode": row.candidate.metadata.get("performance_mode"),
                    "prevalidation_action": row.candidate.metadata.get("prevalidation_action"),
                    "score": row.score,
                    "exact_recent_match": row.exact_recent_match,
                    "normalized_recent_match": row.normalized_recent_match,
                    "max_recent_similarity": row.max_recent_similarity,
                    "repeated_opening": row.repeated_opening,
                    "repeated_phrase": row.repeated_phrase,
                }
                for row in selection.ranked
            ],
        }
        return selected
