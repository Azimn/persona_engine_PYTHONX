# Ensemble Model Collection Readiness

Date: 2026-09-03

This note follows the frozen architecture checkpoint in `ENSEMBLE_CAUSAL_ARCHITECTURE_CHECKPOINT.md`; it does not modify that earlier evidence.

The final pre-integration collection-harness commit was `b30f4904595d8f5be0cc11e0b1e28193cd94e7f7`. GitHub Actions run `33779833026` completed successfully on Python 3.11 and Python 3.12, including the full deterministic suite, focused Ensemble architecture tests, evaluation entry-point checks, and deterministic Scene Lab smoke.

Wayfarer model hardening and Ensemble were direct descendants of the same `76e054d` checkpoint and are now integrated on `wayfarer-local-model-hardening`. The combined local Python 3.11 verification is recorded in `CURRENT_STATUS.md`.

## Matched-history correction earned by the first live run

The first Qwen Ensemble collection stopped on a `semantic_projection_mismatch` in the repaired history. Beliefs, commitments, decisions, and every relationship magnitude matched. The only difference was `last_conflict_resolved_at`: the old v2 probe rebuilt the offline and model histories at different wall-clock times.

The corrected probe still creates histories solely through public character inputs and restarts the continuing subject. It then closes that pre-probe database and forks the same temporary evaluation snapshot for the offline reference and every model seed. Each temporary arm calls public `advance_time(0, record_event=False)` immediately before the probe so elapsed model-generation latency cannot trigger different idle dynamics. This makes the renderer the only experimental difference and preserves the exact canonical repair boundary in both arms. Temporary branches are never merged and have no production authority.

Reports record the exact git head, source-file hashes, cartridge hash, installed model registry/digest, generation settings, captured `ExpressionRequest`, live renderer status, every surviving or rejected candidate text and its validation/ranking trace, final delivery status, and renderer-independent semantic projection. Collection fails closed if Ollama falls back, candidate authority is not `engine_live`, engine validation falls back, or semantic projection differs.

Surface diagnostics treat observed phrases such as `process information` and `operate on parameters` as mechanistic speech. This is a reported prose symptom, not a semantic rejection by itself; a character can use technical language without surrendering subject authority.

The comparator can explicitly rescore both saved arms under the current symptom rubric. Default comparison preserves each historical report's original labels; current-rubric rescoring is opt-in and recorded in the command used, so a changed diagnostic definition cannot silently rewrite old evidence.

This is a collection-integrity repair, not evidence that Ensemble improves prose. The failed report remains under the ignored local evaluation directory and will be indexed by hash with the completed model results.

The situated Scene Lab report is versioned as `ensemble-scene-lab-run-v2` for actual-model evidence. In addition to the full scene, turn, candidate, and delivery traces, it records git head, relevant source hashes, cartridge hash, installed model registry/digest, and generation settings. Earlier v1 Scene Lab output remains valid as an architecture smoke but lacks this evidence-freeze metadata.
