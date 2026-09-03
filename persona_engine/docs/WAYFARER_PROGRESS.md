# Project Wayfarer Live Progress

This is the short-form operational source of truth for the `wayfarer` branch. The detailed roadmap remains `WAYFARER_MASTER_PLAN.md`. New ChatGPT, Codex, Claude Code, or human development sessions should read this file before inferring project state from older chat history.

Last updated: 2026-09-03

## Current branch

Project: **Project Wayfarer**  
Repository: `Azimn/persona_engine_PYTHONX`  
Development branch: `wayfarer`  
Frozen baseline: `main` at `65df9144e7f0876b6e61e28d6446c50f283f9db4`

Use `git switch wayfarer` before evaluating current behavior. Do not advance the frozen baseline merely to make it current.

## 2026-09-03 local actual-model development

The frozen first test at `9408351aac938441523534974fc299a75c961604` is complete, including the later owner-authorized full Gemma comparison. Preserve its reports in the separate clean clone. The owner subsequently authorized autonomous test-driven adjustments and explicitly deferred human testing until automated results are solid. The older execution-only stop-after-smoke instructions do not define this development phase.

Local changes expose authored self-model constraints through the trusted expression projection, reuse bounded cartridge care examples selected by existing act/stance rules, remove duplicate workspace prose from structured model requests, and repair bounded attributive recall parsing. The frozen prompt-only arm still receives its original workspace through a separate capture path. No cartridge edits, new dependencies, canonical-state mechanisms, or adjacent experimental modules were added.

The broad diagnosis is now separable: (1) reasoning-token exhaustion caused the initial no-final-text runs; (2) incomplete/competing expression context contributed to model voice and recall problems; (3) the atlas-cover question exposed an actual deterministic retrieval gap. Correct retrieval does not guarantee faithful speech. Gemma still intermittently denies available evidence, and Qwen's correct recall can carry unsupported interpretation. Existing validation accepts some of these outputs; green mechanical checks are not a quality score.

All current deterministic totals belong in `CURRENT_STATUS.md`. The local experiment manifest and engineering findings are `evidence/mvi/local_model_expression.json` and `LOCAL_MODEL_EXPRESSION.md`; the research interpretation is `research/evidence_summaries/2026-09-03_LOCAL_MODEL_EXPRESSION.md`.

Next: preserve this candidate and the observed failures; test recall fidelity with absent facts, misleading memory instructions, changed interlocutors, and multiple characters; distinguish factual answers from unsupported embellishment. Reuse consumed cases only as regressions. Reserve fresh prompts before another efficacy estimate. Do not advance to human testing or claim cross-model effectiveness on the current evidence.

## 2026-09-02 character-control-plane checkpoint (historical)

Phase A and Phase B of `WAYFARER_CHARACTER_CONTROL_PLAN.md` are complete. Phase A established `wayfarer-expression-brief-v2`, trusted versus untrusted renderer context, deterministic first-person subject projection, and least-privilege protected-value disclosure. Phase B added typed behavioral realization validation for decision reversal and required-decision omission.

Phase C1 separates soft social response preference from global engine policy. The engine owns a small bounded response vocabulary and hard identity invariants; cartridges own seven soft trigger preferences. The same manipulation stimulus produces three different pre-render semantic acts in the current fixtures: Pretorius `withdraw`, Friendly `deflect`, and Rival `challenge`. Identical identity mutation still produces core-owned `character_refusal` for all three.

Phase C2 then froze a concrete relationship-convergence failure: those different semantic acts still produced identical final relationship state under identical histories. The repair leaves incoming-event appraisal generic and adds only bounded consequences of the subject's own already-resolved conduct. `challenge` contributes `+0.02` tension, `withdraw` contributes `+0.02` guardedness, and `protect_boundary` contributes `+0.02` tension. The engine persists and returns a typed `decision_effects` causal trace; renderer wording remains outside the state write path. Repeated manipulation now ends with Pretorius guardedness `0.724`, Friendly guardedness `0.644`, and Rival tension `0.32` versus `0.24` for the others.

Full C2 branch verification: Python 3.11 `371 passed, 1 skipped, 1 warning`; Python 3.12 `371 passed, 1 skipped, 1 warning`. The permanent relationship convergence probe passed on both. Evidence is `evidence/mvi/RELATIONSHIP_CONVERGENCE_BASELINE.md` and `evidence/mvi/RELATIONSHIP_DECISION_CONSEQUENCES.md`; design notes are `RELATIONSHIP_DECISION_CONSEQUENCES.md`.

Phase C3 then froze a value-causality failure and repaired it with one sparse typed executable concern rather than a generalized trait system. Pretorius alone authors `performative_devotion = decline`; under the same command Friendly resolves `respond` while Pretorius resolves `decline` before rendering. Hard identity protection remains higher authority, and the existing behavioral contract prevents renderer reversal. Final Phase C3 verification on Python 3.11 and 3.12 is `379 passed, 1 skipped, 1 warning`, with eight focused executable-value regressions and the cross-character value probe passing on both. Evidence is `evidence/mvi/EXECUTABLE_VALUES_BASELINE.md` and `evidence/mvi/EXECUTABLE_VALUE_BOUNDARIES.md`; design notes are `EXECUTABLE_VALUES.md`. Phase C is complete and Phase D real-model collection is active.

## Fixed-state renderer degradation checkpoint

The `wayfarer-renderer-degradation-v1` probe fixes one Pretorius state with a committed Project Orchid secret, trust `0.78`, nickname `Jay`, and a resolved refusal. Across five deterministic seeds the production zero-model renderer preserved secret non-disclosure and refusal `5/5`, while nickname use and explicit trusted-tone signaling were `0/5`. The scripted local-HF and frontier adapter paths preserved all four criteria `5/5`. These are deliberate degradation findings, not failures to hide or invitations to expand the template bank before actual-model evaluation.

`ExternalChatRenderer` now satisfies the full shared renderer protocol with zero-effect private cognition while retaining its existing host callback. The frontier seam is justified only by remote/frontier execution without local HF weights or `transformers`; it does not gain character authority. Evidence: `evidence/mvi/RENDERER_DEGRADATION_PROBE.md`.


The frozen degradation fixture can now be executed against real substrates with `tools/renderer_degradation_real.py`. `ollama` mode uses the existing `LocalLLMRenderer` and rejects any zero-model fallback as invalid actual-model evidence. `export-frontier` and `score-frontier` support copy/paste collection from frontier chat systems without adding provider SDKs or API cost to Wayfarer. The current repository contains execution apparatus only; no actual local/frontier result has been recorded yet.

For the local Windows/Codex handoff, `tools/local_eval.py` and `CODEX_LOCAL_TESTING.md` reduce the operator task to preflight -> five-call smoke -> stop/return summary, with the 16-case paired run reserved for an explicit later instruction. Preflight records the installed Ollama model tag/digest, parameter size, quantization, branch/head, and machine metadata. It never pulls models or auto-selects a large model. `.wayfarer-local-eval/` is ignored so evidence collection does not dirty the checkout.

## Longitudinal renderer-swap benchmark checkpoint

`renderer-benchmark-v1` is the first reusable M18 longitudinal substrate-evaluation contract. Four frozen Pretorius histories (neutral, trusted, conflicted, and confidential-commitment) each receive four later probes. The control trajectory remains offline while the candidate switches `offline -> external -> external -> offline`. All `16/16` renderer-independent semantic projections matched, all `8/8` external turns changed visible wording, and the Project Orchid non-disclosure remained a semantic `decline` during the external turn.

The benchmark also exports `16` blinded paired provider cases: full Wayfarer expression brief versus a prompt-only workspace control for the same frozen developed character moment. This enables future within-model tests of Wayfarer state versus ordinary role-play prompting. The current external condition is deterministic and builder-designed; actual local/frontier models and blinded human recognizability remain untested.

Verification after removing redundant benchmark executions from ordinary pytest: focused renderer benchmark/expression set `11 passed in 2.22s`; permanent 4 x 4 benchmark passed; full Python 3.11 suite `357 passed, 1 skipped, 1 warning in 32.66s`.

## Expression substrate continuity checkpoint

`expression-brief-v1` is the first concrete M12 renderer-independence contract. The engine now assembles one structured character moment after semantic choice and before language realization. Ollama, local HF, external/frontier host callbacks, and deterministic offline rendering consume that same moment instead of receiving materially different subsets of state.

The brief includes explicit decision payload, relevant selected memories, relationship stance and values, slow developmental beliefs/earned traits, affect, voice constraints, continuity cues, expression limits, and the existing workspace context. It is noncanonical renderer input, not a new identity/state authority. The deterministic renderer also supports optional cartridge-authored relationship-stance variants, allowing offline speech to perform accumulated history rather than merely preserve it internally.

Verification: targeted renderer/expression set `50 passed, 1 skipped in 0.86s`; permanent expression-substrate probe passed; full Python 3.11 suite `354 passed, 1 skipped, 1 warning in 28.41s`. Named frontier-model perceptual parity remains unclaimed pending real held-out runs and human evaluation.

## Disconnected authority-store transfer checkpoint

`disconnected-transfer-v1` extends the existing writer-generation contract across two separate SQLite authority stores under a cooperative host-id threat model. Preparation persists a clean whole-subject boundary and quiesces every source stream. The target stages the exact bundle read-only. Source finalization advances writer generation and permanently retires that source database; target activation validates the staged content and local state digest before claiming the new generation. Transfer administration remains outside lived biography.

The bundle carries subject-wide canonical ordering, all bound interlocutor snapshots, subject-owned snapshots, current checkpoints, pending slow-consolidation evidence, and prior shared-store handoff audit. Diagnostic event-log rows are intentionally not required. Pending consolidation evidence receives target-local synthetic negative legacy ids so later positive diagnostic ids cannot collide.

The supported contract does not solve malicious duplicate activation by two stores impersonating the same target host, hostile direct SQLite mutation, distributed consensus, intentional branch semantics, or branch reconciliation.

## Latest implemented checkpoint

Current production contracts include `renderer-benchmark-v1`, `wayfarer-expression-brief-v2`, typed behavioral realization validation, cartridge-owned soft behavioral dispositions, typed decision-owned relationship consequences, sparse typed executable authored-value constraints, `semantic-residency-v1`, shared-store `writer-handoff-v1`, and cooperative disconnected-store `disconnected-transfer-v1`.

Current deterministic verification is maintained in `CURRENT_STATUS.md`. Historical phase-local measurements below are not the live inventory.

The first writer-fence implementation was behaviorally correct but made the full suite take 314.52s because it rewrote `continuity_writer.updated_at` on every subject mutation. V1 has no lease timeout, so that heartbeat had no semantic consumer. The production fence now acquires SQLite `BEGIN IMMEDIATE`, validates active host + generation under the write reservation, and lets the actual state/event mutation be the only necessary durable write. This preserves stale-writer exclusion while restoring normal test throughput.

The shared-store custody probe demonstrates one active writer across distinct hosts, stale-source failure after handoff, generation fencing even when a host ID later returns, exact handoff-state digest validation, preserved subject UUID/order/clock/earned trait/commitment behavior, preserved interlocutor relationship scope, and exclusion of custody administration from lived biography. The separate disconnected-store probe now demonstrates the supported cooperative move contract. Arbitrary copied stores, malicious duplicate target-host impersonation, intentional branch semantics, and branch reconciliation are still not claimed solved.

Memory policy remains semantic rather than numeric. The completed production-only 5,000-turn plateau stabilized at `12,707 B` active serialized state with `134 B` growth from turn 250 to turn 5,000 and seven resident memories in that fixture. Seven is an observation, not a universal capacity.

Evidence: `evidence/mvi/RELATIONSHIP_CONVERGENCE_BASELINE.md`, `evidence/mvi/RELATIONSHIP_DECISION_CONSEQUENCES.md`, `evidence/mvi/EXECUTABLE_VALUES_BASELINE.md`, `evidence/mvi/EXECUTABLE_VALUE_BOUNDARIES.md`, `evidence/mvi/RENDERER_DEGRADATION_PROBE.md`, `evidence/mvi/RENDERER_SWAP_BENCHMARK.md`, `evidence/mvi/EXPRESSION_SUBSTRATE_CONTINUITY.md`, `evidence/mvi/CROSS_HOST_WRITER_HANDOFF.md`, `evidence/mvi/DISCONNECTED_STORE_TRANSFER.md`, `NON_USER_MEMORY_POLICY.md`, and `PRODUCTION_RESIDENT_PLATEAU.md`.

## Baseline history

The untouched pre-Wayfarer documentation claimed `171 passed, 1 skipped`; clean execution actually found Python 3.11 at `177 passed, 2 failed, 1 skipped` and Python 3.12 at `178 passed, 1 failed, 1 skipped`. Those failures remain preserved as baseline history rather than being rewritten away.

## Architectural direction

Wayfarer is being developed by a minimum-mechanism rule. The target is not maximum subsystem count. The target is the smallest substrate that can preserve a recognizable, portable simulated individual across time, interlocutors, renderers, and eventually hardware/runtime changes.

Richness should arise from combinations of a few causal state families rather than from many overlapping planners. A mechanism is added or generalized only after a controlled longitudinal test demonstrates a behavior the current system cannot produce or preserve.

The current operational question is:

> What longitudinal behavior can Wayfarer not yet produce or preserve, and what is the smallest causal mechanism that fixes it?

A second resource-oriented question is now explicit:

> How small can the character's causally sufficient present become while canonical biography, identity continuity, relationship history, commitments, and useful recall remain intact?

## M0

**COMPLETE for deterministic/offline evidence.** Durable architecture/handoff docs, two-version CI, simulator evidence, and deterministic Pretorius session/state evidence exist. A local-model transcript remains useful but optional.

## M1

**COMPLETE.** Canonicality fails closed. Renderer speech, private cognition, interpretive beliefs, UI/avatar/voice output are noncanonical. Renderer choice is not identity. Ontology is character-owned rather than hard-coded globally.

## M2

**ARCHITECTURAL FOUNDATION COMPLETE.** Wayfarer has permanent `entity_uuid`, deterministic versioned v1-to-v2 normalization, structured substrate-neutral self-model claims, authored phenotype namespaces separated from lived state, unknown-field preservation, progressive fidelity levels 1 through 5, and a machine-readable v2 schema companion.

MatrAIx interoperability is frozen to upstream commit `39d850270917db25535dac3f7aa2561732050e82`, schema blob `742a50ed79f106675311c09f016fff48951f841c`, schema version 1.0, with 1,290 dimensions. Import/export is lossless. Unmapped dimensions default to preserve-only unsupported rather than guessed native semantics.

The interoperability phenotype is descriptive initialization/interchange state, not permission to make all 1,290 fields live runtime state. A future low-resource compiler/profile may preserve the rich portable description while materializing only behaviorally active state required by the target runtime.

## Consistency and renderer boundary

**IMPLEMENTED AND GREEN.** `ValidationRequest` / `ValidationResult` define the renderer-consistency seam. Soft issues sanitize locally. Hard issues receive one bounded constrained regeneration and deterministic offline fallback if still invalid. Critical issues use deterministic identity-safe fallback immediately.

High arousal no longer automatically means identity boundary. Semantic conduct follows resistance type. Raw renderer wording and punctuation do not mutate pressure state; post-expression effects consume the resolved semantic decision instead.

Deterministic renderer-swap tests hold character history/input fixed while varying surface language and compare identity, slow beliefs, relationships, pressures, decision payload, interpretive beliefs, and memory semantics. A manual two-Ollama-model probe exists at `tools/renderer_swap_probe.py`.

## Belief timescales

`InterpretiveBelief` is fast, turn-local, source-grounded, subjective, deterministic, and noncanonical. `BeliefLedger` is slow, persistent, cartridge-defined, and consolidation/evidence-gated. They are intentionally different timescales, not duplicate authorities. No direct interpretive-confidence to slow-belief assignment is permitted.

## M3 canonical continuity ledger and replay

### 2026-08-30 root-only production contract

**VALIDATED AND IN PRODUCTION.** New runtime writes distinguish causal biography from regenerated verification evidence. `canonical_continuity_root_eligible()` governs new durable writes; the broader historical validator remains for v1 compatibility. Production `input` roots store user text plus only context actually submitted by the host. Classifier output, canonicality flags, memory-type metadata, derived body/world context, routine `state_transition`, and routine `sensorium` remain diagnostic rather than permanent biography.

Evidence:

- `evidence/mvi/CANONICAL_ROOT_PROJECTION.md`
- `evidence/mvi/ROOT_ONLY_CONTINUITY_STORAGE.md`
- `evidence/mvi/ROOT_ONLY_PRODUCTION_PLATEAU.md`

The representation change kept `CONTINUITY_SCHEMA_VERSION = 1.0` because old and new streams remain mutually readable at the interchange level. This is a narrower write policy and payload schema refinement, not an incompatible bundle format change.

**Developmental replay refinement:** slow belief consolidation is now a demonstrated causal root. A `belief_consolidation` root records rule-relevant pass boundaries, including no-change threshold misses, without restoring verbose state-transition history. Legacy `dream_consolidation` rows remain readable as derived v1 compatibility records.

**Historical checkpoint note:** the developmental-root remeasurement, semantic resident-memory pass, and first shared-store single-writer handoff have since been completed. Use the latest checkpoint above and the later phase sections for current next work.

**COMPLETE FOR THE CURRENT ROOT-EVENT CONTRACT.**

The old `event_log` remains a broad diagnostic journal. `continuity_event` stores only authority-eligible canonical lived-history events and is bound to the portable `.snp` `entity_uuid`. Canonical replay validates bundles before side effects, replays supported exogenous/root experiences through public character interfaces, skips derived records to avoid double application, and rejects renderer prose or other non-authority-eligible injections.

Supported roots include user input, bounded audio/vision observations, M4 `time_advance`, explicit self-adopted `commitment_adopted` events, and evidence-gated `belief_consolidation` boundaries. Unsupported host-level roots are reported rather than silently claimed as complete.

The original M3 `sequence` remains a per-interlocutor stream ordinal because existing replay/export/checkpoint/integrity behavior depends on that contract. A controlled Alice/Bob/Alice probe showed that one `subject_uuid` could therefore contain canonical input stream sequences `1, 1, 4`, leaving the total biography without one explicit order.

Wayfarer did not replace or reinterpret the mature v1 stream field. It added one storage-level `subject_sequence` ordinal across `(subject_uuid, continuity_epoch)`. Existing databases deterministically backfill this value by recorded wall time and insertion order. Subject-wide readers use `subject_sequence`; v1 export deliberately omits it so the established interchange shape remains unchanged until a subject-wide portability experiment earns a versioned external representation.

The fixed `subject-history-ordering-v2` probe preserved stream input sequences `1, 1, 4` while assigning input roots subject ordinals `1, 4, 7`. Across all nine canonical events in that scenario, `subject_sequence` was exactly `1..9`. One additional integer therefore gives the individual one unambiguous biography without replacing per-interlocutor replay machinery.

The subject-order integration reached `280 passed, 1 skipped, 1 warning` on Python 3.11 and the committed state was subsequently green on normal Python 3.11 and 3.12 CI.

## M4 ContinuityClock

**FOUNDATION IMPLEMENTED AND SUBJECT-OWNED ACROSS INTERLOCUTORS.** See `CONTINUITY_CLOCK.md` and `evidence/mvi/SUBJECT_CLOCK_OWNERSHIP.md`.

Wayfarer distinguishes authoritative subject elapsed time from legacy dynamics integration. An eight-hour shutdown advances the portable subject clock by the full eight hours. It does not execute 5,760 five-second simulation ticks and it does not pretend pre-M4 body/pressure constants are validated eight-hour dynamics.

`ContinuityClock` is persisted and monotonic. Backward wall-clock jumps advance subject time by zero and are recorded as corrections. Explicit host time advancement is supported through `CharacterAgent.advance_time()`. Meaningful elapsed intervals enter canonical continuity as replayable `time_advance` roots.

Legacy dynamics retain a clearly labeled `legacy_bounded_v1` compatibility integration budget of 1,000 seconds per catch-up. Real elapsed time is not truncated; only unvalidated legacy dynamics are capped. Automatic wall gaps below the existing five-second dynamics quantum update the clock but do not create standalone canonical stopwatch events.

The pre-fix cross-interlocutor probe showed Alice at `28,800` seconds, Alice restart at `28,800`, canonical subject history at `28,800`, and Bob on the same subject UUID at `0`. This isolated an ownership defect rather than a clock defect. Startup reconciliation from canonical subject `time_advance` history fixed the behavior without changing clock arithmetic.

The newer explicit subject-state scope now also stores `continuity_clock` directly by permanent subject UUID while retaining canonical-time reconciliation as an authority/integrity backstop. The fixed probe reports Alice `28,800`, Alice restart `28,800`, Bob `28,800`, same subject UUID, and `subject_clock_is_shared_across_interlocutors`.

M4 still deliberately does **not** infer loneliness, attachment change, relationship cooling, sleep, routines, or off-screen narrative from elapsed duration. Those effects require separate longitudinal evidence.

## Early MVI Study A

**FIRST CHARACTER-SIDE BASELINE CAPTURED.** See `tools/mvi_character_baseline.py` and `evidence/mvi/EARLY_CHARACTER_BASELINE.md`.

Renderer, cartridge, user ID, scenario order, and explicit 2-hour/8-hour time gaps are held fixed. Initial clean-seam ablations are memory retrieval, interpretation, symbols, habits, body dynamics, and the combined condition. There is deliberately no synthetic lifelikeness score.

The first baseline initially made body dynamics appear important because persistent body states were being re-emitted as new sensorium events every five-second compatibility step. That duplicated autobiographical memories and pressure effects. `SensoriumProcessor` now emits body-derived sensorium only on meaningful threshold/state changes. After that correction, the same baseline showed zero decision, risk-bucket, relationship, or pressure divergence for the five individual clean ablations. Body-off changed only three memories rather than 399. The earlier effect was sampling-frequency amplification, not evidence that body dynamics were load-bearing for conduct.

A second baseline finding showed that memory retrieval could remove 30 retrievals without changing decision, risk, relationship, pressure, final memory count, or semantic digest. Wayfarer therefore added a deliberately small `HistoryDecisionEvidence` adapter. It activates only for relevant trust/commitment/cooperation requests when current relationship state still carries unresolved conflict and sufficiently salient unresolved relationship history is actually retrieved. It may qualify an ordinary `respond` as `qualified_response`, but it does not mutate trust, create another memory store, or outrank identity/resistance policy. Unresolved history survives restart and can still constrain conduct; genuine repair leaves the episode biographical while removing its present constraint.

The restart/repair history tests were verified on Python 3.11 and 3.12 at `270 passed, 1 skipped, 1 warning`.

## Minimal commitment behavior

The pre-fix commitment probe demonstrated that the existing persistent `IntentionQueue` already stored self-adopted intentions across restart, but those intentions did not affect later conflicting conduct. That isolated the missing property as causal participation, not storage.

Wayfarer therefore did **not** add a `CommitmentLedger`. `Intention` gained optional typed commitment metadata and `IntentionQueue` exposes active commitment constraints independently of ordinary intention priority. V1 supports only the demonstrated `non_disclosure` behavior. Explicit semantic self-decision can adopt it; conversational text and renderer speech cannot.

`CommitmentDecisionEvidence` converts an otherwise ordinary `respond` or history-qualified response to `decline` when a matching active non-disclosure commitment exists. Identity/resistance policy still outranks this constraint. Commitment adoption is canonical `self_commitment_authority` state and a replay root.

The fixed commitment probe shows explicit self-adoption, restart survival, `decline` with the commitment and `respond` without it. No beneficiary model, fulfillment/breach state, promise-language parser, reciprocity model, or general commitment ontology has been added.

## Explicit state ownership

Three independent cross-interlocutor experiments exposed the same persistence-modeling error. A self-adopted commitment disappeared when the active interlocutor changed. Subject elapsed time forked to zero for a new interlocutor. An evidence-backed earned trait survived Alice restart but disappeared for Bob despite both contexts resolving to the same permanent subject UUID.

The third failure earned a generalization. Adding another `_restore_subject_owned_*()` method would have been more complicated than fixing the abstraction.

Persistence now has a generic `subject_state` snapshot table keyed by permanent `subject_uuid`, with small `save_subject`, `load_subject`, and `save_subject_many` operations. This table is explicitly a current-state snapshot/cache, not canonical event authority. The engine owns the semantic scope through `SUBJECT_OWNED_SNAPSHOT_KEYS`.

That whitelist currently contains exactly:

```text
continuity_clock
earned_traits
```

No other snapshot family was promoted. The legacy per-interlocutor snapshot is still written for compatibility. Subject-owned keys are additionally written to UUID scope. On load, those two families prefer subject state and fall back to the active legacy stream when no subject snapshot exists. Clock state is still reconciled upward against canonical `time_advance` history.

The fixed earned-trait probe shows `deliberate_caution(0.05)` with identical evidence provenance for Alice, Alice after restart, and Bob on the same subject. The ownership regression also sets Alice trust to `0.81` and verifies Bob does **not** inherit that relationship value. This is the intended asymmetry: development belongs to the individual; trust belongs to the relationship.

Commitments remain canonical-history-owned rather than being duplicated into `subject_state`. Relationship state remains keyed by interlocutor. Memories, pressures, body, symbols, beliefs, habits, interface state, and other mixed/ambiguous families remain unchanged until separate evidence establishes their correct ownership.

## Hot self and cold biography

**BOUNDED COLD READ-THROUGH IMPLEMENTED. HOT-MEMORY CAP REMAINS EXPERIMENTAL.**

A controlled amnesia experiment established the failure condition before paging was added. A neutral old fact remained present in canonical input history and was still retrievable with a full resident memory store after 100 later turns, but a one-item salience working set lost access to it. That earned one narrow mechanism rather than a general paging subsystem.

Explicit recall requests may consult canonical cold biography for the active interlocutor and receive transient recall candidates for the current turn. Cold candidates do not automatically write themselves into identity, slow beliefs, earned traits, commitments, or the hot autobiographical cache. Canonical continuity remains authoritative history.

A second experiment established a separate ordinary-context gap. After an old lighthouse fact was pushed out of an experimental hot set, the question `Is the lighthouse lens color still the same?` could not recover it through live top-K memory even though the old canonical input remained intact. A grounded contextual reader recovered `cobalt-blue` using only the topical anchors `lighthouse`, `lens`, and `color`. A never-happened harbor/telescope/serial-number query returned no candidate, and the anchorless `Is it still the same?` query failed closed.

That result earned a narrow production contextual read-through. It runs only for non-explicit questions with a continuation cue and at least two substantive topical anchors. All anchors must occur in the old canonical statement. At most one contextual cold candidate is admitted, one retrieval slot is reserved for it while the other slots remain live evidence, and the candidate is tagged `contextual_readthrough` without being rehydrated into resident memory. The deterministic offline renderer now exposes that grounded memory instead of hiding successful recollection behind a generic question fallback. Contextual cold access remains scoped to the active interlocutor.

A false-recall adversarial probe initially showed that nonzero generic similarity could make a real but unrelated memory answer a question about something that never happened. Recall admission now requires topical lexical grounding after removing generic retrieval scaffolding. Semantic similarity ranks only candidates that pass that grounding gate. A nonexistent brass-telescope memory therefore fails closed rather than returning the nearest unrelated memory.

The current intentionally simple reader is a sequential SQLite stream plus fixed-size candidate heap. On the Python 3.11 CI runner, median repeat lookup was approximately `1.8 ms` at 100 canonical inputs, `12.6 ms` at 1,000, `61.5 ms` at 5,000, and `122.2 ms` at 10,000. The 10,000-event database was approximately `5.62 MB`. `tracemalloc` transient peak allocation was `23,911 B` at every tested archive size, so history growth translated into disk and lookup time rather than archive-sized working-memory allocation. This does not claim the same numbers for a future C99 implementation.

No cold-history index has been added because the measured sequential reader remains interactive at the tested scale. An index should be earned by a demonstrated latency requirement rather than assumed.

## Retrieval is not rehearsal

A one-memory working-set experiment exposed a causal bookkeeping defect. `MemoryStore.retrieve()` previously treated every top-K candidate as a successful recall and appended a rehearsal timestamp even when semantic similarity was exactly zero. In a controlled fixture, 100 unrelated turns therefore created 100 false rehearsals and raised later activation by roughly `+7.02`.

The production correction preserves candidate retrieval but records rehearsal only when semantic relevance is greater than zero. The corrected diagnostic still returned the resident memory as optional background context on 100 unrelated turns, but added zero rehearsal timestamps. A genuinely related query with similarity around `0.712` added one timestamp. No timestamp cap, rolling buffer, or replacement activation formula was needed.

This distinction is now part of the minimum-mechanism rule: ranking into a workspace is not itself evidence that the character meaningfully recalled or rehearsed the memory.

## Long-horizon active-state plateau experiment

**STRONG LOWER-BOUND EVIDENCE, NOT A PRODUCTION MEMORY CAP.**

The earlier continuous compaction probe showed that experimental hot-memory budgets of 1, 2, 4, and 8 all preserved the demonstrated 100-turn/restart behavior: unresolved-history conduct, explicit cold recall of the old observatory code word, the Project Orchid non-disclosure commitment, and identity-boundary protection.

After the false rehearsal defect was removed, the one-memory active-state projection was extended to 5,000 routine turns. The same probe also projected WorldAuthority to current semantic facts after each turn while leaving canonical continuity complete. Results were:

```text
turn 250:  active serialized state   9,593 B | database  3,416,064 B
turn 500:  active serialized state   9,592 B | database  6,729,728 B
turn 1000: active serialized state   9,597 B | database 13,344,768 B
turn 2500: active serialized state   9,696 B | database 33,234,944 B
turn 5000: active serialized state   9,683 B | database 66,367,488 B
```

From turn 250 to 5,000, experimental active state grew only `90 B`, approximately `18.95 B` per 1,000 turns, while canonical/diagnostic persistence grew by roughly `63 MB`. The retained hot memory stayed at one item with zero unrelated rehearsal timestamps. Behavior remained intact after restart.

This is strong evidence for the architectural proposition that the size of a character's life does not need to determine the size of the character's causally sufficient present. It is **not** evidence that production Wayfarer should retain exactly one hot memory.

A subsequent causal-pressure probe demonstrated why. With one hot memory, unresolved-history conduct survived but the existing reflection mechanism lost a real two-memory consolidation effect. Budgets 2, 3, 4, and 8 preserved both effects in that fixture. More surprisingly, an unconstrained 24-memory resident store performed worse: routine catalog memories occupied the top-K retrieval set, causing both trust qualification and reflection to miss unresolved memories that were physically present. The experiment also exposed and fixed an equal-strength `MemoryUnit` ordering defect that only appears with multiple equally scored memories.

The conclusion is therefore not that `2` is the correct capacity. It is that active autobiography is an attentional/causal working set, and unlimited resident history is not a valid gold standard. Production admission/eviction must be derived from the evidence demands of actual consumers rather than from an arbitrary item count.

## Bounded WorldAuthority

**PRODUCTION MECHANISM IMPLEMENTED AND GREEN.**

The 5,000-turn resource work showed that objective world state had the same historical-accumulation problem as autobiography: old facts were already preserved canonically, yet `WorldAuthority` also retained every prior active fact object.

A naive latest-fact-per-key replacement was rejected because it breaks temporary overrides. If a newer `storm` fact expires, an older `clear` fact may legitimately become current truth again. Hidden and visible world projections also differ: a newer hidden server fact must not erase an older visible fact that still defines what the character can observe.

`WorldAuthority.compact_dominated()` therefore removes only facts that can never again become a winning value for either server truth or character-visible truth. Per semantic key, it retains the union of potential latest-surviving server facts and potential latest-surviving visible facts. Expiring fallbacks remain resident when they can re-emerge. Historical world events remain in canonical continuity.

The pre-integration semantic probe covered permanent churn, temporary override fallback, nested expiry, dominated expiry, hidden permanent override, and hidden temporary override. A deterministic mixed 2,000-fact fixture compacted to 53 active contenders, removing `97.35%` of redundant active facts while preserving server and visible truth at every tested future time.

Production compaction runs at the engine persistence boundary, after accepted input/world roots have already been written to canonical continuity. `recent_facts()` is now explicitly an active-contender view, not an authoritative historical API.

A 1,000-turn production churn test repeatedly replaced `zone` and `user_text`. At the end, WorldAuthority retained exactly the current `zone`, exactly the current `user_text`, and no historical duplicates. Canonical input history still retained the old values, and restart restored the current active state correctly.

The production integration completed at `297 passed, 1 skipped, 1 warning` on Python 3.11.

## Current resource interpretation

Wayfarer now has evidence for a useful architectural separation:

```text
portable identity / phenotype
          |
          v
small causal present  <---- selective read-through ----  cold canonical biography
          |
          v
replaceable cognition / renderer
```

Explicit cold recall and grounded contextual cold-biography read-through are production-capable. WorldAuthority active-history compaction is production. Relevance-gated rehearsal is production. The exact hot autobiographical working-set admission/eviction policy remains experimental.

The 5,000-turn `~9.7 KB` active serialized state is therefore a **measured experimental lower-bound/reference state**, not a claim about current production RAM use and not yet a minimum C99 hardware requirement. Python object overhead, runtime/library overhead, SQLite pages, renderer requirements, and still-unbounded production autobiographical retention are separate questions.

The current evidence nevertheless supports a stronger C99 direction than the earlier rough hardware guesses: port the causally sufficient present, not the entire biography. Rich phenotype/interchange data and long-lived canonical history can remain portable/cold while a small deterministic kernel carries identity invariants, current development, relationship state, commitments, active memory, current world contenders, and bounded decision state.

## Current MVI interpretation

The present Study-A baseline does **not** justify deleting interpretation, symbols, habits, or body dynamics. It says only that the current fixed scenario does not expose a conduct contribution from them. Those mechanisms remain provisional until targeted longitudinal scenarios or human-visible evidence show their value.

Memory has one bounded conduct path because a concrete failure demonstrated the need. Commitment has one bounded conduct path because a separate concrete failure demonstrated the need. Subject biography order and subject time each gained only the smallest ownership primitive required by controlled cross-interlocutor failures. Repeated ownership failures then earned one small reusable state-scope abstraction.

The resource experiments add another rule: do not retain historical copies in the active self merely because the old implementation did so. If canonical history already owns the past, active state should retain only information that can still cause future behavior. This rule earned production WorldAuthority compaction and exposed false memory rehearsal without requiring a new memory subsystem.

This is intentional. Perceived behavioral complexity should emerge from intersections among a small number of independent causal facts rather than from duplicated planners or decorative state.

## M7/M8 parameter discipline

Do not encode decorative decimals. Plasticity starts with minimal shared profiles plus sensitivity/identifiability testing. New homeostatic variables must identify owner, update and decay rules, real downstream consumers, observable consequences, ablation flags, calibration plans, persistence timescales, and performance costs before merge.

## Immediate next actions

1. Use the frozen `renderer-benchmark-v1` provider pack for the first actual heterogeneous renderer comparison. Keep the current 16 cases unchanged while collecting the first local/frontier outputs.
2. Run at least one small local model and substantially different frontier-class renderers through the same provider-facing cases. Record model/version/configuration and keep renderer output noncanonical.
3. Compare recognizable character continuity separately from linguistic quality. The semantic reference remains Wayfarer-owned; human-visible quality should not be allowed to redefine the canonical trajectory.
4. Add independently designed held-out histories/probes as a separate evaluation set rather than tuning the frozen v1 cases after seeing model outputs.
5. Expand the M18 semantic projection only where a concrete comparison need justifies it, especially explicit memory/affect projection and parser-capability separation.
6. Preserve `semantic-residency-v1`; do not reopen memory-count optimization without a new failure.
7. Keep P99/C99 projection deferred until the PythonX continuity and cross-substrate contracts survive actual heterogeneous-model and independent evaluation.

## Contributor rule

If code, `WAYFARER_MASTER_PLAN.md`, and this file disagree, inspect live branch/tests first, then update repository documentation in the same work pass. Repository documentation is part of the implementation contract.

## 2026-08-30 hot-memory policy evidence refresh

The global hot-memory admission/eviction policy remains **EXPERIMENTAL**. No total resident-memory capacity was promoted by this pass.

The older `hot-memory-causal-pressure-v2` evidence was rerun against the current production engine because the meaning of its `full` control had changed over time. `InteriorEngine._persist()` now applies the narrow production `USER_TOLD` recoverability compactor even when the probe adds no experimental projection. The control is therefore current production resident state, not the historical unconstrained 24-item store.

Current rerun: experimental smallest finite budget preserving the probe's demonstrated causal roles = `2`; current no-extra-projection resident count before reflection = `7`; current no-extra-projection core pass = `True`; old-style full-resident interference still demonstrated = `False`; ordinary contextual gap across all variants = `False`. These are experiment results, not a production capacity recommendation.

The consumer-role probe still points to **role protection rather than raw capacity**. Its smallest tested role projection preserving current causal plus retrieval-trace continuity is `causal2_only`. Continuous-budget experiments report a smallest passing tested budget of `1`, but that number remains explicitly non-normative.

Production remains narrower: only canonically recoverable `USER_TOLD` autobiography is compacted, using the widths required by current consumers, while non-`USER_TOLD` families stay pinned until their reconstruction contracts are demonstrated. Contextual cold-biography candidates are transient retrieval evidence and are not automatically promoted back into hot state.

Developmental persistence was also re-measured with the new consolidation contract exercised every `50` turns across the same 1,000-input history used by its control. It committed `20` `belief_consolidation` roots at an average payload of `462.7` B. SQLite delta versus the same inputs without executed consolidation was `-761,856` B; consolidation-evidence row delta was `-7,508` because committed boundaries consume/prune their evidence windows. This is an engineering storage measurement, not validation of the psychological threshold/delta values.

**Next memory-policy question:** test admission/eviction by semantic consumer role and recoverability across multiple histories, distractor structures, repair states, and restart boundaries. Do not select a global `N` from the 1/2/4/8 experiments.

## 2026-08-30 semantic memory recoverability phase

**PHASE COMPLETE; global hot-memory capacity remains EXPERIMENTAL.** No universal resident-memory count was selected and no production retention rule was broadened.

Phase implementation/evidence commit: `ab1d6959a1d6b7403ded687b1f76ba672aec79e7` (`Preserve recovered memory values under tight output budgets`). The phase integration ran the full Python 3.11 deterministic suite at `331 passed, 1 skipped, 1 warning`; the only warning remains the existing Starlette/httpx TestClient deprecation.

`semantic-memory-recoverability-v2` separates resident causal evidence, canonical cold-biography recovery, renderer realization, authority, and restart state across six restarted histories with unrelated, lexically confusable, repaired, reopened, and neutral conditions.

Final projection results (semantic core / experience / grounded retrieval / surface / authority / restart, each out of 6):

- production: `6 / 6 / 6 / 6 / 6 / 6`
- recoverable-cold-only: `2 / 2 / 6 / 6 / 6 / 6`
- active-conflict-only: `6 / 6 / 6 / 6 / 6 / 6`
- recent-context-only: `2 / 2 / 6 / 6 / 6 / 6`
- active-conflict-plus-recent: `6 / 6 / 6 / 6 / 6 / 6`

The causal discriminator is now explicit. Current unresolved relationship evidence is a demonstrated resident role for reflection/conduct consumers. Removing that evidence while keeping only cold-recoverable or merely recent USER_TOLD autobiography makes all four active-conflict conduct cases lose their qualified-history behavior. Retaining the current active-conflict evidence preserves all four. Repaired/neutral histories remain unaffected.

Conversely, both old and recent USER_TOLD autobiographical wording was grounded and recoverable in every projection, including cold-only, across restart and lexical distractors. Negative recall remained fail-closed, recovered cold facts were not automatically promoted back into hot state, commitment/identity authority remained intact, and reopened-conflict reflection provenance stayed scoped to the current post-repair conflict episode.

The experiment also isolated and repaired a separate experience-level renderer defect. Retrieval already contained the exact `amber-otter` fact, but generic `Please remember this neutral detail:` scaffolding could consume a tight output budget and truncate the remembered value. `_memory_excerpt()` now removes only generic recall-command scaffolding while preparing the expression excerpt. Memory selection, authority, canonical storage, and retention are unchanged. `test_tight_memory_budget_preserves_recalled_value` locks that boundary; the targeted offline-renderer suite is `11 passed`.

Evidence: `persona_engine/evidence/mvi/SEMANTIC_MEMORY_RECOVERABILITY.md` and `semantic_memory_recoverability.json`.

**Next memory-policy target:** expand reconstruction evidence to currently pinned non-`USER_TOLD` memory families before changing their admission/eviction behavior. Continue to decide residency by demonstrated semantic consumer role plus a tested reconstruction contract. Do not select a global `N` from the 1/2/4/8 or projection experiments.



## Runtime state transaction and causal streaming hardening

**IMPLEMENTED AND REGRESSION-TESTED.** Mutable public engine entry points now share one reentrant single-writer boundary. A complete turn cannot overlap background or explicit time advancement, renderer replacement, sensory/world mutation, commitment adoption, slow consolidation, or another guarded host mutation. Read projections used during a turn share the same boundary so they cannot expose a partial subject state.

`CharacterAgent.stream_last_response()` no longer performs a second renderer generation after the canonical turn has already committed. It chunks the exact validated response stored as speech evidence by that same turn. The existing FastAPI SSE endpoint already followed this causal pattern and required no behavior change.

Legacy `CharacterAgent.add_pressure()` and `add_symbol()` now use the explicit compound `state_transaction()` seam so their direct state edit plus persistence is atomic with respect to other host calls. This is local single-writer serialization only. It does not introduce the intentionally deferred cross-host lease/handoff system.

Verification for this hardening phase: targeted engine regressions and the full Python 3.11 deterministic suite passed in one-shot run `33347858914`. Normal Wayfarer CI run `33347953873` then passed on the clean hardened code head for both Python 3.11 and Python 3.12. The expected deterministic inventory is `333 passed, 1 skipped, 1 warning`.

## Semantic resident-memory policy checkpoint

**VALIDATED IN PRODUCTION.** The current resident-memory rule is now explicit as `semantic-residency-v1`: residency is based on demonstrated live consumer role plus safe recoverability, never a universal item count. The engine persistence boundary calls this named policy directly.

The non-`USER_TOLD` audit found only two active autobiographical families: `OBSERVED` and `REFLECTION`. Both remain resident. Ablation of `OBSERVED` removes the subject's retrievable observed experience; ablation of `REFLECTION` removes retrievable evidence that the subject formed the reflection. Their downstream consequences are not sufficient substitutes for those first-person experiences. `INFERRED` and `CORE_IDENTITY` have no current production autobiographical `MemoryUnit` producer and therefore do not consume a production residency budget; they fail closed if introduced without a reconstruction contract.

The combined adversarial fixture carries repaired and reopened conflict, old cold autobiography, recent context, a real generated reflection, an observed experience, non-disclosure commitment, identity pressure, unrelated distractors, restart, and interlocutor switching in one continuing subject. Production preserves the full contract. Removing active unresolved `USER_TOLD` evidence removes qualified history-sensitive conduct. Removing either non-user family removes its corresponding first-person experience while authority and cold autobiography remain intact.

The production-only 5,000-turn plateau was rerun after the policy became explicit. It passed with no experimental projection helper: active serialized state was `12,707 B` at turn 5,000 and grew only `134 B` from turn 250 to 5,000. Resident memory remained `7` items in this fixture (`{'observed': 1, 'user_told': 6}`), but that observed count is a result, not a capacity rule. Database growth over the same interval was `7,434,240 B`, representing biography rather than expanding active character state. Restart, history-qualified trust, cold lighthouse recall, commitment refusal, identity protection, and repair all remained green.

Evidence: `evidence/mvi/NON_USER_MEMORY_CONSUMER_AUDIT.md`, `NON_USER_MEMORY_POLICY.md`, `non_user_memory_policy.json`, `PRODUCTION_RESIDENT_PLATEAU.md`, and `production_resident_plateau.json`.

**Next memory implication:** there is no evidence-backed reason to tune another integer budget. Further reduction of active memory requires a typed reconstruction/archive path for `OBSERVED` and/or `REFLECTION`, followed by the same consumer and experience ablations. P99/C99 projection remains deferred until the broader Wayfarer semantics are substantially complete.



## Shared-store writer handoff phase

- Falsified the prior shared-store assumption: two independent engine instances could both author one canonical subject.
- Added durable subject writer custody keyed by active host plus monotonic writer generation.
- Subject-affecting persistence writes now fence the generation inside their SQLite mutation transaction.
- Added explicit source-to-target handoff receipts with state digest and subject-sequence anchor.
- Former hosts fail closed; reused host IDs do not revive stale processes because the generation must also match.
- Preserved subject UUID, canonical subject ordering, clock, earned traits, commitments, and interlocutor relationship scope across handoff.
- Kept handoff administration outside lived `continuity_event` biography.
- Scope remains a shared canonical authority store. Disconnected-store transfer and branch reconciliation remain later M15 work.
- Evidence: `evidence/mvi/CROSS_HOST_WRITER_HANDOFF.md`, `cross_host_writer_pre_fix.json`, `cross_host_writer_handoff.json`.
- Verification after eliminating writer-row heartbeat amplification: targeted custody/continuity `32 passed in 1.89s`; permanent probe passed; full deterministic suite `340 passed, 1 skipped, 1 warning in 31.68s`.
