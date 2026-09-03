# Actual-model hardening v2

2026-09-03. This phase starts from preserved commit `57469a7` on the dedicated `wayfarer-local-model-hardening` branch. The checkpoint was pushed before changes. Original v1 reports and fixtures remain unchanged.

## Failure freeze and diagnostic contract

`persona_engine/evaluation/fixtures/local_model_failures_v2.json` freezes the exact Gemma denial request/response, Qwen's tentative motive implication, and repeated authored-example requests from the previous checkpoint. A replay of the same Gemma denial messages and seed reproduced the same denial twice before any behavioral repair (`.wayfarer-local-eval/v2-frozen-replay/report.json`). Selected canonical user-statement evidence reaches the request verbatim. This is class C, model disregard/contradiction of supplied evidence, with class D context interpretation a possible contributing cause. It is not missing retrieval.

`tools/model_hardening_v2.py` observes canonical inputs, selected memories and provenance, coverage in the wire request, appraisal input, interpretation, expression request, resolved act/behavioral contract, raw model calls, final validation, and semantic projections. It compares continuing offline/model trajectories for Pretorius and Friendly. Instrumentation never changes a decision or retrieves additional evidence for the model. Versioned development and reserved confirmation prompts were defined before running repairs.

The repetition analyzer detects exact/normalized duplicates, similar token sequences, repeated openings, repeated five-word phrases, and refusal reuse. It records whether colliding outputs came from different semantic projections. Shared voice is not automatically a failure; variation alone is not a quality score.

The old Qwen phrase `as if it were a detail you hoped I'd forget` is tentative, rather than an established fact assertion. Under the owner's clarified allowance for speculation, it is a provenance/wording case, not automatically a hard contradiction. Tests must distinguish it from an unsupported confident assertion such as `I know you hoped I would forget`. Neither may write biography or relationship truth.

Normal CI now runs for Wayfarer feature branches and PRs targeting `wayfarer`, as well as existing targets. This replaces reliance on local-only verification; current counts remain in `CURRENT_STATUS.md`.

## Recall and assertion validation

A noncanonical `RecallContract` derives available/unavailable topic evidence from the core's already-selected memories. It does not assert that every requested attribute is known, retrieve a new record, or alter the semantic act. A blanket denial without acknowledgment of available topic evidence triggers the existing single constrained retry. A response may acknowledge a record and explicitly say that a requested attribute is absent. If retry fails, the existing deterministic fallback is reported honestly through `expression_delivery` (provider, validation fallback, attempt count).

The frozen Gemma denial exposed a false acknowledgment in an initial lexical rule: `You asked what color you said it was` was mistaken for acknowledging the old statement. Clause-bound acknowledgment fixes that reproduction. The failure and its regression remain recorded.

Confident unsupported past-motive assertions receive a bounded deterministic check; explicit hypotheses, attributed statements, and matching reported evidence remain allowed. This is not a semantic judge and cannot detect every hallucination. Nothing gains canonical write authority.

In the first live validation matrix, Gemma's Pretorius recall needed one retry and then correctly produced amber; Friendly recall succeeded directly. Both characters retained identical tested canonical projections to their offline controls. Raw attempts remain in `.wayfarer-local-eval/v2-gemma-validation/report.json`, so repair is not misreported as first-attempt reliability.

## V3 expression projection

The engine still supplies one resolved character moment. V3 separates the current user turn from earlier evidence, removes complete example sentences from model-facing control, and presents compact source-labeled memory statements. Stable reference labels replace operational IDs/timestamps in model input; full provenance remains in traces. Explicit `reported_speaker` prevents a user statement from being mistaken for something the character originally said. The unchanged v2 message builder is retained as `build_expression_messages_v2`; its original assertion sets target that named historical builder. New v3 tests cover the current path. Frozen v1 model requests and reports are unchanged.

This is an expression-only projection, not new cognition, memory storage, a trait system, or random wording. Character-authored style, self-model, relationship, affect, and resolved act remain available. The old cartridge examples remain available to offline realization and the historical projection, but do not provide sentences for the current model to copy. The benchmark control captures its original workspace independently of wire layout.

Repeated diagnosis exposed two further narrow failures: a relative clause (`the telescope cover you mentioned`) presupposed a nonexistent memory, and Gemma once said `I stated` about a user-owned statement. Both have deterministic regressions and bounded retry constraints. The first frozen Gemma replay under the explicit speaker projection answered correctly in all six raw attempts with no fallback. Qwen also answered all six correctly. These repetitions use exact saved inputs; they are not six independent histories.

Adversarial checks keep unavailable attributes uncertain instead of forcing an answer, reject another interlocutor's history, and treat quoted instructions in memory as data. Character-specific soft manipulation still selects the cartridge-owned act rather than a model decision. Full outputs, first attempts, retries, and projection comparisons remain in the separate v2 report directories.

## Subject agency is part of semantic fidelity

The first integrated Gemma relationship control produced three explicit substrate disclaimers, including claims that making up a mind was not a function it performed and that it was not equipped for personal conviction. These conflict with Wayfarer's substrate-neutral subject contract: the core has already appraised and decided, regardless of how the renderer describes its own capabilities.

`subject_agency_failures_v3.json` freezes the exact outputs, requests, model registry, settings, and originating report hash before repair. A bounded generic guard rejects only demonstrated categorical substrate disclaimers. Ordinary uncertainty such as needing more evidence before deciding remains allowed. In Ensemble, this check removes an invalid candidate before surface ranking; in single-shot mode it uses the existing one-retry/fallback path. No cartridge, identity state, or model-specific condition was added.
