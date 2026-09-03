"""Multi-candidate model realization for Project Ensemble.

This renderer broadens linguistic possibility without broadening model authority.
Every candidate receives the same already-resolved ``ExpressionRequest``.  The
model may vary wording; it may not choose a different decision, memory, fact, or
relationship state.  The selected text still passes through the engine's normal
consistency layer before exposure.
"""

from __future__ import annotations

from typing import Any

from .ensemble_realization import (
    CandidateSource,
    RealizationCandidate,
    RecentSurfaceWindow,
    select_candidate,
)
from .expression_bridge import build_expression_messages
from .renderer import LocalLLMRenderer
from .renderer_contract import ExpressionRequest


ENSEMBLE_REALIZATION_VERSION = "ensemble-candidate-realization-v1"


class EnsembleLLMRenderer(LocalLLMRenderer):
    """Generate several performances of one resolved turn and select one.

    V1 selection is intentionally narrow: it minimizes pathological reuse of
    recent wording.  It does not score personality, goals, factual correctness,
    or preferred conduct.  Those remain owned by the subject core and the
    existing consistency validator.
    """

    def __init__(
        self,
        *args,
        candidate_count: int = 3,
        recent_surface_window: int = 8,
        candidate_seed_stride: int = 7919,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        if not 1 <= int(candidate_count) <= 8:
            raise ValueError("candidate_count must be between 1 and 8")
        if int(candidate_seed_stride) == 0:
            raise ValueError("candidate_seed_stride must be non-zero")
        self.candidate_count = int(candidate_count)
        self.candidate_seed_stride = int(candidate_seed_stride)
        self._recent_surface = RecentSurfaceWindow(max_items=int(recent_surface_window))
        self._last_ensemble_trace: dict[str, Any] | None = None

    def runtime_status(self) -> dict:
        status = dict(super().runtime_status())
        status.update({
            "realization_mode": ENSEMBLE_REALIZATION_VERSION,
            "candidate_count": self.candidate_count,
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
                "selected_text": rendered,
            }
            return rendered

        messages = build_expression_messages(request)
        candidates: list[RealizationCandidate] = []
        failures: list[dict[str, Any]] = []

        for ordinal in range(self.candidate_count):
            seed = self._candidate_seed(request.seed, ordinal)
            try:
                content = self._ollama_chat(messages, seed)
                if not content:
                    failures.append({"ordinal": ordinal, "seed": seed, "reason": "empty_response"})
                    continue
                candidates.append(RealizationCandidate(
                    text=self._clean_truncate(content, max_chars),
                    source=CandidateSource.MODEL,
                    ordinal=ordinal,
                    seed=seed,
                    metadata={"provider": "ollama", "model": self.model_name},
                ))
            except Exception as exc:
                failures.append({
                    "ordinal": ordinal,
                    "seed": seed,
                    "reason": f"{type(exc).__name__}",
                })

        if not candidates:
            self._actual_backend = "offline"
            self._fallback_reason = "No Ensemble candidate returned final model text."
            rendered = self._offline.render_expression_request(request, max_chars=max_chars)
            self._recent_surface.add(rendered)
            self._last_ensemble_trace = {
                "version": ENSEMBLE_REALIZATION_VERSION,
                "mode": "offline_fallback",
                "candidate_failures": failures,
                "selected_text": rendered,
            }
            return rendered

        selection = select_candidate(candidates, self._recent_surface.snapshot())
        selected = selection.selected.text
        self._recent_surface.add(selected)
        self._actual_backend = "ollama"
        self._fallback_reason = None
        self._last_ensemble_trace = {
            "version": ENSEMBLE_REALIZATION_VERSION,
            "mode": "candidate_selection",
            "requested_candidate_count": self.candidate_count,
            "generated_candidate_count": len(candidates),
            "candidate_failures": failures,
            "selected_ordinal": selection.selected.ordinal,
            "selected_seed": selection.selected.seed,
            "ranked": [
                {
                    "ordinal": row.candidate.ordinal,
                    "seed": row.candidate.seed,
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
