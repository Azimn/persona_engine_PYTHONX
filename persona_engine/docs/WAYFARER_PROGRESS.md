# Project Wayfarer Live Progress

This is the short-form operational source of truth for the `wayfarer` branch. The detailed roadmap remains `WAYFARER_MASTER_PLAN.md`. New ChatGPT, Codex, Claude Code, or human development sessions should read this file before inferring project state from older chat history.

Last updated: 2026-08-30

## Current branch

Project: **Project Wayfarer**  
Repository: `Azimn/persona_engine_PYTHONX`  
Development branch: `wayfarer`  
Frozen baseline: `main` at `65df9144e7f0876b6e61e28d6446c50f283f9db4`

Use `git switch wayfarer` before evaluating current behavior. Do not advance the frozen baseline merely to make it current.

## Latest implemented checkpoint

Current production/evidence head before this documentation update:

```text
268739c
Preserve slow belief development in canonical continuity
```

The developmental-continuity production gate completed with:

```text
Focused developmental/continuity/replay tests: 18 passed
Full Python 3.11 deterministic suite: 330 passed, 1 skipped, 1 warning
Changed slow belief: live -0.4, restart -0.4, canonical replay -0.4
Separated no-change repair boundaries: live 0.0, canonical replay 0.0
```

The prior root-only storage evidence remains the current persistence-size baseline:

```text
1,000-turn SQLite file: 2,486,272 B
5,000-turn SQLite file: 8,581,120 B
5,000-turn active serialized state: 12,758 B
```

The canonical-root projection first demonstrated that a mixed 21-event history could be reduced to 9 causal roots while preserving the exact semantic replay digest, cold biography, submitted host context, commitment continuity, subject time, and bounded sensory replay. Serialized event bytes fell 73.27% and payload bytes fell 82.73% in that experiment.

Production now follows the same causal contract. New v1 runtime histories retain minimum-sufficient roots rather than routine regenerated `state_transition` and `sensorium` records. Historical v1 histories containing those derived rows remain valid, importable, and replayable; replay skips the derived records rather than double-applying them. Rich derived packets remain available in the bounded diagnostic journal.

The 1,000-turn production storage probe reduced durable continuity from approximately 3.01 rows per exercised turn to 1.004. Canonical input payloads averaged 75.75 B and exact canonical/diagnostic payload duplication was zero. The complete database fell from the previous approximately 6.78 MB measurement to 2.49 MB.

The 5,000-turn production plateau remained behaviorally green. Resident memory remained seven objects, the same subject survived restart, unresolved history continued to qualify trust, cold lighthouse recall worked, the non-disclosure commitment still declined disclosure, identity rewrite still produced `protect_boundary`, and genuine repair returned relationship conflict to zero. Active state changed only +205 B between turn 250 and turn 5,000. Database growth over that interval was 7,438,336 B instead of the pre-persistence-cleanup 62,939,136 B.

The slow-belief developmental continuity gap is now closed for the demonstrated `BeliefLedger` rule contract. Pre-fix evidence showed two separately consolidated identity violations reached `trust_user=-0.4`, survived restart, but replayed from input roots alone as `0.0`; consolidating once only at replay end reached merely `-0.2`. It also showed that two one-repair threshold misses separated by consolidation stayed at `0.0`, while grouping the same two repairs before one pass reached `+0.15`. Consolidation boundaries are therefore causal even when no belief value changes.

Production now records a compact `belief_consolidation` root whenever an executed pass consumes evidence relevant to the active belief rules, including threshold misses. Empty passes with no rule-relevant evidence remain housekeeping. Replay regenerates evidence from prior roots, checks the cartridge rule digest and pre-belief digest, executes the pass at the recorded boundary, and checks changed-belief IDs plus the post-belief digest. The belief snapshot, canonical boundary, and evidence-window pruning are committed atomically. Evidence: `evidence/mvi/DEVELOPMENTAL_CONTINUITY.md` and `evidence/mvi/DEVELOPMENTAL_CONTINUITY_FIXED.md`.

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

**Next evidence target:** re-measure persistence with developmental roots active, then choose the next semantic gap from actual longitudinal failure rather than adding another subsystem speculatively. Cross-host single-writer handoff and broader authorized world/action replay remain major roadmap gaps.

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

1. Verify this documentation commit and the committed `46110470...` contextual cold-biography integration through ordinary Wayfarer CI on Python 3.11 and 3.12.
2. Do **not** turn the pressure fixture's smallest passing budget (`2`) into a production capacity constant.
3. Audit every active consumer of autobiographical memory and derive the minimum evidence each can use: ordinary turn retrieval, `HistoryDecisionEvidence`, reflection/consolidation, renderer grounding, and any other current reader.
4. Design a production hot-memory admission/eviction candidate from those consumer contracts. It should protect currently causal unresolved/evidence-bearing memories, prevent routine history from crowding them out, and rely on canonical cold biography plus grounded transient read-through for inactive history.
5. Stress that candidate with several distinct simultaneous causal roles rather than duplicate copies of one event type. Preserve repair semantics, unresolved-history conduct, explicit recall, contextual continuation, identity protection, commitments, restart, and cross-interlocutor boundaries.
6. If and only if that policy passes, integrate it and repeat the 5,000-turn plateau measurement with no experimental compaction helper. That will be the first defensible production resident-state measurement.
7. After the production measurement, translate the surviving state families into a C99-oriented compact layout and estimate the character-kernel hardware floor separately from the optional language-generation floor. Continue targeted MVI scenarios for interpretation, habits, symbols, and body only where a longitudinal behavior gives them something concrete to explain.

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

**EVIDENCE COMPLETE; production global hot-memory policy remains EXPERIMENTAL.** No universal resident-memory capacity was selected and no production retention behavior changed in this phase.

`semantic-memory-recoverability-v1` compared current production against four experimental USER_TOLD projections across six histories: unresolved conflict with unrelated distractors, unresolved conflict with lexical distractors, repaired history, reopened conflict with unrelated distractors, reopened conflict with lexical distractors, and neutral history with lexical distractors. Every variant was restarted before evaluation. The probe separately checked current conduct, old and recent contextual recall, negative-recall fail-closed behavior, commitment/identity authority, and reopened-conflict provenance.

Projection results (core passes / 6): production `0/6`; recoverable-cold-only `0/6`; active-conflict-only `0/6`; recent-context-only `0/6`; active-conflict-plus-recent `0/6`.

Production passed all scenarios: `False`. Active-conflict-only passed all scenarios: `False`. Recent-only preserved every active-conflict conduct case: `False`. Cold-only preserved every active-conflict conduct case: `False`. All projections preserved the tested recoverable-context contract: `False`.

Interpret these results by semantic role, not count. Canonical biography can reconstruct the tested old/recent USER_TOLD wording without automatically rehydrating it into resident state. The discriminating resident role in this experiment is current unresolved relationship evidence needed by conduct/reflection consumers. A passing projection is not evidence that all other memory families or future behaviors can be evicted.

Evidence: `persona_engine/evidence/mvi/SEMANTIC_MEMORY_RECOVERABILITY.md` and `semantic_memory_recoverability.json`.

**Next memory-policy target:** use the observed failure matrix, if any, to isolate the smallest missing semantic/recoverability contract. If no production failure appears, expand consumer-role coverage beyond USER_TOLD before changing retention policy. Non-USER_TOLD families remain pinned until reconstruction is demonstrated.

