# Local model expression and retrieval findings

Date: 2026-09-03. Evidence tier: internal builder-designed development and engineering tests.

Authoritative engineering account: [LOCAL_MODEL_EXPRESSION.md](../../persona_engine/evidence/mvi/LOCAL_MODEL_EXPRESSION.md). Machine-readable artifact custody and measurements: [local_model_expression.json](../../persona_engine/evidence/mvi/local_model_expression.json). Current implementation and numeric verification remain governed by code, tests, and `CURRENT_STATUS.md`.

The first frozen Gemma collection establishes that the actual renderer path can execute, not that Wayfarer is generally effective. A thinking-budget failure was distinguishable from semantic/character failure because the provider returned reasoning without final text and the harness marked fallback invalid. Disabling thinking was a host-profile adjustment, not a change to subject identity.

The subsequent experiments separate three failure locations: missing recall-question activation, competing/incomplete model-facing projection, and model failure to use available evidence faithfully. An attributive recall question failed deterministically before repair. After retrieval was corrected, Gemma could still deny a supplied memory; Qwen could answer correctly while adding an unsupported interpretation. This is a concrete limitation of treating either retrieval success, canonical-state equality, or keyword-based output scoring as sufficient character continuity evidence.

Existing cartridge examples provide an economical expression cue for accumulated relationship state. They also induce copying. Better transmission of a designed cue is not by itself evidence that a model independently infers lived character meaning. A same-state ablation and cross-character deterministic checks support the narrower claim that these cues remain noncanonical projections rather than a new identity authority.

A saved-message Gemma ablation implicated duplicate legacy workspace context in a recall failure, but later repetitions remained unreliable. The instruction-only alternative failed and was discarded. Preserve both the improvement and the negative repeat. Requests built in separate runs include changing operational metadata, so a fixed sampling seed alone does not establish identical input. Exact wire messages are more informative than model tag and seed alone.

The earlier frozen 16-pair comparison and these development probes are different protocols. Their prompt-only controls also differ in supplied representation/information, limiting a pure architectural causal claim. No result here establishes superiority over independently designed alternatives, frontier-model parity, broad recognizability, or thesis-level validation.

Reserved sets used to guide repairs were explicitly retired into development evidence. The final structured-context confirmation uses fresh phrasing/seeds but retains builder-designed histories. It does not satisfy the independent protocol in `research/HELD_OUT_CROSS_MODEL_IDENTITY_PROTOCOL.md`. Human testing is deferred at the owner's request; the next evidence should improve automated recall fidelity, attribution, adversarial robustness, and within-/between-character discrimination first.
