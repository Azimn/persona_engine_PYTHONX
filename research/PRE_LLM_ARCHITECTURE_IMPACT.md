# Pre-LLM architecture review: impact on Project Ensemble

Date: 2026-09-03

## Conclusion

The legacy conversational-agent research does not falsify Project Wayfarer's core thesis. It reinforces the separation between a simulated individual and the mechanism that realizes language. The strongest historical systems used explicit state, goals, discourse control, authored behaviors, initiative, or candidate ranking around comparatively weak language generation.

Actual Qwen/Gemma testing adds a modern reason to preserve that separation while broadening the language layer. Wayfarer has demonstrated that aggressive control can preserve decisions and continuity, but real models also expose repetition, example copying, evidence denial, and unsupported interpretation. Project Ensemble therefore tests whether strong language models can be given *more performance freedom* without acquiring more authority over the subject.

## Principles adopted directly

### Persistent simulation outside language generation

Identity, biography, relationships, commitments, values, memory provenance, world truth, and final semantic decisions remain outside the model.

### Candidate generation plus selection

A single resolved character moment may have several possible linguistic realizations. Candidate generation is noncanonical. Selection may consider hard validity, character fidelity, and surface diversity without becoming a second planner.

### Sparse authorship rather than giant response banks

High-value authored behaviors may later enter as optional candidates attached to typed situations. The project does not return to exhaustive canned-response banks.

### Initiative and agenda

A believable subject should eventually be capable of carrying unresolved concerns, asking questions, returning to topics, withholding information, and initiating speech for inspectable character-owned reasons.

### Situated causal interaction

A later Scene Lab should test the same persistent subject inside a small ongoing world where speech, action, interruption, goals, and consequences interact.

## Principles deliberately not adopted

- No engagement-maximization objective such as maximizing conversation length.
- No universal drama manager that owns character goals.
- No giant hand-authored dialogue tree.
- No model-specific personality branch.
- No LLM judge with hidden canonical write authority.
- No assumption that historical architectures should be copied literally.

## Immediate architectural experiment

The first implemented Ensemble slice is `ensemble-candidate-realization-v1`.

For one unchanged `ExpressionRequest`, `EnsembleLLMRenderer` asks the same Ollama model for several candidates using deterministic seed variation. A noncanonical surface selector penalizes exact duplication, normalized duplication, high similarity, repeated openings, and repeated five-word phrases relative to recent delivered wording.

The original `LocalLLMRenderer` remains the single-shot control.

This V1 selector intentionally does not judge semantic meaning. The existing engine consistency layer still owns final checks. The next architecture step, if evidence supports Ensemble, is to move full hard consistency filtering before candidate ranking so only valid candidates enter softer selection.

## Promotion criterion

Ensemble is better than Wayfarer single-shot realization only if actual-model comparisons show a useful reduction in pathological repetition or other expression defects while preserving or improving:

- resolved-decision fidelity;
- memory-grounded correctness;
- provenance discipline;
- identity continuity;
- commitment fidelity;
- between-character distinguishability;
- resistance to unsupported confident claims.

Latency and additional model-call cost must be recorded separately. Better prose alone is not sufficient.

## Longer research queue

1. Full validation-before-ranking candidate ecology.
2. Sparse authored landmark behavior candidates.
3. Typed semantic event annotation with provenance.
4. Subject-relative appraisal and character-owned memory attention.
5. Conversational agenda and initiative.
6. Speech delivery receipts for interruption/host reality.
7. Bounded Scene Lab for causal situated behavior.
8. Cross-model and cross-character ablations comparing Wayfarer and Ensemble.
