# Project Wayfarer Current Status

Project Wayfarer is the active development line of `Azimn/persona_engine_PYTHONX` on the `wayfarer` branch.

The frozen pre-Wayfarer comparison point remains `main` at commit `65df9144e7f0876b6e61e28d6446c50f283f9db4`. Do not use `main` documentation as current Wayfarer status.

PythonX is the reference implementation and experimental laboratory. The long-term objective is to discover and validate the minimum semantics required to preserve one portable, believable simulated individual, then project those stabilized contracts into lower-resource runtimes including a future P99/C99-compatible implementation.

## Current production checkpoint

Current production contract: **`writer-handoff-v1` shared-store custody plus `semantic-residency-v1` memory residency.**

Current Python 3.11 verification:

```text
Targeted custody/continuity set: 32 passed
Permanent shared-store handoff probe: passed
Full deterministic suite: 340 passed, 1 skipped, 1 warning in 31.68s
```

Writer custody uses explicit host identity plus a monotonic writer generation. Mutating SQLite transactions acquire a write reservation before validating that generation, so an explicit handoff cannot race the check while avoiding the earlier per-mutation writer-row write amplification. The remaining warning is the existing Starlette/httpx TestClient deprecation, not a Wayfarer behavioral failure.

The authoritative evidence for this phase is `evidence/mvi/CROSS_HOST_WRITER_HANDOFF.md`. Exact final commit identity and cross-version CI belong in repository history/Actions rather than duplicated self-referential prose here.

## Project definition

The authoritative character is not the LLM. Authored identity plus lived continuity state constitute the individual. A language model may provide interpretation, proposals, reasoning bandwidth, or linguistic realization, but renderer replacement must not silently replace identity, biography, commitments, relationships, or developmental trajectory.

Natural language is evidence, not write authority. Objective world facts require World Authority. Character-owned commitments require an explicit semantic self-decision path. Renderer/private-cognition/UI/avatar/voice output is noncanonical.

## Implemented foundation

M0 deterministic/offline evidence and repository handoff infrastructure are established. M1 ownership/authority repair is complete. M2 has permanent entity UUID, structured self-model/ontology foundations, progressive fidelity, and lossless MatrAIx phenotype interoperability. M4 ContinuityClock and demonstrated subject-owned clock state are implemented. Explicit commitment behavior, subject-wide canonical ordering, grounded cold biography, bounded resident memory behavior, and renderer-independent semantic decision paths have been exercised through deterministic tests and longitudinal probes.

The detailed operational record remains `WAYFARER_PROGRESS.md`; the roadmap remains `WAYFARER_MASTER_PLAN.md`.

## Current M3 continuity contract

New runtime continuity is **causal-root-only**.

`canonical_continuity_root_eligible()` governs new durable writes. Current root families include user input/user statement, authoritative time advance, explicit self-adopted commitments, rule-relevant slow-belief consolidation boundaries, bounded sensor observations, authorized world facts/manual facts, and accepted world-action resolutions.

Routine `state_transition` and `sensorium` records remain rich bounded diagnostic evidence but are no longer duplicated into new permanent biography. Replay regenerates those consequences from their causal roots.

Historical v1 ledgers containing derived canonical `state_transition` and `sensorium` rows remain valid, importable, and replayable. The broader historical canonical validator therefore remains separate from the narrower new-write root policy. `CONTINUITY_SCHEMA_VERSION` remains `1.0` because this is a compatible write-policy/payload refinement rather than an incompatible interchange change.

Production input roots use payload schema `input-root-v2` and preserve the user text plus only host context actually submitted at the boundary. Derived classifier output, canonicality flags, memory-type metadata, and internally generated body/world context are not stored in the durable input root.

## Root-projection and production evidence

The controlled canonical-root projection reduced a mixed history from 21 canonical events to 9 causal roots while preserving the exact semantic replay digest, cold biography, submitted host context, commitment continuity, subject time, and bounded sensory replay.

Measured projection reduction:

- serialized event bytes: 29,685 -> 7,934, a 73.27% reduction;
- payload bytes: 18,794 -> 3,245, an 82.73% reduction.

Production 1,000-turn storage after root-only integration:

- SQLite file: `2,486,272 B`;
- canonical continuity rows: `1,004`, or `1.004` per exercised turn;
- canonical continuity physical allocation: `319,488 B`;
- canonical input payload average: `75.75 B`;
- exact canonical/diagnostic duplicated payload bytes: `0`.

The comparable database measurement immediately before root-only continuity was approximately `6.78 MB`, after diagnostic/biography separation. Before persistence cleanup began, the 1,000-turn database was approximately `13.44 MB`.

Production 5,000-turn plateau after root-only integration:

- probe passed;
- turn-5,000 database: `8,581,120 B`;
- database growth from turn 250 to 5,000: `7,438,336 B`;
- turn-5,000 active serialized state: `12,758 B`;
- active-state growth from turn 250 to 5,000: `+205 B`;
- resident memories: `7`;
- canonical input count: `5,003`.

Restart and behavioral contracts remained green: same permanent subject UUID, unresolved history still qualified trust, cold lighthouse recall remained visible, the Project Orchid non-disclosure commitment still produced `decline`, identity rewrite still produced `protect_boundary`, and genuine repair returned relationship conflict to zero without stale unresolved-tension loops.

Evidence files:

- `evidence/mvi/CANONICAL_ROOT_PROJECTION.md`
- `evidence/mvi/ROOT_ONLY_CONTINUITY_STORAGE.md`
- `evidence/mvi/ROOT_ONLY_PRODUCTION_PLATEAU.md`

## Persistence ownership after this phase

`continuity_event` owns durable causal biography.

`state` and the explicitly whitelisted `subject_state` entries are current-state snapshots/caches, not substitutes for event authority.

`event_log` is bounded recent operational telemetry. It is intentionally not part of the minimum permanent person.

`consolidation_evidence` is the compact semantic evidence stream currently used by slow belief consolidation. Consumed evidence can be pruned after its consolidation watermark is persisted.

The current 1,000-turn storage profile shows that canonical continuity is no longer the dominant persistent object. Consolidation evidence plus its index and the bounded diagnostic window are now larger than the durable continuity table.

## Developmental continuity contract

The pre-fix developmental probe forced a real slow `BeliefLedger` trajectory. Two identity violations consolidated separately moved `trust_user` from `0.0` to `-0.2` to `-0.4`, and ordinary restart preserved `-0.4`. The root-only canonical export contained only the two input events, so current replay reconstructed `0.0`. Replaying both inputs and consolidating only once at the end reconstructed only `-0.2`.

The threshold control was more decisive: one repair followed by a consolidation pass, repeated twice, stayed at `0.0` because each pass consumed a sub-threshold evidence window. The same two repairs grouped before one consolidation reached `+0.15`. A no-change consolidation boundary can therefore alter later development and is genuine causal history.

Production commit `268739c` adds the minimum mechanism supported by that result. An executed pass becomes a compact `belief_consolidation` root only when it consumed evidence relevant to the active belief rules. Threshold misses are recorded; empty irrelevant passes are not. The payload records a rule digest, before/after belief digests, relevant evidence counts, changed IDs, and before/after values for changed beliefs. It is verification/causal metadata, not a full state dump.

Replay regenerates the preceding evidence, verifies the active rule digest and pre-belief digest, executes consolidation at the recorded boundary without writing a duplicate root, then verifies changed IDs and the post-belief digest. Rule mismatch requires explicit migration rather than silently replaying development under different rules. Persistence atomically commits the belief snapshot, canonical consolidation root, and pruning of the consumed evidence window.

Post-fix evidence reproduces `trust_user=-0.4` across live state, restart, and canonical replay. Two separate no-change repair boundaries also reproduce `0.0` in canonical replay. Legacy `dream_consolidation` remains a derived compatibility family.

Evidence:

- `evidence/mvi/DEVELOPMENTAL_CONTINUITY.md`
- `evidence/mvi/developmental_continuity.json`
- `evidence/mvi/DEVELOPMENTAL_CONTINUITY_FIXED.md`
- `evidence/mvi/developmental_continuity_fixed.json`

## Hot-memory policy status

The global hot-memory admission/eviction policy remains **EXPERIMENTAL**. No total resident-memory capacity was promoted by this pass.

The older `hot-memory-causal-pressure-v2` evidence was rerun against the current production engine because the meaning of its `full` control had changed over time. `InteriorEngine._persist()` now applies the narrow production `USER_TOLD` recoverability compactor even when the probe adds no experimental projection. The control is therefore current production resident state, not the historical unconstrained 24-item store.

Current rerun: experimental smallest finite budget preserving the probe's demonstrated causal roles = `2`; current no-extra-projection resident count before reflection = `7`; current no-extra-projection core pass = `True`; old-style full-resident interference still demonstrated = `False`; ordinary contextual gap across all variants = `False`. These are experiment results, not a production capacity recommendation.

The consumer-role probe still points to **role protection rather than raw capacity**. Its smallest tested role projection preserving current causal plus retrieval-trace continuity is `causal2_only`. Continuous-budget experiments report a smallest passing tested budget of `1`, but that number remains explicitly non-normative.

Production remains narrower: only canonically recoverable `USER_TOLD` autobiography is compacted, using the widths required by current consumers, while non-`USER_TOLD` families stay pinned until their reconstruction contracts are demonstrated. Contextual cold-biography candidates are transient retrieval evidence and are not automatically promoted back into hot state.

Developmental persistence was also re-measured with the new consolidation contract exercised every `50` turns across the same 1,000-input history used by its control. It committed `20` `belief_consolidation` roots at an average payload of `462.7` B. SQLite delta versus the same inputs without executed consolidation was `-761,856` B; consolidation-evidence row delta was `-7,508` because committed boundaries consume/prune their evidence windows. This is an engineering storage measurement, not validation of the psychological threshold/delta values.

**Current memory-policy result:** that consumer-role/recoverability pass is complete as `semantic-residency-v1`. No universal `N` was selected. `OBSERVED` and `REFLECTION` remain resident until a future typed reconstruction path earns their eviction; see the later Semantic residency policy section and its evidence.

## Other known limitations

Replay does not yet cover every future authoritative host/world/action family. Shared-store cross-host single-writer custody and explicit handoff are now implemented as `writer-handoff-v1`; disconnected-store transfer/branch reconciliation remains future work. Social influence/collaboration authority is not yet fully typed. The default zero-model renderer remains linguistically limited. There is no production microphone, camera, TTS, avatar engine, or mobile-native host. Offscreen life remains limited compared with the planned event-based autonomy layer. The minimum viable individual has not yet been established through the complete ablation program.

## Standing design decisions

The local single-owner default does not require a per-event cryptographic previous-hash chain. Add adversarial tamper evidence only if the threat model expands to hostile hosts, untrusted synchronization, remote custody, or multi-party administrative control.

Developmental/plasticity parameters must earn their existence through observable behavioral effects, sensitivity analysis, identifiability checks, held-out scenarios, simpler baselines, and versioned experiment provenance. Numerical precision is not evidence of psychological validity.

## Immediate next work

1. Preserve the shared-store `writer-handoff-v1` fence. Any next cross-host phase must falsify disconnected-store transfer/branch behavior rather than weaken the working shared-store contract.
2. Do not resume memory-count optimization without a new demonstrated failure. `semantic-residency-v1` and the 5,000-turn active-state plateau are the current memory result.
3. Full typed social-influence authority and richer offscreen autonomy remain unresolved longitudinal candidates; choose the next one by writing its falsification criterion first.
4. Treat duplicated current-status prose as a repository-governance risk. The current manual synchronization process has produced stale contradictory checkpoints and should be replaced by a machine-verifiable status source plus CI consistency checks in a separate governance phase.
5. Add an independently designed adversarial continuity evaluation before making strong robustness claims about the same-individual contract or freezing cross-language conformance vectors.

## Required reading

Before modifying Wayfarer behavior, read in this order:

1. `WAYFARER_MASTER_PLAN.md`
2. `WAYFARER_PROGRESS.md`
3. `WAYFARER_CHARTER.md`
4. `AI_DEVELOPER_HANDOFF.md`
5. `AUTHORITY_MATRIX.md`
6. `ARCHITECTURE_LOCK.md`
7. `WAYFARER_BASELINE.md`
8. this file
9. relevant tests and evidence

Repository documentation is part of the implementation contract. If documentation and code disagree, establish live behavior through code, history, tests, and evidence, then update documentation in the same work pass.

## Semantic memory recoverability status

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

**Historical checkpoint note:** this was the next target at the end of semantic-memory-recoverability-v2. It was subsequently completed by `semantic-residency-v1`; current policy is described below.



## Runtime transaction and streaming integrity

The local runtime enforces a reentrant process-local serialization boundary around public access paths that can mutate or expose the continuing subject during a turn. This closes the race between `receive_input()` and background/explicit `advance_time()`. Shared-store cross-host custody is now a separate `writer-handoff-v1` host + generation fence; disconnected authority-store copies and branch reconciliation remain deferred. Compound legacy pressure/symbol helpers participate in the local boundary.

The public streaming convenience path is also causal: `stream_last_response()` executes one turn and emits chunks from that turn's already validated final response. It does not ask the renderer for a second, potentially divergent utterance after canonical writeback. The FastAPI SSE path already streamed the committed result and remains unchanged.

Two deterministic regressions cover exact streamed-response identity and blocking of concurrent turn/time mutations. At that historical local-serialization checkpoint the Python 3.11 deterministic inventory was `333 passed, 1 skipped, 1 warning`. One-shot run `33347858914` passed the targeted regressions and full Python 3.11 suite; normal Wayfarer CI run `33347953873` passed both Python 3.11 and Python 3.12 on hardened code head `8ae965baddaacfefa55112b5ee81778b1db962ad`. The current inventory is recorded at the top of this file.

## Semantic residency policy

Wayfarer production now names its resident-memory contract `semantic-residency-v1`. Inactive `USER_TOLD` autobiography may be reconstructed from canonical cold biography, while current unresolved relationship evidence remains resident for demonstrated conduct/reflection consumers. `OBSERVED` and `REFLECTION` remain resident because controlled ablations lose retrievable first-person experience and no equivalent cold reconstruction path exists. No universal resident-memory count is approved.

A combined adversarial fixture and a fresh 5,000-turn production-only plateau are green. At turn 5,000 the exercised fixture used `12,707 B` of serialized active state and `7` resident memories, with only `134 B` active-state growth since turn 250. These are measured outcomes, not fixed budgets.



## Shared-store cross-host writer custody

`writer-handoff-v1` is the first M5 custody contract. Each permanent subject has one active `host_id` plus a monotonic writer generation in the shared authority store. Subject-affecting persistence writes fence against both values inside the same SQLite transaction as the mutation. A host with a stale generation or a different active host fails closed with `WriterLeaseError`.

An explicit handoff persists a clean source boundary, records its state digest and subject-sequence anchor as administrative continuity metadata, advances the writer generation, and names the target host. The handoff itself is not inserted into `continuity_event`; changing custodial machinery is not automatically a lived experience. The target validates the durable receipt and loaded-state digest before accepting custody.

The combined probe preserves permanent subject UUID, subject-wide canonical ordering, continuity clock, subject-owned earned traits, self-owned commitment behavior, and interlocutor-specific relationship scope. It also proves generation fencing when a host ID later returns: an older process with that same host ID remains stale until it receives the new generation explicitly.

Scope is deliberately narrow: one shared canonical SQLite authority store, cooperative hosts, no expiry/automatic stealing. Disconnected copies, remote consensus, hostile direct database access, and branch reconciliation are not claimed solved. See `evidence/mvi/CROSS_HOST_WRITER_HANDOFF.md`.
